import http.server
import socketserver
import json
import urllib.parse
import os
import time
import sys

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(DIRECTORY, "static")
CANDIDATES_FILE = os.path.join(DIRECTORY, "Hackathon-Details", "candidates.jsonl")

# Candidate offset index and metadata cache
# candidate_id -> (offset, line_length)
candidate_index = {}
# List of dicts for fast search filtering
candidate_metadata = []

def index_candidates():
    global candidate_index, candidate_metadata
    print(f"[*] Starting indexing of candidate dataset: {CANDIDATES_FILE}")
    start_time = time.time()
    
    if not os.path.exists(CANDIDATES_FILE):
        print(f"[!] Error: {CANDIDATES_FILE} not found!")
        print("[!] Please run the project extraction step first or verify the file location.")
        sys.exit(1)
        
    count = 0
    candidate_index.clear()
    candidate_metadata.clear()
    
    with open(CANDIDATES_FILE, "rb") as f:
        offset = 0
        for line in f:
            line_len = len(line)
            if not line.strip():
                offset += line_len
                continue
                
            try:
                # Decode line as UTF-8
                line_str = line.decode("utf-8")
                data = json.loads(line_str)
                cid = data.get("candidate_id")
                if cid:
                    candidate_index[cid] = (offset, line_len)
                    
                    profile = data.get("profile") or {}
                    signals = data.get("redrob_signals") or {}
                    
                    # Safe skills parsing
                    skills_raw = data.get("skills") or []
                    skills = []
                    if isinstance(skills_raw, list):
                        for s in skills_raw:
                            if isinstance(s, dict) and s.get("name"):
                                skills.append(str(s["name"]).lower())
                    
                    # Safe YoE parsing
                    yoe_val = profile.get("years_of_experience")
                    try:
                        yoe = float(yoe_val) if yoe_val is not None else 0.0
                    except (ValueError, TypeError):
                        yoe = 0.0
                    
                    candidate_metadata.append({
                        "id": str(cid),
                        "name": str(profile.get("anonymized_name") or "Anonymized Candidate"),
                        "title": str(profile.get("current_title") or "Unknown Title"),
                        "company": str(profile.get("current_company") or "Unknown Company"),
                        "location": str(profile.get("location") or "Unknown Location"),
                        "yoe": yoe,
                        "skills": skills,
                        "preferred_work_mode": str(signals.get("preferred_work_mode") or "Unknown"),
                        "willing_to_relocate": bool(signals.get("willing_to_relocate") or False)
                    })
            except Exception as e:
                # Log first few errors for visibility
                if count < 10:
                    print(f"[!] Error parsing record at offset {offset}: {e}")
            
            offset += line_len
            count += 1
            if count % 20000 == 0:
                print(f"[*] Indexed {count} records...")
                
    elapsed = time.time() - start_time
    print(f"[+] Indexing completed in {elapsed:.2f} seconds.")
    print(f"[+] Indexed {len(candidate_index)} candidates successfully.")
    print(f"[+] Metadata cache populated with {len(candidate_metadata)} records.")

def get_candidate_data(candidate_id):
    if candidate_id not in candidate_index:
        return None
    offset, length = candidate_index[candidate_id]
    with open(CANDIDATES_FILE, "rb") as f:
        f.seek(offset)
        line_bytes = f.readline()
        return json.loads(line_bytes.decode("utf-8"))

class CandidateHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Serve from static directory
        parsed_url = urllib.parse.urlparse(path)
        clean_path = parsed_url.path
        
        # Default route
        if clean_path == "/" or clean_path == "":
            clean_path = "/index.html"
            
        file_path = os.path.join(STATIC_DIR, clean_path.lstrip("/"))
        return file_path

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)
        
        # API endpoints
        if path.startswith("/api/"):
            self.handle_api(path, query)
        else:
            # Fallback to serving static files
            super().do_GET()

    def handle_api(self, path, query):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        response_data = {}
        
        if path == "/api/stats":
            file_size_mb = os.path.getsize(CANDIDATES_FILE) / (1024 * 1024)
            response_data = {
                "success": True,
                "total_candidates": len(candidate_index),
                "file_size_mb": round(file_size_mb, 2),
                "status": "ready"
            }
            
        elif path == "/api/candidate":
            cid = query.get("id", [None])[0]
            if not cid:
                response_data = {"success": False, "error": "Missing candidate ID parameter 'id'"}
            else:
                data = get_candidate_data(cid)
                if data:
                    response_data = {"success": True, "data": data}
                else:
                    response_data = {"success": False, "error": f"Candidate ID '{cid}' not found"}
                    
        elif path == "/api/search":
            q = query.get("q", [""])[0].strip().lower()
            title = query.get("title", [""])[0].strip().lower()
            loc = query.get("location", [""])[0].strip().lower()
            
            yoe_min_str = query.get("yoe_min", ["0"])[0]
            yoe_max_str = query.get("yoe_max", ["20"])[0]
            
            try:
                yoe_min = float(yoe_min_str) if yoe_min_str else 0.0
            except ValueError:
                yoe_min = 0.0
                
            try:
                yoe_max = float(yoe_max_str) if yoe_max_str else 20.0
            except ValueError:
                yoe_max = 20.0
            
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            
            # Simple keyword search parsing
            search_tokens = [tok for tok in q.split() if tok]
            
            filtered = []
            for item in candidate_metadata:
                # Filter by title
                if title and title not in item["title"].lower():
                    continue
                # Filter by location
                if loc and loc not in item["location"].lower():
                    continue
                # Filter by YoE (we expand to a very large number if max is 20 to include outliers)
                max_threshold = 100.0 if yoe_max >= 20.0 else yoe_max
                if item["yoe"] < yoe_min or item["yoe"] > max_threshold:
                    continue
                    
                # Keyword search matching name, title, company, location, or skills
                if search_tokens:
                    text_blob = f"{item['name']} {item['title']} {item['company']} {item['location']} {' '.join(item['skills'])}".lower()
                    if not all(tok in text_blob for tok in search_tokens):
                        continue
                        
                filtered.append({
                    "id": item["id"],
                    "name": item["name"],
                    "title": item["title"],
                    "company": item["company"],
                    "location": item["location"],
                    "yoe": item["yoe"]
                })
                
            # Paginate
            total_results = len(filtered)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            
            paginated_results = filtered[start_idx:end_idx]
            
            response_data = {
                "success": True,
                "total": total_results,
                "page": page,
                "limit": limit,
                "pages": (total_results + limit - 1) // limit,
                "results": paginated_results
            }
            
            print(f"[API] Search query='{q}' title='{title}' loc='{loc}' yoe=[{yoe_min}, {yoe_max}] page={page} -> Matched {total_results} candidates")
            
        else:
            response_data = {"success": False, "error": f"Endpoint '{path}' not supported"}
            
        self.wfile.write(json.dumps(response_data).encode("utf-8"))

def main():
    # Make sure static directory exists
    os.makedirs(STATIC_DIR, exist_ok=True)
    
    # Index the file
    index_candidates()
    
    # Start web server
    handler = CandidateHTTPHandler
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"\n[+] Candidate Visualizer local server running at:")
        print(f"    --> http://localhost:{PORT}/")
        print(f"[*] Press Ctrl+C to terminate the server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Server stopped.")

if __name__ == "__main__":
    main()
