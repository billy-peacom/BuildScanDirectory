import os
import re
from utils import _read_file_lines

class Master:
    def __init__(self, path, filename, created_by=None):
        self.path = os.path.normpath(path)
        self.filename = filename   
        self.created_by = created_by
        self.dependencies = []    
        self.created_by_proc = []

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
                if file.endswith('.mas'):    
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
        master_dict = {master.filename: master for master in masters}    

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
            if dependent_filename in master_dict:
                master.add_dependency(master_dict[dependent_filename])
            else:
                print(f"Dependency file {dependent_filename} not in master {master.filename} dict")

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
        hold_table_data = []

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.fex'):    
                    file_path = os.path.join(root, file)
                    
                    lines = _read_file_lines(file_path)
                    for line in lines:
                        hold_match = hold_regex.search(line)
                        if hold_match:
                            hold_name = hold_match.group(2)
                            hold_table_data.append((file_path, hold_name))
    
        return hold_table_data


    @staticmethod
    def _match_master_to_hold(hold_name, masters, procedure):
        for master in masters:
            if master.filename == hold_name:
                master.add_created_by_proc(procedure)
                break
