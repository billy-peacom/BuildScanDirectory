import os
import pandas as pd
import shutil
import re
from utils import log_report_error, ErrorCode

class Report:
    def __init__(self, report_name):
        self.procedures = []
        self.name = report_name

    @staticmethod
    def get_reports(inventory_file, source_directory, target_directory):
        inventory_df = Report._load_reports(inventory_file)

        os.makedirs(target_directory, exist_ok=True)
        artifact_dict = {} 

        for _, row in inventory_df.iterrows():
            artifact_name = row['name']
            artifact_data = row['procedures']

            
            if pd.notna(artifact_data) and isinstance(artifact_data, str):
                artifact_files = Report.process_artifacts(artifact_data)
            else:
                artifact_files = []

            artifact_dict[artifact_name] = artifact_files

            if pd.isna(artifact_name):
                continue
            

            for file in artifact_files:
                source_file_path = os.path.normpath(os.path.join(source_directory, file.lstrip("/")))

                relative_path = file.lstrip("/") 
                target_file_path = os.path.normpath(os.path.join(target_directory, relative_path))

                target_file_dir = os.path.dirname(target_file_path)
                os.makedirs(target_file_dir, exist_ok=True)


                if os.path.exists(source_file_path) == False:
                    log_report_error(source_file_path, ErrorCode.FILE_NOT_FOUND, file)
                else:
                    shutil.copy(source_file_path, target_file_path)

        return artifact_dict

    @staticmethod
    def _load_reports(inventory_file):
        inventory_df = pd.read_csv(inventory_file, header=0, skiprows=[1])
                
        return inventory_df

    @staticmethod
    def process_artifacts(artifact_data):
        current_files = []

        for line in artifact_data.split("\n"):
            line = line.strip()

            cleaned_file_path = re.sub(r"^\d+\)\s*", "", line).strip()

            cleaned_file_path = re.sub(r"^[^:]*:", "", cleaned_file_path).strip()

            if cleaned_file_path:
                current_files.append(cleaned_file_path)

        return current_files