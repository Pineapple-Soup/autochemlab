import os
import re
import sys
from chemicals import CAS_from_any, MW, Tb, Tm, iapws95_rhol_sat  # type: ignore
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
    return [field.replace("Hazards", "") for field in fields if field.startswith("Hazards")]

def parse_locants(c : str):
    c = re.sub(r'(\d)(\d)', r'\1,\2', c)
    c = re.sub(r'(\d)([a-zA-Z])', r'\1-\2', c)
    return c

file = get_input()
reader = PdfReader(file)
fields = reader.get_form_text_fields()
chemical_names = extract_chemical_names(fields)
chemical_names = [parse_locants(c) for c in chemical_names]
# TODO: Exception Handling
chemicals = [CAS_from_any(chemical) for chemical in chemical_names]
chemical_properties = [[MW(CAS), Tb(CAS), Tm(CAS)] for CAS in chemicals]
[print(name, CAS, props) for name, CAS, props in zip(chemical_names, chemicals, chemical_properties)]