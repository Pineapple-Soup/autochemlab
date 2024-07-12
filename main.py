import os
import re
import requests
import sys
from chemicals import MW, Tm, Tb
from pypdf import PdfReader, PdfWriter

def get_input_file() -> str | None:
    if len(sys.argv) > 2:
        print(f"Usage: python3 {sys.argv[0]} | python3 {sys.argv[0]} filename")
        exit(1)

    if len(sys.argv) < 2:
        return None
    
    file = sys.argv[1]
    if not os.path.isfile(file):
        print(f"{file} is not a valid file")
        exit(1)
    
    file_name, file_ext = os.path.splitext(file)
    if file_ext.lower() != '.pdf':
        print(f"{file} must be a PDF file!")
        exit(1)
    
    return file

def get_names_from_fields(fields: list[str]) -> list[str]:
    return [parse_locants(c) for c in extract_chemical_names(fields)]

def get_names_from_user() -> list[str]:
    names = input("Enter the names of the chemicals [omitting commas and dashes], each separated by a semicolon: ")
    names = names.split(';')
    return [parse_locants(name.strip()) for name in names]

def extract_chemical_names(fields: list[str]) -> list[str]:
    return [field.replace("Hazards", "") for field in fields if field.startswith("Hazards")]

def parse_locants(compound: str) -> str:
    compound = re.sub(r'(\d)(\d)', r'\1,\2', compound)
    compound = re.sub(r'(\d)([a-zA-Z])|([a-zA-Z])(\d)', r'\1\3-\2\4', compound)
    compound = re.sub(r'(\d) ([a-zA-Z])', r'\1-\2', compound)
    # Handle edge cases
    compound = re.sub(r'([a-zA-Z]) (hex+)', r'\1\2', compound)
    compound = re.sub("hexanes", "hexane", compound)
    return compound

def retrieve_CASRN(chemical: str) -> str | None:
    try:
        url = f"https://commonchemistry.cas.org/api/search?q={chemical}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data['count'] > 0:
            return data['results'][0]['rn']
        else:
            raise ValueError
    except ValueError as e:
        print(f"Could not find CASRN for {chemical} with exception: {e}")

def retrieve_all_CASRNs(chemicals: list[str]) -> list[str]:
    casrns = []
    for idx, chemical in enumerate(chemicals):
        retry = 1
        while retry >= 0:
            casrn = retrieve_CASRN(chemical)
            if casrn is not None:
                casrns.append(casrn)
                break
            elif retry > 0:
                # Option 1: Strip numbers and try again
                chemical = re.sub(r"^[\d,]+-", "", chemical)
                chemicals[idx] = chemical
                retry -= 1
            else:
                # Option 2: Prompt user for correct chemical name
                print(f"Failed at {chemical}")
                retry -= 1
                # raise ValueError
    return casrns

def retrieve_properties(casrn: str) -> dict[str, str]:
    compound_data = {}
    url = f"https://commonchemistry.cas.org/api/detail?cas_rn={casrn}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        molecular_weight = response.json()["molecularMass"]
        if molecular_weight:
            compound_data["Molecular Weight"] = molecular_weight
        else:
            compound_data["Molecular Weight"] = str(round(MW(casrn), 2))
        experimental_properties = response.json()["experimentalProperties"]
        for property in experimental_properties:
            property_value = re.search(r'[-]?\d*\.?\d+', property["property"]).group() # type: ignore
            compound_data[property["name"]] = str(round(float(property_value), 3))
        if "Boiling Point" not in compound_data:
            try:
                compound_data["Boiling Point"] = str(round(Tb(casrn)-273.15, 3)) # type: ignore
            except TypeError as e:
                compound_data["Boiling Point"] = None
        if "Melting Point" not in compound_data:
            try:
                compound_data["Melting Point"] = str(round(Tm(casrn)-273.15, 3)) # type: ignore
            except TypeError as e:
                compound_data["Melting Point"] = None
        if "Density" not in compound_data:
            compound_data["Density"] = None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
    except KeyError as e:
        print(f"KeyError: {e} - Missing expected data in API response.")
    except Exception as e:
        print(f"Unexpected Error: {e}")
    return compound_data

def retrieve_all_data(chemical_names: list[str], chemical_casrns: list[str]) -> list[dict]:
    chemical_data = []
    for name, casrn in zip(chemical_names, chemical_casrns):
        properties = retrieve_properties(casrn)
        if properties is not None:
            chemical_data.append({"name" : name , "data" : properties})
    return chemical_data

def get_mp_and_bp_designation() -> set[str]:
    print("Boiling Point Chemicals")
    bp_chemicals = get_names_from_user()
    ret = set()
    for boiling_point in bp_chemicals:
        ret.add(boiling_point)
    return ret

def generate_fields_from_properties(fields_list: list[list], chemical_properties: list[dict], chemical_designation: set[str]) -> dict[str, str]:
    fields = {}
    for key, data in zip(fields_list, chemical_properties):
        if "Molecular Weight" in key[0]:
            fields[key[0]] = data["data"]["Molecular Weight"]
        if "fill_" in key[1]:
            melting_point = data["data"]["Melting Point"]
            boiling_point = data["data"]["Boiling Point"]
            fields[key[1]] = boiling_point if data["name"] in chemical_designation else melting_point
        if "Density" in key[2]:
            fields[key[2]] = data["data"]["Density"]
    return fields

if __name__ == "__main__":
    file = get_input_file()
    if file:
        reader = PdfReader(file)
        fields = list(reader.get_form_text_fields())
        chemical_names = get_names_from_fields(fields)
        chemical_CASRNs = retrieve_all_CASRNs(chemical_names)
        # print(chemical_names)
        # print(chemical_CASRNs)
        chemical_data = retrieve_all_data(chemical_names, chemical_CASRNs)
        chemical_designation = get_mp_and_bp_designation()
        fields_list = [field for field in fields if "Molecular Weight" in field or "fill_" in field or "Density" in field]
        fields_list = [fields_list[i:i+3] for i in range(0, len(fields_list), 3)]
        new_fields = generate_fields_from_properties(fields_list, chemical_data, chemical_designation)
        # print(new_fields)

        writer = PdfWriter()
        writer.append(reader)
        writer.update_page_form_field_values(writer.pages[0], new_fields, auto_regenerate=False)

        outfile = file.split('/')[-1]
        with open(f"output/{outfile}", "wb") as output_stream:
            writer.write(output_stream)

    else:
        chemical_names = get_names_from_user()
        chemical_CASRNs = retrieve_all_CASRNs(chemical_names)
        chemical_data = retrieve_all_data(chemical_names, chemical_CASRNs)
        for chemical in chemical_data:
            print(f"\n===== {chemical["name"]} =====")
            for property, value in chemical["data"].items():
                    print(f"{property}: {value}")
