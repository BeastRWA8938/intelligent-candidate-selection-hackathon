import os

def search():
    terms = ['modular', 'different jd', 'other jd', 'another jd', 'later jd', 'different job', 'multiple jd', 'multiple jobs']
    found_any = False
    for root, dirs, files in os.walk('.'):
        for f in files:
            if f.endswith(('.txt', '.md', '.docx', '.yaml')):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as file_obj:
                        content = file_obj.read().lower()
                        for term in terms:
                            if term in content:
                                print(f'Found term "{term}" in: {path}')
                                found_any = True
                except Exception as e:
                    pass
    if not found_any:
        print("No modularity or multi-JD terms found in the documents.")

if __name__ == "__main__":
    search()
