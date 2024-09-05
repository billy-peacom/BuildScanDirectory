import os
import shutil
import re
import csv
class Master:
    def __init__(self, path, filename, created_by=None):
        self.path = os.path.normpath(path)
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
                            else:
                                print("Dependency file not in master dict")

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
        
        hold_regex = re.compile(r"on\s+(table|graph)\s+hold\s+as\s+(\S+)", re.IGNORECASE)
        app_hold_regex = re.compile(r"app\s+hold", re.IGNORECASE)

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

                                        for master in masters:
                                            if master.filename == hold_name:
                                                master.add_created_by_proc(procedure)
                                                break   

                        except Exception as e:
                            print(e)
class Procedure:
    def __init__(self, file_path, includes=None):
        self.file_path = os.path.normpath(file_path)  
        self.filename = os.path.basename(file_path).lower()    
        self.includes = includes or []
        self.masters = []

    def add_master(self, master):
        """
        Adds a Master object to the Procedure's list of masters.
        """
        if isinstance(master, Master) and master not in self.masters:
            self.masters.append(master)


    def add_include(self, include):
        if include not in self.includes:
            self.includes.append(include)

    @staticmethod
    def get_procedures(directory, masters):
        """
        Searches the given directory for all '.fex' files, extracts table references,
        and checks if they match any Master filenames. If they do, the corresponding
        Master is added to the Procedure's list of masters.
        """
        procedures = []

          
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.fex'):    
                    file_path = os.path.join(root, file)
                    procedure = Procedure(file_path=file_path)

                      
                    with open(file_path, 'r', encoding='utf8') as f:
                        for line in f:
                            line_lower = line.strip().lower()    
                            if "graph file" in line_lower or "table file" in line_lower or "define file" in line_lower:    #todo, change to regex match
                                  
                                table_name = line.split()[-1].strip().lower()

                                  
                                for master in masters:
                                    if master.filename == table_name:
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
    def __copy_parents(src, dest_folder, dir_offset=0):
        src = os.path.normpath(src)
        dest_folder = os.path.normpath(dest_folder)

        prev_offset = 0 if dir_offset == 0 else src.replace(os.sep, '%', dir_offset - 1).find(os.sep) + 1
        post_offset = src.rfind(os.sep)

        src_dirs = '' if post_offset == -1 else src[prev_offset:post_offset]
        src_filename = src[post_offset + 1:]

        dest_dir = os.path.join(dest_folder, src_dirs)
        os.makedirs(dest_dir, exist_ok=True)

        shutil.copy(src, os.path.join(dest_dir, src_filename))

    # @staticmethod
    # def __copy_parents(src, dest_folder, dir_offset=0):
    #     src = os.path.normpath(src)
    #     dest_folder = os.path.normpath(dest_folder)  # Normalize destination folder path
    #     prev_offset = 0 if dir_offset == 0 else src.replace('/', '%', dir_offset - 1).find('/') + 1
    #     post_offset = src.rfind('/')
    #     create_folder = os.path.dirname(os.path.join(dest_folder, src))
    #     dest_folder = os.path.join(dest_folder, os.path.basename(src))

    #     src_dirs = '' if post_offset == -1 else src[prev_offset:post_offset]
    #     src_filename = src[post_offset + 1:]

    #     # os.makedirs(f'{dest_folder}/{src_dirs}', exist_ok=True)
    #     # shutil.copy(src, f'{dest_folder}/{src_dirs}/{src_filename}')
    #     os.makedirs(create_folder, exist_ok=True)
    #     shutil.copy(src, f'{dest_folder}\\{src_filename}')

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

                for m in all_masters:
                    for created_by in m.created_by_proc:
                        if created_by.file_path not in copied_holds:
                            os.makedirs(f'{output_directory}\\holds', exist_ok=True)
                            shutil.copy(created_by.file_path, f"{output_directory}\\holds\\{created_by.filename}") 
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
    def get_output_csv(procedures, output_file="output.csv"):
        unique_rows = set()

        with open(output_file, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)

            csvwriter.writerow(['Master Filename', 'Procedure File Path', 'Master File Path'])

            for procedure in procedures:
                for master in procedure.masters:
                    row = (master.filename, procedure.file_path, master.path)

                    if row not in unique_rows:
                        unique_rows.add(row)
                        csvwriter.writerow(row)

        print(f"CSV file '{output_file}' created with unique rows.")
    
    @staticmethod
    def get_includes(scan_directory, procedures, procedure_directory):
        include_regex = re.compile(r"^(?!\s*-?\s*-\*)\s*-?\s*INCLUDE\s*(?:=\s*)?(?:[A-Za-z]+:)?(?:[\/\.\w]+\/)?([\w]+\.fex)", re.IGNORECASE)
        unique_includes = set()

        for root, dirs, files in os.walk(procedure_directory):
            for file in files:
                if file.lower().endswith('.fex'):    
                    procedure_path = os.path.join(root, file)

                    with open(procedure_path, 'r', encoding='utf8') as f:
                        try:
                            for line in f:
                                line = line.strip()

                                include_match = include_regex.search(line)
                                if include_match:
                                    include_name = include_match.group(1).lower()

                                    for procedure in procedures:
                                        if procedure.file_path == procedure_path:
                                            unique_includes.add(include_name)
                                            procedure.add_include(include_name)                      

                        except Exception as e:
                            print(e)
        for include in unique_includes:
            found_files = []

            for root, dirs, files in os.walk(scan_directory):
                for file in files:
                    if file.lower() == include:
                        found_files.append(os.path.join(root, file))

            if len(found_files) == 1:
                src = found_files[0]
                dest = os.path.join(procedure_directory, include)

                os.makedirs(procedure_directory, exist_ok=True)
                shutil.copy(src, dest)
            elif len(found_files) > 1:
                print(f"Error: Multiple files found for {include}: {found_files}. Skipping.\n")
            else:
                print(f"Warning: No file found for {include} in {scan_directory}. Skipping.\n")


  
if __name__ == "__main__":

    scan_directory = os.path.normpath("OD/CM/Ops") #scandir proc + master
    procedure_directory = os.path.normpath("ac_ops_11") #folder with fexes for initial scan
    output_directory = os.path.normpath("ac_ops_11/data/fullpath")


    masters = Master.get_masters(scan_directory)


    Master.find_dependencies(masters)

    #Todo - Add a function for procs to capture includes and add them to the AC_ops_11 dir  getincludes()  copy_included_procs()

    #Todo - Grab all master created_by_proc []
    Master.get_hold_tables(scan_directory, masters)


    #Todo - move those procedures (.fex) to the procedure_directory


    procedures = Procedure.get_procedures(procedure_directory, masters)
    Procedure.get_includes(scan_directory, procedures, procedure_directory)


    num_copied_files = Procedure.copy_used_masters(output_directory, procedures)

    output_csv = Procedure.get_output_csv(procedures)
    #Todo - Output csv : master.filename | procedure.filePath | master.path
    print(f"Total number of master files copied: {num_copied_files}") 
