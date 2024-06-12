import os
import sys
from pypdf import PdfReader # type: ignore

def get_input():
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} filename")
        return 1
    
    file = sys.argv[2]
    if not os.path.isfile(file):
        print(f"{file} is not a valid file")
        return 1
    
    file_name, file_ext = os.path.splitext(file)
    if file_ext.lower != '.pdf':
        print(f"{file} must be a PDF file!")
        return 1
    
    return file
    


file = get_input()