import os
from wf_object import Master
from wf_object import Procedure
from report import Report
from typing import List
from utils import save_errors_to_csv, convert_to_relative_path
import pandas as pd
import csv

scan_directory = os.path.normpath("../OD/CM/Ops")
output_directory = os.path.normpath("../output")
inventory_file = os.path.normpath("../inventory.csv")

masters: List[Master] = Master.get_masters(scan_directory)
print(f"Number of Masters found: {len(masters)}")

procedures: List[Procedure] = Procedure.get_procedures(scan_directory)
print(f"Number of Procedures found: {len(procedures)}")

master_path_dict = {str(master.file_path).lower(): master for master in masters}
procedure_path_dict = {str(procedure.file_path).lower(): procedure for procedure in procedures}
master_name_dict = {master.name.lower(): master for master in masters}  

for master in masters:
    master.add_included_master(scan_directory, output_directory, master_name_dict)

for procedure in procedures:
    procedure.get_hold_tables(master_name_dict, "added_holds.txt", "not_added.txt")

for procedure in procedures:
    procedure.process_procedure(master_name_dict)

for procedure in procedures:
    procedure.get_includes_obj(scan_directory, procedure_path_dict)

report_dict = Report.get_reports(inventory_file, scan_directory, output_directory)

# Process Master Data
data = []
for master in masters:
    created_by_procs = master.created_by_procs if master.created_by_procs else [None]
    included_masters = master.included_masters if master.included_masters else [None]

    if not master.created_by_procs and not master.included_masters:
        data.append([ 
            master.name, 
            convert_to_relative_path(master.file_path, scan_directory, output_directory), 
            '', '', '', ''
        ])
    else:
        for created_by_proc in created_by_procs:
            for used_in_proc in included_masters:
                data.append([
                    master.name,
                    convert_to_relative_path(master.file_path, scan_directory, output_directory),
                    created_by_proc.file_name if created_by_proc else '',
                    convert_to_relative_path(created_by_proc.file_path, scan_directory, output_directory) if created_by_proc else '',
                    used_in_proc.name if used_in_proc else '',
                    convert_to_relative_path(used_in_proc.file_path, scan_directory, output_directory) if used_in_proc else ''
                ])

# Convert to DataFrame and save to CSV
df = pd.DataFrame(data, columns=[
    'master_name', 
    'master_file_path', 
    'created_by_proc_name', 
    'created_by_proc_path', 
    'used_in_proc_name', 
    'used_in_proc_path'
])

df = df.drop_duplicates()
df.to_csv('master_dependency.csv', index=False, encoding='utf-8')

# Process the report dictionary and convert paths to relative
with open('report_procedure.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['report_name', 'obj_url'])
    
    for report, obj_urls in report_dict.items():
        for obj_url in obj_urls:
            writer.writerow([report, obj_url])

# Save errors
save_errors_to_csv()
