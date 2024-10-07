import os
from wfobject import Master
from wfobject import Procedure
from report import Report
from VizBuilder import VizBuilder
import networkx as nx
from networkx.drawing.nx_agraph import from_agraph
import csv

def mark_migrated_objects_by_filenames(migrated_filenames, masters, procedures):
    migrated_set = set(migrated_filenames)

    for master in masters:
        if master.filename in migrated_set:
            master.mark_as_migrated()

    for procedure in procedures:
        if procedure.filename in migrated_set:
            procedure.mark_as_migrated()

def generate_missing_dependencies_report(missing_holds, missing_includes, procedures, inventory_file, scan_directory, output_csv):
    inventory_reports, reports_with_invalid_files = Report.get_reports(procedures, inventory_file, scan_directory) 

    missing_dependencies_set = set()

    for report in inventory_reports:
        if not report.procedures and report.report_name not in reports_with_invalid_files.keys():
            missing_dependencies_set.add((
                report.report_name, 'Missing primary fex', 'N/A', 'AC inventory'
            ))

    for report, invalid_procedures in reports_with_invalid_files.items():
        for proc in invalid_procedures:
            missing_dependencies_set.add((
                    report, 'Primary fex not found in file system', proc, 'AC inventory'
                ))

    for hold, procs in missing_holds.items():
        missing_dependencies_set.add((
            hold, 'master', tuple(procs), 'CM Package'
        ))
    
    for proc, missing_includes in missing_includes.items():
        if missing_includes:
            missing_dependencies_set.add((
                proc.file_path, 'import', tuple(missing_includes), 'CM Package'
            ))

    with open(output_csv, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Missing object name', 'Type', 'Path', 'Missing from'])
        for dep in missing_dependencies_set:
            csv_writer.writerow(dep)

    if missing_dependencies_set:
        print("AC INVENTORY:")
    for dep in missing_dependencies_set:
        if dep[3] == 'AC inventory':
            print(f"\t{dep[1]}: {dep[0]} - {dep[2]}")

    if missing_dependencies_set:
        print("\nCM PACKAGE:")
    for dep in missing_dependencies_set:
        if dep[3] == 'CM Package' and dep[1] == 'import':
            print(f"\tImport not found for {dep[0]} :")
            for proc in dep[2]:
                print(f"\t\t{proc}")
            print()
        if dep[3] == 'CM Package' and dep[1] == 'master':
            print(f"\tTable reference not found in {dep[0]} :")
            for proc in dep[2]:
                print(f"\t\t{proc}")
            print()


if __name__ == "__main__":
    scan_directory = os.path.normpath("/home/BuildScanDirectory/ops/") #scandir proc + master
    output_directory = os.path.normpath("../output/")
    inventory_file = os.path.normpath("../20240823_OPSBI_Webfocus inventory.xlsx")
    exclusion_list = ['common_dates_ibi.fex', 'utility_functions.fex', 'wor02_01_parameters.fex', 'Global_Dates.fex']

    masters = Master.get_masters(scan_directory) #gets all masters from scan
    procedures = Procedure.get_procedures(scan_directory, masters) 
    Master.find_dependencies(masters)
    Master.get_hold_tables(scan_directory, masters, procedures)
    missing_includes = Procedure.get_includes_obj(procedures, scan_directory)
    #num_copied_files = Procedure.copy_used_masters(output_directory, procedures, includes)
    ValidProcs = Report.get_report_procs(procedures, inventory_file, scan_directory)
    proc_dict = {procedure.file_path: procedure for procedure in procedures} 
    master_dict = {master.filename: master for master in masters}
    #ValidProcs = []
    
    """for master in masters:
        if not master.file_path.endswith(master.filename + ".mas"):
            print(f"{master.filename} != {master.file_path}")"""
    reports, _ = Report.get_reports(procedures, inventory_file, scan_directory)
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
    Procedure.report_proc_master_output(reports, "../master_proc.csv")
    Procedure.proc_fmt_output(reports, "../Proc_Output.csv")
    
    missing = set()
    missing_holds_dict = {}


    for procedure in ValidProcs:
        missing_holds = procedure.get_missing_holds(master_dict)
        if missing_holds:
            missing_holds_dict[procedure.filename] = list(missing_holds)
    print(len(missing_holds_dict))
    print(missing_holds_dict)


    generate_missing_dependencies_report(missing_holds_dict, missing_includes, procedures, inventory_file, scan_directory, "missing.csv")

    
    # mark_migrated_objects_by_filenames(["station_master", "soc_irrop_report_00_upgauges_v2.fex", "omi_snapshot_master_staging"], masters, procedures)
    
    # VizBuilder.generate_report_graph(reports, '../images/reports')
    # G = VizBuilder.generate_all_work_graph(reports, '../images')
    # nxg = nx.DiGraph(nx.drawing.nx_agraph.from_agraph(G))
    # VizBuilder.label_interdependent_graphs(reports, "../report_grouping.csv", exclusion_list)
    
    # VizBuilder.save_disconnected_subgraphs_as_svg(nxg, "../images/by_group", exclusion_list, only_interdependent=True, output_csv="../interdependency_group.csv")
    #VizBuilder.analyze_graph(nxg, "../report_grouping.csv")
    # VizBuilder.generate_master_graph(reports, '../images/masters')
    # VizBuilder.generate_procedure_graph(reports, '../images/procedures')
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


