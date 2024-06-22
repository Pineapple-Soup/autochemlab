import os
import re
import requests # type: ignore
import sys
from chemicals import IDs_to_CASs  # type: ignore
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

def retrieve_properties(casrn : str):
    compound_data = {}
    url = f"https://commonchemistry.cas.org/api/detail?cas_rn={casrn}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        compound_data["Molecular Weight"] = response.json()["molecularMass"]
        experimental_properties = response.json()["experimentalProperties"]
        for property in experimental_properties:
            compound_data[property["name"]] = property["property"]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return None
    except KeyError as e:
        print(f"KeyError: {e} - Missing expected data in API response.")
        return None
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return None
    return compound_data

if __name__ == "__main__":
    file = get_input()
    reader = PdfReader(file)
    fields = reader.get_form_text_fields()
    chemical_names = [parse_locants(c) for c in extract_chemical_names(fields)]
    # TODO: Exception Handling
    chemical_CASRNs = IDs_to_CASs(chemical_names)
    print(chemical_names)
    print(chemical_CASRNs)
    chemical_data = []
    for name, casrn in zip(chemical_names, chemical_CASRNs):
        properties = retrieve_properties(casrn)
        if properties is not None:
            chemical_data.append({"name" : name , "info" : properties})
    for chemical in chemical_data:
        print(f"====={chemical["name"]}=====")
        for property, value in chemical["info"].items():
            print(f"{property}: {value}")