import pandas as pd
from enum import Enum
import os
from pathlib import Path
from typing import List


master_errors = pd.DataFrame(columns=["file_path", "error", "value"])
procedure_errors = pd.DataFrame(columns=["file_path", "error", "value"])
report_errors = pd.DataFrame(columns=["file_path", "error", "value"])

class ErrorCode(Enum):
    FILE_NOT_FOUND = "File not found"
    DEPENDENCY_NOT_IN_DICT = "Dependency not in dict"
    SCAN_DIR_NOT_IN_PATH = "scan_dir is not in path"
    HOLD_NAME_NOT_FOUND = "Hold name not found"
    HOLD_NAME_PARAMETERIZED = "Hold name is parameterized"
    INCLUDE_NOT_FOUND = "Procedure include not found in procedure dict"

def log_master_error(file_path, error, value):
    global master_errors
    error_data = pd.DataFrame([{
        "file_path": file_path,
        "error": error.name,
        "message": error.value,
        "value": value
    }])
    master_errors = pd.concat([master_errors, error_data], ignore_index=True)


def log_procedure_error(file_path, error, value):
    global procedure_errors
    error_data = pd.DataFrame([{
        "file_path": file_path,
        "error": error.name,
        "message": error.value,
        "value": value
    }])
    procedure_errors = pd.concat([procedure_errors, error_data], ignore_index=True)


def log_report_error(file_path, error, value):
    global report_errors
    error_data = pd.DataFrame([{
        "file_path": file_path,
        "error": error.name,
        "message": error.value,
        "value": value
    }])
    report_errors = pd.concat([report_errors, error_data], ignore_index=True)


def save_errors_to_csv(master_file="master_errors.csv", procedure_file="procedure_errors.csv", report_file="report_errors.csv"):
    if not master_errors.empty:
        print("Master errors")
        master_errors.to_csv(master_file, index=False)
    
    if not procedure_errors.empty:
        print("Procedure errors")
        procedure_errors.to_csv(procedure_file, index=False)
    
    if not report_errors.empty:
        print("Report errors")
        report_errors.to_csv(report_file, index=False)


def read_file_lines(file_path):
    try:
        with open(file_path, 'r', encoding='utf8') as f:
            return [line.strip() for line in f]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return [] 

def is_absolute_and_valid_path(path_str: str) -> bool:
    try:
        path = Path(path_str)
        
        if not path.is_absolute():
            print('Path is ABS')
            return False
        
        if not path.exists():
            print('Path does not exist')
            return False
                        
        return True
    except Exception as e:
        print(f"Error checking path: {e}")
        return False
    
def walk_directory(directory: str, file_extension: str) -> List[str]:
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(file_extension):
                file_path = Path(root) / file
                abs_file_path = file_path.resolve()
                file_paths.append(str(abs_file_path))
    return file_paths

def convert_to_relative_path(abs_path, scan_directory, output_directory):
    scan_directory = os.path.abspath(scan_directory)
    # output_directory = os.path.abspath(output_directory)

    abs_path = os.path.abspath(abs_path)

    if abs_path.startswith(scan_directory):
        print(f'Path: {abs_path}')
        print(f'\tStarts with scan')
        
        # Get the relative path from scan_directory
        relative_path = os.path.relpath(abs_path, scan_directory)
        print(f'\t{relative_path}')
        
        # Prepend output_directory to the relative path
        final_path = os.path.join(output_directory, relative_path)
        print(f'\t{final_path}')

        cleaned_final_path = final_path.lstrip('./\\')
        print(f'\t{cleaned_final_path}')
        
        # Return the final path
        return cleaned_final_path
    else:
        print(f'Path: {abs_path}')
        print(f'\tSomethings wrong')
        
    return abs_path