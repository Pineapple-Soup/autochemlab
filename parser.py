import os
import re
import sys
import chemicals.identifiers as CI # type: ignore
from pypdf import PdfReader # type: ignore

def get_input():
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} filename")
        exit(1)
    
    file = sys.argv[1]
    if not os.path.isfile(file):
        print(f"{file} is not a valid file")
        exit(1)
    
    file_name, file_ext = os.path.splitext(file)
    if file_ext.lower() != '.pdf':
        print(f"{file} must be a PDF file!")
        exit(1)
    
    return file
    
def extract_chemical_names(fields : dict):
    chemicals = []
    for field in fields:
        if field.startswith("Hazards"):
            field = field.replace("Hazards", "")
            chemicals.append(field)
    return chemicals

def parse_locants(c : str):
    c = re.sub(r'(\d)(\d)', r'\1,\2', c)
    c = re.sub(r'(\d)([a-zA-Z])', r'\1-\2', c)
    return c

file = get_input()
reader = PdfReader(file)
fields = reader.get_form_text_fields()
chemicals = extract_chemical_names(fields)
chemicals_parsed = [parse_locants(c) for c in chemicals]