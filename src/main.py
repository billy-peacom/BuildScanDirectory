import os
from master import Master
from procedure import Procedure
from report import Report

if __name__ == "__main__":
    scan_directory = os.path.normpath("../OD/CM/Ops") #scandir proc + master
    procedure_directory = os.path.normpath("../ac_ops_11") #folder with fexes for initial scan
    output_directory = os.path.normpath("../ac_ops_11/data/fullpath")
    inventory_file = os.path.normpath("../20240823_OPSBI_Webfocus inventory.xlsx")


    # masters = Master.get_masters(scan_directory) #gets all masters from scan
    # Master.find_dependencies(masters)
    # hold_table_data = Master.get_hold_tables(scan_directory, masters)

    # for file_path, hold_name in hold_table_data:
    #     procedure = Procedure(file_path=file_path)
    #     Master._match_master_to_hold(hold_name, masters, procedure)

    # includes = Procedure.get_includes(scan_directory)
    # procedures = Procedure.get_procedures(procedure_directory, masters, includes)
    # num_copied_files = Procedure.copy_used_masters(output_directory, procedures, includes)

    report_dict = Report.copy_reports(inventory_file, scan_directory, output_directory)

    # Procedure.get_output_csv(procedures) 
    # print(f"Total number of master files copied: {num_copied_files}")
