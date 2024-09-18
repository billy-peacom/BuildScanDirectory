import os
import pandas as pd
import shutil
import re

debug = True

class Report:
    def __init__(self, report_name):
        #self.file_path = os.path.normpath(file_path)
        #self.filename = os.path.basename(file_path)()
        self.report_name = report_name
        self.procedures = []
        self.group_id = None
        self.is_duplicate = "N"
    def add_procedure(self, procedure):
        if procedure not in self.procedures:
            self.procedures.append(procedure)
    def add_duplicate_grouping(reports):
        report_to_group_id = {}
        group_id_to_report = {}
        next_group_id = 0
        
        for report in reports:
            list_key = tuple(report.procedures)
            if list_key not in report_to_group_id:
                next_group_id +=1
                report_to_group_id[list_key] = next_group_id
            report.group_id  = report_to_group_id[list_key]
            
            if report.group_id not in group_id_to_report:
                group_id_to_report[report.group_id] = []
            group_id_to_report[report.group_id].append(report)
        for reports in group_id_to_report.values():
            if len(reports) > 1:
                for report in reports:
                    report.is_duplicate = "Y"
    
    @staticmethod
    def get_report_procs(procedures, inventory_file, source_directory):
        proc_dict = {procedure.file_path.lower(): procedure for procedure in procedures} 
        inventory_df = Report._load_reports(inventory_file)
        procedureList = []
        #os.makedirs(target_directory, exist_ok=True)
        artifact_dict = {} 
        reports = []
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
                #print(f"Target directory: {target_directory}")

            artifact_dict[artifact_name] = artifact_files

            if pd.isna(artifact_name):
                print(f"Skipping row due to missing artifact name")
                continue
            else:
                curReport = Report(report_name=artifact_name)
            for file in artifact_files:
                source_file_path = os.path.normpath(os.path.join(source_directory, file.lstrip("/")))
                if source_file_path.lower() in proc_dict:
                    procedureList.append(proc_dict[source_file_path.lower()])
                    curReport.add_procedure(proc_dict[source_file_path.lower()])
                else:
                    print(f"Procedure Not Found: {source_file_path}")
            reports.append(curReport)        

        return procedureList
    
    
    @staticmethod
    def get_reports(procedures, inventory_file, source_directory):
        proc_dict = {procedure.file_path.lower(): procedure for procedure in procedures} 
        inventory_df = Report._load_reports(inventory_file)
        procedureList = []
        #os.makedirs(target_directory, exist_ok=True)
        artifact_dict = {} 
        reports = []
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
                #print(f"Target directory: {target_directory}")

            artifact_dict[artifact_name] = artifact_files

            if pd.isna(artifact_name):
                print(f"Skipping row due to missing artifact name")
                continue
            else:
                curReport = Report(report_name=artifact_name)
            for file in artifact_files:
                source_file_path = os.path.normpath(os.path.join(source_directory, file.lstrip("/")))
                if source_file_path.lower() in proc_dict:
                    procedureList.append(proc_dict[source_file_path.lower()])
                    curReport.add_procedure(proc_dict[source_file_path.lower()])
                else:
                    print(f"Procedure Not Found: {source_file_path}")
            reports.append(curReport) 
        return reports           
            
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
