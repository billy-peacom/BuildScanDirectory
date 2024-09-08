import os
import shutil
import re
import csv
import pygraphviz as pgv
from collections import defaultdict
class Master:
    def __init__(self, path, filename, created_by=None):
        self.path = path
        self.filename = filename.lower()    
        self.created_by = created_by
        self.dependencies = []    
        self.created_by_proc = [] #todo
    def add_dependency(self, master):
        """
        Adds a Master object as a dependency to this Master.
        """
        if isinstance(master, Master) and master not in self.dependencies:
            self.dependencies.append(master)

    @staticmethod
    def get_masters(directory):
        """
        Searches the given directory for all '.mas' files, extracts the FILENAME value from each,
        and returns a list of Master objects.
        """
        masters = []

          
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.mas'):    
                    file_path = os.path.join(root, file)

                      
                    master_obj = None
                    with open(file_path, 'r') as f:
                        for line in f:
                            line_lower = line.strip().lower()
                            if line_lower.startswith("filename="):
                                  
                                filename = line.split('=')[1].split(',')[0].strip().lower()
                                master_obj = Master(path=file_path, filename=filename)
                                break    

                    if master_obj:
                        masters.append(master_obj)

        return masters

    @staticmethod
    def find_dependencies(masters):
        """
        Scans through the existing list of Master objects to find and add dependencies.
        """
        master_dict = {master.filename: master for master in masters}    

        for master in masters:
            #print(f"Master: {master.filename}" )
            with open(master.path, 'r') as f:
                for line in f:
                    line_lower = line.strip().lower()
                    if "crfile=" in line_lower:
                        crfile_parts = line_lower.split('crfile=')
                        if len(crfile_parts) > 1:
                            crfile_path = crfile_parts[1].split(',')[0].strip()
                            dependent_filename = os.path.basename(crfile_path).split('.')[0].lower()
                            if dependent_filename in master_dict:
                                master.add_dependency(master_dict[dependent_filename])
                                #print(f"Dependancy Found: {dependent_filename}")

    def add_created_by_proc(self, procedure_filename):
        """
        Adds the name of the procedure that created this master to the created_by_proc list.
        """
        if procedure_filename not in self.created_by_proc:
            self.created_by_proc.append(procedure_filename)

    @staticmethod
    def get_hold_tables(directory, masters):
        """
        Searches the given directory for all '.fex' files, extracts hold table references,
        and checks if they match any Master filenames. If they do, the corresponding
        Master is added to the Procedure's list of masters.
        """
        
        hold_regex = re.compile(r"^\s*on\s+(table|graph)\s+hold\s+as\s+(\S+)", re.IGNORECASE)
        app_hold_regex = re.compile(r"^\s*app\s+", re.IGNORECASE)

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.fex'):    
                    file_path = os.path.join(root, file)
                    procedure = Procedure(file_path=file_path)
                    hold = False
                    i = 1
                    with open(file_path, 'r', encoding='utf8') as f:
                        try:
                            for line in f:
                                i+=1
                                line_lower = line.strip().lower()

                                if app_hold_regex.search(line_lower):
                                    hold = True

                                if hold:
                                    hold_match = hold_regex.search(line_lower)
                                if hold_match:
                                    hold_name = hold_match.group(2).lower()
                                    
                                    if "/" in hold_name:
                                        hold_name = hold_name.rsplit('/',1)[-1]
                                    for master in masters:
                                        if master.filename == hold_name:
                                            master.add_created_by_proc(procedure)
                                            break   

                        except Exception as e:
                            pass#print(e)
class Procedure:
    def __init__(self, file_path, includes=None):
        self.file_path = file_path
        self.filename = os.path.basename(file_path).lower()    
        self.includes = includes if includes is not None else []
        self.masters = []
        self.includes = [] #todo

    def add_master(self, master):
        """
        Adds a Master object to the Procedure's list of masters.
        """
        if isinstance(master, Master) and master not in self.masters:
            self.masters.append(master)

    @staticmethod
    def get_procedures(directory, masters):
        """
        Searches the given directory for all '.fex' files, extracts table references,
        and checks if they match any Master filenames. If they do, the corresponding
        Master is added to the Procedure's list of masters.
        """
        procedures = []

          
        for root, dirs, files in os.walk(directory):
            pattern = re.compile(r"^\s*(table|graph)\s+file", re.IGNORECASE)
            for file in files:
                if file.lower().endswith('.fex'):    
                    file_path = os.path.join(root, file)
                    procedure = Procedure(file_path=file_path)

                      
                    with open(file_path, 'r', encoding='utf8') as f:
                        for line in f:
                            line_lower = line.strip().lower()  
                            if re.search(pattern, line_lower):  
                                  
                                table_name = line.split()[-1].strip().lower()
                                  
                                for master in masters:
                                    if master.filename == table_name:
                                        #print(f"{table_name}: {procedure.filename}")
                                        procedure.add_master(master)
                                        break    

                    procedures.append(procedure)

        return procedures


    @staticmethod
    def collect_all_dependencies(master, collected=None):
        """
        Recursively collects all dependencies of a master.
        """
        if collected is None:
            collected = set()
        
        if master not in collected:
            collected.add(master)
            for dependency in master.dependencies:
                Procedure.collect_all_dependencies(dependency, collected)
        
        return collected

    @staticmethod
    def __copy_parents(src, dest_folder, dir_offset=10):
        prev_offset = 0 if dir_offset == 0 else src.replace('/', '%', dir_offset - 1).find('/') + 1
        post_offset = src.rfind('/')

        src_dirs = '' if post_offset == -1 else src[prev_offset:post_offset]
        src_filename = src[post_offset + 1:]

        os.makedirs(f'{dest_folder}/{src_dirs}', exist_ok=True)
        shutil.copy(src, f'{dest_folder}/{src_dirs}/{src_filename}')

        #os.makedirs(f'{dest_folder}/{os.path.dirname(src)}', exist_ok=True)
        #shutil.copy(src, f'{dest_folder}/{src_filename}')

    @staticmethod
    def copy_used_masters(output_directory, procedures):
        """
        Copies all Master files associated with any Procedure, including dependencies,
        to the specified output directory.
        """
        os.makedirs(output_directory, exist_ok=True)
        copied_files = set()   
        copied_holds = set() 
            
        for procedure in procedures:
            for master in procedure.masters:
                all_masters = Procedure.collect_all_dependencies(master)
                #print(f"Master: {master.file_name}")
                for m in all_masters:
                    for created_by in m.created_by_proc:
                        if created_by.file_path not in copied_holds:
                            #os.makedirs(f'{output_directory}/holds', exist_ok=True)
                            #shutil.copy(created_by.file_path, f"{output_directory}/holds/{created_by.filename}") 
                            Procedure.__copy_parents(created_by.file_path, output_directory)
                            copied_holds.add(created_by.file_path)
                            
                    if m.path not in copied_files:
                        Procedure.__copy_parents(m.path,output_directory)
                        pre, ext = os.path.splitext(m.path)
                        try:
                            Procedure.__copy_parents(pre + ".acx",output_directory)
                        except:
                            pass
                            # print(f"file not found {pre}.acx")
                            
                        #shutil.copy(m.path, output_directory)
                        copied_files.add(m.path)
                        #print(f"Copied: {m.filename} from {m.path} to {output_directory}")

        return len(copied_files)
    @staticmethod
    def get_output_csv(procedures, output_file="Master Dependency.csv"):
        unique_rows = set()

        with open(output_file, 'w', newline='') as masterDependancy:
            csvwriter = csv.writer(masterDependancy)

            csvwriter.writerow(['Master Filename', 'master file path', 'Created By Proc File Path', 'Created by Proc File Name', 'Used in Proc'])

            for procedure in procedures:
                for master in procedure.masters:
                    for proc in master.created_by_proc:
                        row = (master.filename, master.path, proc.file_path, proc.filename, procedure.file_path)

                        if row not in unique_rows:
                            unique_rows.add(row)
                            csvwriter.writerow(row)

        print(f"CSV file '{output_file}' created with unique rows.")
        
    def get_output_csv_mp(procedures, output_file="Masters Procs.csv"):
        unique_rows = set()

        with open(output_file, 'w', newline='') as masterDependancy:
            csvwriter = csv.writer(masterDependancy)

            csvwriter.writerow(['Master Filename', 'master file path', 'Used in Procedure name', 'Procedure Path'])

            for procedure in procedures:
                for master in procedure.masters:
                    row = (master.filename, master.path, procedure.filename,procedure.file_path)

                    if row not in unique_rows:
                        unique_rows.add(row)
                        csvwriter.writerow(row)

        print(f"CSV file '{output_file}' created with unique rows.")
    @staticmethod
    def get_procedures_using_master(target_master):
        """
        Finds and returns a list of procedures that use the given master.
        """
        # Filter through procedures to find those using the target master
        procedures_using_master = []
        for procedure in Procedure.get_procedures(procedure_directory, masters):
            if target_master in procedure.masters:
                procedures_using_master.append(procedure)
        return procedures_using_master
    
class MasterCentricVisualization:
    @staticmethod
    def create_single_master_image(master, output_dir='master_dependency_images'):
        """
        Creates a flowchart-style visualization for a single master and its dependencies, 
        created_by_procs, and using procedures.
        """
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Initialize a directed graph for the master dependency
        G = pgv.AGraph(directed=True)

        # Add the master as the central node
        G.add_node(master.filename, label=master.filename, shape='box', style='filled', fillcolor='yellow', group='center')

        # Add dependencies (Masters this master depends on) on the left
        for dependency in master.dependencies:
            G.add_node(dependency.filename, label=dependency.filename, shape='box', style='filled', fillcolor='orange', group='left')
            G.add_edge(dependency.filename, master.filename, label='depends on', color='orange')
            for dependency2nd in dependency.dependencies:
                G.add_node(dependency2nd.filename, label=dependency2nd.filename, shape='box', style='filled', fillcolor='orange', group='left')
                G.add_edge(dependency2nd.filename, dependency.filename, label='depends on', color='orange')
        # Add the procedures that created this master (above the master)
        for proc in master.created_by_proc:
            G.add_node(proc.filename, label=proc.filename, shape='box', style='filled', fillcolor='lightblue', group='top')
            G.add_edge(proc.filename, master.filename, label='created', color='blue')

        # Add the procedures that use this master (on the right)
        for procedure in Procedure.get_procedures_using_master(master):
            G.add_node(procedure.filename, label=procedure.filename, shape='box', style='filled', fillcolor='lightgreen', group='right')
            G.add_edge(master.filename, procedure.filename, label='used in', color='green')

        # Save the graph as an image
        output_image = os.path.join(output_dir, f"{master.filename}_dependency.svg")
        G.layout(prog='dot')
        G.draw(output_image)
    def create_single_report_image(reportName, proceduire, output_dir='report_dependency_images'):
        """
        Creates a flowchart-style visualization for a single master and its dependencies, 
        created_by_procs, and using procedures.
        """
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Initialize a directed graph for the master dependency
        G = pgv.AGraph(directed=True)

        
        # Add the master as the central node
        G.add_node(master.filename, label=master.filename, shape='box', style='filled', fillcolor='yellow', group='center')

        # Add dependencies (Masters this master depends on) on the left
        for dependency in master.dependencies:
            G.add_node(dependency.filename, label=dependency.filename, shape='box', style='filled', fillcolor='orange', group='left')
            G.add_edge(dependency.filename, master.filename, label='depends on', color='orange')
            for dependency2nd in dependency.dependencies:
                G.add_node(dependency2nd.filename, label=dependency2nd.filename, shape='box', style='filled', fillcolor='orange', group='left')
                G.add_edge(dependency2nd.filename, dependency.filename, label='depends on', color='orange')
        # Add the procedures that created this master (above the master)
        for proc in master.created_by_proc:
            G.add_node(proc.filename, label=proc.filename, shape='box', style='filled', fillcolor='lightblue', group='top')
            G.add_edge(proc.filename, master.filename, label='created', color='blue')

        # Add the procedures that use this master (on the right)
        for procedure in Procedure.get_procedures_using_master(master):
            G.add_node(procedure.filename, label=procedure.filename, shape='box', style='filled', fillcolor='lightgreen', group='right')
            G.add_edge(master.filename, procedure.filename, label='used in', color='green')

        # Save the graph as an image
        output_image = os.path.join(output_dir, f"{master.filename}_dependency.svg")
        G.layout(prog='dot')
        G.draw(output_image)

    @staticmethod
    def visualize_each_master(masters, output_dir='master_dependency_images_fulltest'):
        """
        Creates a separate flowchart image for each master and its dependencies, 
        created_by_procs, and using procedures.
        """
        # Loop through each master and create a separate image
        for master in masters:
            MasterCentricVisualization.create_single_master_image(master, output_dir)
    def load_report_mapping(report_mapping_file):
        """
        Loads the report mapping from a CSV file with two columns: Report Name, ProcedurePath.
        """
        report_mapping = {}
        with open(report_mapping_file, mode='r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) == 2:
                    report_name, procedure_path = row
                    if procedure_path not in report_mapping:
                        report_mapping[procedure_path] = []
                    report_mapping[procedure_path].append(report_name)
        return report_mapping

# Example Usage:

if __name__ == "__main__":
    scan_directory = "/home/mike/GetComplexityStats/OneDrive_1_12-8-2024/Change Management - 20240625/Ops_Analytics_20240625/"
    procedure_directory = "/home/mike/GetComplexityStats/ac_ops_11/"
    output_directory = "/home/mike/GetComplexityStats/testfullscan/ac_ops_11/Dependencies"

    # Gather masters and procedures as in your current code
    masters = Master.get_masters(scan_directory)
    Master.find_dependencies(masters)
    holds = Master.get_hold_tables(scan_directory, masters)
    procedures = Procedure.get_procedures(procedure_directory, masters)

    # Generate one image per ETL dependency
    for procedure in procedures:
        for master in procedure.masters:
            MasterCentricVisualization.create_single_master_image(master, 'master_dependency_images')
            #MasterCentricVisualization.visualize_each_master(master)

""" 
if __name__ == "__main__":

    scan_directory = "/home/mike/GetComplexityStats/ac_ops_11/"
    procedure_directory = "/home/mike/GetComplexityStats/ac_ops_11/"
    output_directory = "/home/mike/GetComplexityStats/ac_ops_11/Dependancies"


    masters = Master.get_masters(scan_directory)


    Master.find_dependencies(masters)

    #Todo - Add a function for procs to capture includes and add them to the AC_ops_11 dir  getincludes()  copy_included_procs()
    #Todo - Grab all master created_by_proc []
    holds = Master.get_hold_tables(scan_directory, masters)


    #Todo - move those procedures (.fex) to the procedure_directory


    procedures = Procedure.get_procedures(procedure_directory, masters)


    #num_copied_files = Procedure.copy_used_masters(output_directory, procedures)
    #Todo - Output csv : master.filename | procedure.filePath | master.path
    #print(f"Total number of master files copied: {num_copied_files}") 
    Procedure.get_output_csv(procedures)
    Procedure.get_output_csv_mp(procedures)
    
"""