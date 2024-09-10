from pathlib import Path
import os
from typing import List

def read_file_lines(file_path):
    try:
        with open(file_path, 'r', encoding='utf8') as f:
            return [line.strip() for line in f]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return [] 

def is_valid_path(path_str: str) -> bool:
    try:
        path = Path(path_str)
        
        if not path.exists():
            print('Path does not exist')
            return False
                        
        return True
    except Exception as e:
        print(f"Error checking path: {e}")
        return False
    
def walk_directory(directory: str, file_extension: str) -> List[str]:
    file_paths = []
    base_directory = Path(directory).resolve()  

    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(file_extension):
                relative_file_path = Path(root).relative_to(base_directory) / file  
                full_path = str(base_directory / relative_file_path)  
                file_paths.append(full_path)  

    return file_paths
