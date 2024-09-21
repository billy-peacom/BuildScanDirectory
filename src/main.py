import os
from wfobject import Master
from wfobject import Procedure
from report import Report
from VizBuilder import VizBuilder
import csv
if __name__ == "__main__":
    scan_directory = os.path.normpath("/home/mike/GetComplexityStats/OneDrive_1_12-8-2024/Change Management - 20240625/Ops_Analytics_20240625/") #scandir proc + master
    procedure_directory = os.path.normpath("../opsfull/") #folder with fexes for initial scan
    output_directory = os.path.normpath("../ac_ops_11/ac_ops_11/")
    inventory_file = os.path.normpath("../20240823_OPSBI_Webfocus inventory.xlsx")


    masters = Master.get_masters(scan_directory) #gets all masters from scan
    procedures = Procedure.get_procedures(scan_directory, masters) 
    Master.find_dependencies(masters)
    Master.get_hold_tables(scan_directory, masters, procedures)
    Procedure.get_includes_obj(procedures, scan_directory)
    #num_copied_files = Procedure.copy_used_masters(output_directory, procedures, includes)
    ValidProcs = Report.get_report_procs(procedures, inventory_file, scan_directory)
    proc_dict = {procedure.file_path: procedure for procedure in procedures} 
    #ValidProcs = []
    reports = Report.get_reports(procedures, inventory_file, scan_directory)
    Report.add_duplicate_grouping(reports)
    #reports = []
    """with open("/home/mike/_BuilderBillyFixTest/BuildScanDirectory/Ops11Inventory.csv", newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
                
            if 'path:' in row[1]:
                # Split on 'path:' and take the part after it
                paths = row[1].split('path:')[1:]
                for path in paths:
                    if path.strip() in proc_dict:
                        ValidProcs.append(proc_dict[path.strip()])
                        cur_report = Report(report_name=row[0])
                        cur_report.add_procedure(proc_dict[path.strip()])
                        reports.append(cur_report)
                    else:
                        pass#print(f"Not Found: {path}")
    """
    Procedure.copy_related_objects_iterative(ValidProcs, output_directory)    
    Procedure.report_proc_output(reports, "../report_proc.csv")
    Procedure.master_proc_output(reports, "../master_created_proc.csv")
    Procedure.proc_fmt_output(reports, "../Proc_Output.csv")
    for report in reports:
        print(report.report_name)
        for proc in report.procedures:
            print(proc.filename)
            for master in proc.masters:
                print(master.filename)
                for created_proc in master.created_by_proc:
                    print(f"Created proc: {created_proc.filename}")
    #for master in masters:
    #    if master.created_by_proc:
    #        for proc in master.created_by_proc:
    #            print(f"{master.filename} : {proc.filename}")
    #VizBuilder.generate_report_graph(reports, '../images/reports')
    
    
            
    #VizBuilder.generate_master_graph(reports, '../images/masters')
    #VizBuilder.generate_procedure_graph(reports, '../images/procedures')
    #VizBuilder.generate_report_dot(reports, "../images/reports_dot")
    #myset = set()
    #for procedure in procedures:
    #    procedure.outputs = procedure.get_output_format()
    
        
    #print(len(reports))
    
    #VizBuilder.generate_report_graph(reports, '/home/mike/_BuilderBillyFixTest/BuildScanDirectory/images')
    #num_copied_files = Procedure.copy_used_masters_2(output_directory, procedures)
    #report_dict = Report.copy_reports(inventory_file, scan_directory, output_directory)
    #Procedure.copy_related_objects_recurse(ValidProcs, output_directory)
    # Procedure.get_output_csv(procedures) 
    #print(f"Total number of master files copied: {num_copied_files}")
