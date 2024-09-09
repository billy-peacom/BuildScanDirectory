import os
import shutil
import re
import csv
from utils import _read_file_lines
from master import Master

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
        and checks if they match any Master filenames.
        """
        procedures = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.fex'):    
                    procedure = Procedure._process_fex_file(root, file, directory, masters, all_includes)
                    procedures.append(procedure)
        return procedures

    @staticmethod
    def _process_fex_file(root, file, directory, masters, all_includes):
        file_path = os.path.normpath(os.path.join(root, file))
        search_path = Procedure._build_search_path(file_path, directory)
        includes_key, includes = Procedure._get_includes_key(search_path, all_includes)
        procedure = Procedure(file_path=file_path, includes=includes, includes_key=includes_key)
        lines = _read_file_lines(file_path)
        for line in lines:
            if "graph file" in line or "table file" in line or "define file" in line:
                table_name = line.split()[-1].strip().lower()
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
    def copy_used_masters(output_directory, procedures, all_includes):
        """
        Copies all Master files associated with any Procedure, including dependencies,
        to the specified output directory.
        """
        os.makedirs(output_directory, exist_ok=True)
        copied_files = set()

        for procedure in procedures:
            Procedure._copy_includes(procedure, all_includes, output_directory, copied_files)
            Procedure._copy_masters(procedure, output_directory, copied_files)

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

        if not os.path.exists(dest_path):
            shutil.copy(file_path, dest_path)
            copied_files.add(file_path)

        includes = all_includes.get(file_path, [])
        for include in includes:
            if include not in copied_files:
                Procedure.copy_file_and_includes(include, output_directory, copied_files, all_includes)

    @staticmethod
    def get_includes(scan_directory):
        include_dictionary = {}

        include_regex = re.compile(r"^(?!\s*-?\s*-\*)\s*-?\s*INCLUDE\s*(?:=\s*)?(?:[A-Za-z]+:)?([\/\.\w]+\.fex)", re.IGNORECASE)

        for root, dirs, files in os.walk(scan_directory):
            for file in files:
                if file.lower().endswith('.fex'):    
                    procedure_path = os.path.normpath(os.path.join(root, file))
                    found_includes = []

                    lines = _read_file_lines(procedure_path)

                    for line in lines:
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