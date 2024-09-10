import os
from wfobject import Master
from wfobject import Procedure
from report import Report

if __name__ == "__main__":
    scan_directory = os.path.normpath("/home/mike/GetComplexityStats/OneDrive_1_12-8-2024/Change Management - 20240625/Ops_Analytics_20240625/") #scandir proc + master
    procedure_directory = os.path.normpath("../opsfull/") #folder with fexes for initial scan
    output_directory = os.path.normpath("/home/mike/GetComplexityStats/ac_ops_11/")
    inventory_file = os.path.normpath("../20240823_OPSBI_Webfocus inventory.xlsx")


    masters = Master.get_masters(scan_directory) #gets all masters from scan
    procedures = Procedure.get_procedures(scan_directory, masters)
    Master.find_dependencies(masters)
    Master.get_hold_tables(scan_directory, masters, procedures)

    
    #includes = Procedure.get_includes(scan_directory)
    
    Procedure.get_includes_obj(procedures, scan_directory)
    #num_copied_files = Procedure.copy_used_masters(output_directory, procedures, includes)
    ValidProcs = Report.get_report_procs(procedures, inventory_file, scan_directory)
    
    
    #num_copied_files = Procedure.copy_used_masters_2(output_directory, procedures)
    #report_dict = Report.copy_reports(inventory_file, scan_directory, output_directory)
    Procedure.copy_related_files(ValidProcs, output_directory)
    # Procedure.get_output_csv(procedures) 
    #print(f"Total number of master files copied: {num_copied_files}")
