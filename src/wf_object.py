from utils import is_valid_path, read_file_lines, walk_directory
from pathlib import Path
from typing import List
import re
class Master:
    def __init__(self, file_path: str, name: str) -> None:
        file_path = Path(file_path)  

        self.file_path: Path = file_path or '' # Full file path from scan directory
        self.access_file_path: Path = file_path.with_suffix('.acx') if file_path else '' # full file path to acx file
        self.name: str = name # maps to filename= 
        self.included_masters: List['Master'] = [] # [Master]
        self.created_by_procs: List['Procedure'] = []# [Procedure]

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
            if filename and is_valid_path(file_path):
                return Master(file_path=file_path, name=filename)
        return None

    
    @staticmethod
    def _extract_filename(line):
        pattern = re.compile(r'^filename\s*=\s*([^,\s]+)', re.IGNORECASE)
        match = pattern.search(line)
        
        if match:
            return match.group(1)
        return None


class Procedure:
    def __init__(self, file_path: str) -> None:
        if is_valid_path(file_path):
            file_path = Path(file_path)
        else:
            print(f'Procedure initalized with invalid path {file_path}')
            file_path = None
        
        self.file_path: Path = file_path or ''# full file path from scan directory
        self.file_name: str = file_path.name if file_path else ''# filename.fex
        self.included_procedures: List[Procedure] = [] # [Procedure]
        self.dependent_masters: List[Master] = [] # [Master]

    @staticmethod
    def get_procedures(directory: str, masters: List['Master']) -> List['Procedure']:
        procedures: List['Procedure'] = []
        file_paths = walk_directory(directory, '.fex')

        for file_path in file_paths:
            procedure = Procedure._process_procedure(file_path, masters)
            if procedure is not None:
                procedures.append(procedure)

        return procedures
    
    @staticmethod
    def _process_procedure(file_path: str, masters: List['Master']) -> 'Procedure':
        if is_valid_path(file_path):
            procedure = Procedure(file_path=file_path)
        else:
            return None
        
        lines: List[str] = read_file_lines(file_path)

        for line in lines:
            table_name = Procedure._extract_table_name(line)
            if table_name and is_valid_path(file_path):
                for master in masters:
                    if master.name == table_name:
                        procedure.add_master(master)
                        return procedure
        
        return procedure 

    @staticmethod
    def _extract_table_name(line: str) -> str:
        pattern = re.compile(r"^\s*(table|graph)\s+file\s+([^\s]+)", re.IGNORECASE)
        match = pattern.search(line)

        if match:
            return match.group(2).strip().lower()  
        return None
    

    def add_master(self, master: 'Master'):
        self.dependent_masters.append(master)