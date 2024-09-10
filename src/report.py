import os
import pandas as pd
import shutil
import re

debug = False

class Report:
    def __init__(self, file_path):
        self.file_path = os.path.normpath(file_path)
        self.filename = os.path.basename(file_path)
        self.procedures = []

    @staticmethod
    def copy_reports(inventory_file, source_directory, target_directory):
        inventory_df = Report._load_reports(inventory_file)

        os.makedirs(target_directory, exist_ok=True)
        artifact_dict = {} 

        for _, row in inventory_df.iterrows():
            artifact_name = row['Artifact name']
            artifact_data = row['PRIMARY FEX(ES)']

            if debug:
                print()
                print(f"Processing files for artifact: {artifact_name}")
            
            if pd.notna(artifact_data) and isinstance(artifact_data, str):
                artifact_files = process_artifacts(artifact_data)
            else:
                artifact_files = []

            if debug:
                print(f"Artifact files: {artifact_files}")
                print(f"Source directory: {source_directory}")
                print(f"Target directory: {target_directory}")

            artifact_dict[artifact_name] = artifact_files

            if pd.isna(artifact_name):
                continue
            

            for file in artifact_files:
                source_file_path = os.path.normpath(os.path.join(source_directory, file.lstrip("/")))

                relative_path = file.lstrip("/") 
                target_file_path = os.path.normpath(os.path.join(target_directory, relative_path))

                target_file_dir = os.path.dirname(target_file_path)
                os.makedirs(target_file_dir, exist_ok=True)

                if debug:
                    print(f"Copying from: {source_file_path}")
                    print(f"Copy to: {target_file_path}")

                if os.path.exists(source_file_path):
                    shutil.copy(source_file_path, target_file_path)

                    if debug:
                        print(f"Copied {source_file_path} to {target_file_path}")
                else:
                    print(f"File not found or invalid: {source_file_path}")

        return artifact_dict

    @staticmethod
    def _load_reports(inventory_file):
        inventory_df = pd.read_excel(inventory_file, header=0, skiprows=[1])
        
        inventory_df = inventory_df[inventory_df['Priority'] != '4. Not Required']
        
        return inventory_df


def process_artifacts(artifact_data):
    current_files = []

    for line in artifact_data.split("\n"):
        line = line.strip()

        cleaned_file_path = re.sub(r"^\d+\)\s*", "", line).strip()
        if debug:
            print(f"Clean 1: {cleaned_file_path}")
        cleaned_file_path = re.sub(r"^[^:]*:", "", cleaned_file_path).strip()
        if debug:
            print(f"Clean 2: {cleaned_file_path}")

        if cleaned_file_path and not cleaned_file_path.startswith("missing") and not cleaned_file_path.startswith("invalid"):
            current_files.append(cleaned_file_path)

    return current_files