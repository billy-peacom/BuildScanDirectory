import os
import shutil
import re
import csv
from utils import _read_file_lines
class Master:
    def __init__(self, path, filename, created_by=None):
        self.path = os.path.normpath(path)
        self.filename = filename     
        self.created_by = created_by
        self.dependencies = [] #Of type master  (self)   
        self.created_by_proc = [] #of type procedure

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
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.mas'):    
                    file_path = os.path.join(root, file)
                    lines = _read_file_lines(file_path)
                    for line in lines:
                        filename = Master.extract_filename(line)
                        if filename:
                            master_obj = Master(path=file_path, filename=filename)   
                            masters.append(master_obj)
                            break
        return masters

    @staticmethod
    def extract_filename(line):
        match = re.match(r'^filename\s*=\s*([^,\s]+)', line, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def find_dependencies(masters):
        """
        Scans through the existing list of Master objects to find and add dependencies.
        """
        master_dict = {master.filename.lower(): master for master in masters}    

        for master in masters:
            lines = _read_file_lines(master.path)
            for line in lines:
                Master._extract_and_add_dependency(line, master, master_dict)

    @staticmethod
    def _extract_and_add_dependency(line, master, master_dict):
        crfile_regex = re.compile(r'crfile\s*=\s*([^,\s]+)', re.IGNORECASE)

        match = crfile_regex.search(line)
        if match:
            crfile_path = match.group(1).strip()
            dependent_filename = os.path.basename(crfile_path).split('.')[0]
            if dependent_filename.lower() in master_dict:
                master.add_dependency(master_dict[dependent_filename.lower()])
            else:
                print("Dependency file not in master dict")

    def add_created_by_proc(self, procedure):
        """
        Adds the name of the procedure that created this master to the created_by_proc list.
        """
        if procedure not in self.created_by_proc:
            self.created_by_proc.append(procedure)

    @staticmethod
    def get_hold_tables(directory, masters, procedures):
        """
        Searches the given directory for all '.fex' files, extracts hold table references,
        and checks if they match any Master filenames. If they do, the corresponding
        Master is added to the Procedure's list of masters.
        """
        hold_regex = re.compile(r"on\s+(table|graph)\s+hold\s+as\s+(\S+)", re.IGNORECASE)
        master_dict = {master.filename.lower(): master for master in masters}    
        #procedure_dict = {procedure.file_path: procedure for procedure in procedures}
        for procedure in procedures:            
            lines = _read_file_lines(procedure.file_path)
            for line in lines:
                hold_match = hold_regex.search(line)
                if hold_match:
                    hold_name = hold_match.group(2)
                    if hold_name.lower() in master_dict:
                        master_dict[hold_name.lower()].add_created_by_proc(procedure)
                        print(master_dict[hold_name.lower()].path)
    
        #return hold_table_data


    @staticmethod
    def _match_master_to_hold(hold_name, masters, procedure):
        for master in masters:
            if master.filename == hold_name:
                master.add_created_by_proc(procedure)
                break


class Procedure:
    def __init__(self, file_path, includes=None, includes_key=None):
        self.file_path = os.path.normpath(file_path)  
        self.filename = os.path.basename(file_path)    
        self.includes = includes or [] #of type procedure
        self.masters = [] #Of type master
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
    def get_procedures(directory, masters):
        """
        Searches the given directory for all '.fex' files, extracts table references,
        and checks if they match any Master filenames.
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
    def _process_fex_file(root, file, directory, masters):
        file_path = os.path.normpath(os.path.join(root, file))
        search_path = Procedure._build_search_path(file_path, directory)
        pattern = re.compile(r"^\s*(table|graph)\s+file", re.IGNORECASE)
        
        #includes_key, includes = Procedure._get_includes_key(search_path, all_includes)
        procedure = Procedure(file_path=file_path)
        lines = _read_file_lines(file_path)
        for line in lines:
            if "graph file" in line or "table file" in line or "define file" in line:
                table_name = line.split()[-1].strip()
                Procedure._match_table_to_master(table_name, procedure, masters)
        return procedure

    @staticmethod
    def _build_search_path(file_path, directory):
        relative_path = os.path.relpath(file_path, directory)
        file_name = os.path.basename(relative_path)
        parent_folder = os.path.basename(os.path.dirname(relative_path))
        return os.path.normpath(os.path.join(parent_folder, file_name))

    @staticmethod
    def _get_includes_key(search_path, all_includes):
        possible_keys = [key for key in all_includes if search_path in key]
        includes_key = possible_keys[0] if len(possible_keys) == 1 else None
        includes = all_includes.get(includes_key, []) if includes_key else []
        return includes_key, includes

    @staticmethod
    def _match_table_to_master(table_name, procedure, masters):
        for master in masters:
            if master.filename == table_name:
                procedure.add_master(master)
                break

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
    def copy_used_masters(output_directory, procedures):
        """
        Copies all Master files associated with any Procedure, including dependencies,
        to the specified output directory.
        """
        os.makedirs(output_directory, exist_ok=True)
        copied_files = set()
        for procedure in procedures:
            #Procedure._copy_includes(procedure, all_includes, output_directory, copied_files)
            Procedure._copy_masters(procedure, output_directory, copied_files)

        return len(copied_files)
    @staticmethod
    def copy_used_masters_2(output_directory, procedures):
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
    def _copy_includes(procedure, all_includes, output_directory, copied_files):
        includes = all_includes.get(procedure.includes_key, [])
        for include in includes:
            Procedure.copy_file_and_includes(include, output_directory, copied_files, all_includes)

    @staticmethod
    def _copy_masters(procedure, output_directory, copied_files):
        for master in procedure.masters:
            all_masters = Procedure.collect_all_dependencies(master)
            for m in all_masters:
                if m.path not in copied_files:
                    Procedure.__copy_parents(m.path, output_directory)
                    copied_files.add(m.path)

    @staticmethod
    def copy_file_and_includes(file_path, output_directory, copied_files, all_includes):
        if file_path in copied_files:
            return
        file_name = os.path.basename(file_path)
        dest_path = os.path.join(output_directory, file_name)

        if not os.path.exists(file_path):
            print(f"Source file not found: {file_path}")
            return

        os.makedirs(output_directory, exist_ok=True)

        if not os.path.exists(dest_path):
            #shutil.copy(file_path, dest_path)
            Procedure.__copy_parents(file_path,dest_path)
            copied_files.add(file_path)

        includes = all_includes.get(file_path, [])
        for include in includes:
            if include not in copied_files:
                Procedure.copy_file_and_includes(include, output_directory, copied_files, all_includes)
 
    @staticmethod
    def get_includes_obj(procedures, scan_directory):
        proc_dict = {procedure.file_path.lower(): procedure for procedure in procedures} 
        #print(proc_dict)   
        include_regex = re.compile(r"^(?!\s*-?\s*-\*)\s*-?\s*INCLUDE\s*(?:=\s*)?(?:[A-Za-z]+:)?([\/\.\w]+\.fex)", re.IGNORECASE)
        for procedure in procedures:
            lines = _read_file_lines(procedure.file_path)

            for line in lines:
                line = line.strip()

                include_match = include_regex.search(line)
                if include_match:
                    include_name = include_match.group(1)

                    if include_name.startswith(".") or "/" not in include_name:
                        include_name = os.path.normpath(os.path.join(os.path.dirname(procedure.file_path), include_name))
                    else:
                        include_name = f"{scan_directory}/{include_name}"
                        include_name = os.path.normpath(include_name)
                    #print(include_name)
                    if include_name.lower() in proc_dict:
                        procedure.add_include(proc_dict[include_name.lower()])
                    else:
                        print(f"{procedure.filename} : Include not found for {include_name}")    
                    #found_includes.append(include_name)
    @staticmethod
    def get_includes(scan_directory):
        include_dictionary = {}

        include_regex = re.compile(r"^(?!\s*-?\s*-\*)\s*-?\s*INCLUDE\s*(?:=\s*)?(?:[A-Za-z]+:)?([\/\.\w]+\.fex)", re.IGNORECASE)

        for root, dirs, files in os.walk(scan_directory):
            for file in files:
                if file.endswith('.fex'):    
                    procedure_path = os.path.normpath(os.path.join(root, file))
                    found_includes = []

                    lines = _read_file_lines(procedure_path)

                    for line in lines:
                        line = line.strip()

                        include_match = include_regex.search(line)
                        if include_match:
                            include_name = include_match.group(1)

                            if include_name.startswith("."):
                                include_name = os.path.normpath(os.path.join(root, include_name))
                            else:
                                include_name = f"{scan_directory}/{include_name}"
                                include_name = os.path.normpath(include_name)
                            #print(include_name)
                            found_includes.append(include_name)



                    if found_includes and procedure_path not in include_dictionary:
                        include_dictionary[procedure_path] = found_includes
                    elif found_includes and procedure_path in include_dictionary:
                        print(f"Key {procedure_path} already exists in dictionary appending includes")
                        for include in found_includes:
                            if include not in include_dictionary[procedure_path]:
                                include_dictionary[procedure_path].append(include)


        return include_dictionary

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
    def copy_all_procs(procedures, output_directory):
        for procedure in procedures:
            Procedure.__copy_parents(procedure.file_path,output_directory)
            for master in procedure.masters:
                Procedure.__copy_parents(master.path,output_directory)
                for proc in master.created_by_proc:
                    Procedure.__copy_parents(proc.file_path,output_directory)


    def copy_related_files(procedures, output_directory, copied_files=None):
        if copied_files is None:
            copied_files = set()

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        for procedure in procedures:
            if procedure.file_path not in copied_files:
                Procedure.__copy_parents(procedure.file_path,output_directory)
                #Procedure._copy_masters(procedure, output_directory, copied_files)
                #shutil.copy(procedure.file_path, os.path.join(output_dir, procedure.filename))
                copied_files.add(procedure.file_path)

            if procedure.includes:
                Procedure.copy_related_files(procedure.includes, output_directory, copied_files)

            for master in procedure.masters:
                if master.path not in copied_files:
                    Procedure.__copy_parents(master.path,output_directory)
                    #shutil.copy(master.file_path, os.path.join(output_dir, master.filename))
                    copied_files.add(master.path)

                Procedure.copy_related_files(master.created_by_proc, output_directory, copied_files)
                #Procedure.copy_related_files(master.masters, output_directory, copied_files)
                   
    
    def __copy_parents(src, dest_folder, dir_offset=8):
        prev_offset = 0 if dir_offset == 0 else src.replace('/', '%', dir_offset - 1).find('/') + 1
        post_offset = src.rfind('/')

        src_dirs = '' if post_offset == -1 else src[prev_offset:post_offset]
        src_filename = src[post_offset + 1:]

        os.makedirs(f'{dest_folder}/{src_dirs}', exist_ok=True)
        shutil.copy(src, f'{dest_folder}/{src_dirs}/{src_filename}')  
    
