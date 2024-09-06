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
    def __init__(self, file_path, includes=None, includes_key=None):
        self.file_path = os.path.normpath(file_path)  
        self.filename = os.path.basename(file_path).lower()    
        self.includes = includes or []
        self.masters = []
        self.includes_key = includes_key

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
    def get_procedures(directory, masters, all_includes):
        """
        Searches the given directory for all '.fex' files, extracts table references,
        and checks if they match any Master filenames. If they do, the corresponding
        Master is added to the Procedure's list of masters.
        """
        procedures = []

          
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.fex'):    
                    file_path = os.path.normpath(os.path.join(root, file))

                    relative_path = os.path.relpath(file_path, directory)
                    file_name = os.path.basename(relative_path)
                    parent_folder = os.path.basename(os.path.dirname(relative_path))
                    search_path = os.path.normpath(os.path.join(parent_folder, file_name))


                    possible_keys = [key for key in all_includes if search_path in key]

                    includes_key = possible_keys[0] if len(possible_keys) == 1 else None
                    includes = all_includes.get(includes_key, []) if len(possible_keys) == 1 else []
                    if len(possible_keys) > 1:
                        print(f"Searching possible keys resulted in more than 1 match.\n Procedure: {file_path}\nSearch term {search_path}:\n\t{possible_keys}\n")


                    procedure = Procedure(file_path=file_path, includes=includes, includes_key=includes_key)

                      
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
    def copy_used_masters(output_directory, procedures, all_includes):
        """
        Copies all Master files associated with any Procedure, including dependencies,
        to the specified output directory.
        """
        os.makedirs(output_directory, exist_ok=True)
        copied_files = set()   
        copied_holds = set() 
            
        for procedure in procedures:
            includes = all_includes.get(procedure.includes_key, [])

            for include in includes:
                Procedure.copy_file_and_includes(include, output_directory, copied_files, all_includes)


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
    def copy_file_and_includes(file_path, output_directory, copied_files, all_includes):
        if file_path in copied_files:
            return

        file_name = os.path.basename(file_path)
        dest_path = os.path.join(output_directory, file_name)

        if not os.path.exists(dest_path):
            shutil.copy(file_path, dest_path)
            copied_files.add(file_path)
            print(f"Copied {file_path} to {output_directory}")

        includes = all_includes.get(file_path, [])
        for include in includes:
            if include not in copied_files:
                Procedure.copy_file_and_includes(include, output_directory, copied_files, all_includes)
    
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
    def get_includes(scan_directory):
        # search everything in scan_directory
        # for every file that has includes
        # append the file path and the list of includes to a dictionary
        include_dictionary = {}

        include_regex = re.compile(r"^(?!\s*-?\s*-\*)\s*-?\s*INCLUDE\s*(?:=\s*)?(?:[A-Za-z]+:)?([\/\.\w]+\.fex)", re.IGNORECASE)

        for root, dirs, files in os.walk(scan_directory):
            for file in files:
                if file.lower().endswith('.fex'):    
                    procedure_path = os.path.normpath(os.path.join(root, file))
                    found_includes = []
                    try:
                        with open(procedure_path, 'r', encoding='utf8') as f:
                                for line in f:
                                    line = line.strip()

                                    include_match = include_regex.search(line)
                                    if include_match:
                                        include_name = include_match.group(1).lower()

                                        if include_name.startswith("."):
                                            include_name = os.path.normpath(os.path.join(root, include_name))
                                        else:
                                            include_name = f"{scan_directory}\\{include_name}"
                                            include_name = os.path.normpath(include_name)

                                        found_includes.append(include_name)

                    except Exception as e:
                        print(e)

                    if found_includes and procedure_path not in include_dictionary:
                        include_dictionary[procedure_path] = found_includes
                    elif found_includes and procedure_path in include_dictionary:
                        print(f"Key {procedure_path} already exists in dictionary appending includes")
                        for include in found_includes:
                            if include not in include_dictionary[procedure_path]:
                                include_dictionary[procedure_path].append(include)


        return include_dictionary



  
if __name__ == "__main__":

    scan_directory = os.path.normpath("OD/CM/Ops") #scandir proc + master
    procedure_directory = os.path.normpath("ac_ops_11") #folder with fexes for initial scan
    output_directory = os.path.normpath("ac_ops_11/data/fullpath")


    masters = Master.get_masters(scan_directory)


    Master.find_dependencies(masters)

    #Todo - Add a function for procs to capture includes and add them to the AC_ops_11 dir  getincludes()  copy_included_procs()

    #Todo - Grab all master created_by_proc []
    # Master.get_hold_tables(scan_directory, masters)


    includes = Procedure.get_includes(scan_directory)
    #Todo - move those procedures (.fex) to the procedure_directory
    # print(includes)

    procedures = Procedure.get_procedures(procedure_directory, masters, includes)


    num_copied_files = Procedure.copy_used_masters(output_directory, procedures, includes)

    # output_csv = Procedure.get_output_csv(procedures)
    #Todo - Output csv : master.filename | procedure.filePath | master.path
    # print(f"Total number of master files copied: {num_copied_files}") 
