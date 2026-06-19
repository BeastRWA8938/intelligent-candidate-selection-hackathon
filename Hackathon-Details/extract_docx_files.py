import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def get_docx_text(path):
    try:
        doc = zipfile.ZipFile(path)
        xml_content = doc.read('word/document.xml')
        root = ET.fromstring(xml_content)
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paragraphs = []
        for para in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            texts = [node.text for node in para.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
            if texts:
                paragraphs.append(''.join(texts))
            else:
                # Add empty line for spacing if there's an empty paragraph
                paragraphs.append('')
        return '\n'.join(paragraphs)
    except Exception as e:
        return f"Error extracting {path}: {e}"

def main():
    details_dir = Path("C:/Users/Rushikesh/Desktop/Data/Hackathon/Hack2Skill-RedRob/Hackathon-Details")
    for docx_path in details_dir.glob("*.docx"):
        txt_path = docx_path.with_suffix(".txt")
        print(f"Extracting {docx_path.name} to {txt_path.name}...")
        text = get_docx_text(docx_path)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
    print("Done!")

if __name__ == "__main__":
    main()
