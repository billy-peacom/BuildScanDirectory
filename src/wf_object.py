from utils import is_absolute_and_valid_path, read_file_lines, walk_directory, log_master_error, log_procedure_error, ErrorCode
from pathlib import Path
from typing import List
import re
import os

class Master:
    def __init__(self, file_path: str, name: str) -> None:
        file_path = Path(file_path)  

        self.file_path: Path = file_path or '' # Full file path from scan directory
        self.object_url: str = None # base path without the scan directory
        self.output_path: str = '' # remove all up to and including scan, prepend output dir
        self.access_file_path: Path = file_path.with_suffix('.acx') if file_path else '' # full file path to acx file
        self.name: str = name # maps to filename= 
        self.included_masters: List['Master'] = [] # [Master]
        self.created_by_procs: List['Procedure'] = []# [Procedure]

    def add_created_by_proc(self, procedure):
        """
        Adds the name of the procedure that created this master to the created_by_proc list.
        """
        if procedure.file_name not in self.created_by_procs:
            self.created_by_procs.append(procedure)

    def get_obj_url(self, scan_directory):
        if self.object_url:
            return self.object_url

        full_path = self.file_path
        scan_directory = Path(scan_directory).resolve()

        try:
            relative_path = full_path.relative_to(scan_directory)
            self.object_url = str(relative_path)
            return self.object_url
        except ValueError:
            log_master_error(self.file_path, ErrorCode.SCAN_DIR_NOT_IN_PATH, scan_directory)
            return str(full_path) 
        
    def get_output_dir(self,scan_directory, output_directory):
        if self.output_path:
            return self.output_path

        full_path = self.file_path
        scan_directory = Path(scan_directory).resolve()
        output_directory = Path(output_directory).resolve()

        try:
            relative_path = full_path.relative_to(scan_directory)

            output_path = output_directory / relative_path

            self.output_path = str(output_path)
            return str(self.output_path)
        except ValueError:
            log_master_error(self.file_path, ErrorCode.SCAN_DIR_NOT_IN_PATH, scan_directory)
            return str(full_path)


    @staticmethod
    def get_masters(directory: str) -> List['Master']:
        masters: List['Master'] = []
        file_paths = walk_directory(directory, '.mas')

        for file_path in file_paths:
            master: Master = Master._process_master(file_path)
            if master is not None:
                masters.append(master)

        return masters
    
    @staticmethod
    def _process_master(file_path: str) -> 'Master':
        lines: List['str'] = read_file_lines(file_path)

        for line in lines:
            filename = Master._extract_filename(line)
            if filename and is_absolute_and_valid_path(file_path):
                return Master(file_path=file_path, name=filename)
        return None

    
    @staticmethod
    def _extract_filename(line):
        pattern = re.compile(r'^filename\s*=\s*([^,\s]+)', re.IGNORECASE)
        match = pattern.search(line)
        
        if match:
            return match.group(1)
        return None
    
    def _extract_and_add_dependency(self, line: str, master_dict: dict):
        crfile_regex = re.compile(r'crfile\s*=\s*([^,\s]+)', re.IGNORECASE)

        match = crfile_regex.search(line)
        if match:
            crfile_path = match.group(1).strip()
            dependent_filename = Path(crfile_path).stem.lower()
            if dependent_filename in master_dict:
                self.add_dependency(master_dict[dependent_filename])
                return dependent_filename
            else:
                log_master_error(self.file_path, ErrorCode.DEPENDENCY_NOT_IN_DICT, crfile_path)
                return dependent_filename
            
        return None
    

    def add_dependency(self, master):
        """
        Adds a Master object as a dependency to this Master.
        """
        if isinstance(master, Master) and master not in self.included_masters:
            self.included_masters.append(master)

    def add_included_master(self, scan_directory, output_directory, master_name_dict):
        self.get_output_dir(scan_directory, output_directory)
        self.get_obj_url(scan_directory)
        lines = read_file_lines(self.file_path)
        for line in lines:
            self._extract_and_add_dependency(line, master_name_dict)


class Procedure:
    def __init__(self, file_path: str) -> None:
        file_path = Path(file_path)
        
        self.file_path: Path = file_path or ''# full file path from scan directory
        self.file_name: str = file_path.name if file_path else ''# filename.fex
        self.included_procedures: List[Procedure] = [] # [Procedure]
        self.dependent_masters: List[Master] = [] # [Master]

    @staticmethod
    def get_procedures(directory: str) -> List['Procedure']:
        procedures: List['Procedure'] = []
        file_paths = walk_directory(directory, '.fex')

        for file_path in file_paths:
            procedure = Procedure(file_path)
            procedures.append(procedure)

        return procedures
        
    @staticmethod
    def _extract_table_name(line: str) -> str:
        pattern = re.compile(r"^\s*(table|graph)\s+file\s+([^\s]+)", re.IGNORECASE)
        match = pattern.search(line)

        if match:
            return match.group(2).strip().lower()  
        return None
    

    def add_master(self, master: 'Master'):
        self.dependent_masters.append(master)

    def get_hold_tables(self, master_name_dict, added_file: str, not_added_file: str):
        hold_regex = re.compile(r"on\s+(table|graph)\s+hold\s+as\s+(\S+)", re.IGNORECASE)
        app_hold_regex = re.compile(r"^\s*app\s+", re.IGNORECASE)
        hold = False

        lines = read_file_lines(self.file_path)
        for line in lines:
            hold_match = hold_regex.search(line)
            if app_hold_regex.search(line):
                hold = True

            if hold and hold_match:
                hold_name = hold_match.group(2).lower()
                hold_name = hold_name.rsplit("/", 1)[-1]

                if '&' in hold_name:
                   log_procedure_error(self.file_path, ErrorCode.HOLD_NAME_PARAMETERIZED, hold_name)
                elif hold_name in master_name_dict:
                    master_name_dict[hold_name].add_created_by_proc(self)
                else:
                    log_procedure_error(self.file_path, ErrorCode.HOLD_NAME_NOT_FOUND, hold_name)

    def process_procedure(self, master_name_dict) -> None:        
        lines: List[str] = read_file_lines(self.file_path)

        for line in lines:
            table_name = self._extract_table_name(line)
            if table_name in master_name_dict:
                self.add_master(master_name_dict[table_name])


    def get_includes_obj(self, scan_directory, procedure_path_dict):
        include_regex = re.compile(r"^(?!\s*-?\s*-\*)\s*-?\s*(INCLUDE|EX)\s*(?:=\s*)?(?:[A-Za-z]+:)?([\/\.\w]+\.fex)", re.IGNORECASE)
        lines = read_file_lines(self.file_path)

        for line in lines:
            line = line.strip()

            include_match = include_regex.search(line)
            if include_match:
                include_name = include_match.group(2)

                if include_name.startswith(".") or "/" not in include_name:
                    include_name = os.path.normpath(os.path.join(os.path.dirname(self.file_path), include_name))
                else:
                    include_name = f"{scan_directory}/{include_name}"

                include_name_abs = os.path.abspath(include_name).lower()

                if include_name_abs.lower() in procedure_path_dict:
                    self.add_dependent_master(procedure_path_dict[include_name_abs.lower()])
                else:
                    log_procedure_error(self.file_path, ErrorCode.INCLUDE_NOT_FOUND, include_name_abs)
    
    def add_dependent_master(self, include):
        if include not in self.dependent_masters:
            self.dependent_masters.append(include)