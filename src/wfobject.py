import os
import shutil
import re
import csv
from utils import _read_file_lines
class Master:
    def __init__(self, path, filename, created_by=None):
        self.path = os.path.normpath(path)
        self.file_path = os.path.normpath(self.path)
        self.filename = filename     
        self.created_by = created_by
        self.dependencies = [] #Of type master  (self)   
        self.created_by_proc = [] #of type procedure
        pre, ext = os.path.splitext(self.path)
        self.access_path = pre + ".acx"
        self.obj_url = None
    def update_obj_url(self, obj_url):
        self.obj_url = obj_url
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
        filenames = set()
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.mas'):    
                    file_path = os.path.join(root, file)
                    lines = _read_file_lines(file_path)
                    for line in lines:
                        filename = Master.extract_filename(line)
                        if filename and filename not in filenames:
                            master_obj = Master(path=file_path, filename=filename)   
                            masters.append(master_obj)
                            filenames.add(filename)
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
        app_hold_regex = re.compile(r"^\s*app\s+", re.IGNORECASE)
        master_dict = {master.filename.lower(): master for master in masters}    
        #procedure_dict = {procedure.file_path: procedure for procedure in procedures}
        for procedure in procedures:            
            lines = _read_file_lines(procedure.file_path)
            hold = False
            for line in lines:
                if app_hold_regex.search(line):
                    hold = True
                if hold:
                    hold_match = hold_regex.search(line)
                    if hold_match:
                        hold_name = hold_match.group(2)
                        if "/" in hold_name:
                            hold_name = hold_name.rsplit('/',1)[-1]
                        if hold_name.lower() in master_dict:
                            master_dict[hold_name.lower()].add_created_by_proc(procedure)
                            #print(f"{hold_name}: {procedure.filename}")
                            #procedure.update_type("ETL",hold_name.lower())
                        #print(master_dict[hold_name.lower()].path)
    
        #return hold_table_data

class Procedure:
    def __init__(self, file_path, includes=None, includes_key=None):
        self.file_path = os.path.normpath(file_path)  
        self.filename = os.path.basename(file_path)    
        self.includes = includes or [] #of type procedure
        self.masters = [] #Of type master
        self.includes_key = includes_key
        self.obj_url = None
        self.outputs = self.get_output_format()
        self.type = "Report Proc"
        self.created_master_name = None
        if not self.outputs:
            self.outputs = {"N/A"}
    def update_type(self, type, master_name = None):
        self.type = type
        if master_name:
            self.created_master_name = master_name
    def update_obj_url(self, obj_url):
        self.obj_url = obj_url
    def add_master(self, master):
        """
        Adds a Master object to the Procedure's list of masters.
        """
        if isinstance(master, Master) and master not in self.masters:
            self.masters.append(master)

    def add_include(self, include):
        if include not in self.includes:
            self.includes.append(include)
    def get_output_format(self):
        pattern = re.compile(r"\s+FORMAT\s+(\w*)", re.IGNORECASE)
        lines = _read_file_lines(self.file_path)
        myset = set()
        for line in lines:
            match = pattern.search(line)
            if match:
                """
                Web: 'html','ahtml','jschart','dhtml','htmtable', 'wp'
                Excel/csv: 'com','excel', 'exl07', 'exl2k', exl97', 'tab', 'tabt', 'comt', 'xlsx', 'lotus'
                pdf: 'pdf', 'apdf'
                powerpoint: 'ppt', 'pptx'
                json/xml: 'json', 'xml'
                image: 'svg', 'jpeg', 'gif', 'png'"""
                if match[1] in ['html','ahtml','jschart','dhtml','htmtable', 'wp']:
                    myset.add("Web")
                elif match[1] in ['com','excel', 'exl07', 'exl2k', 'exl97', 'tab', 'tabt', 'comt', 'xlsx', 'lotus']:
                    myset.add("Excel/CSV")
                elif match[1] in ['pdf', 'apdf']:
                    myset.add("PDF")
                elif match[1] in ['ppt', 'pptx']:
                    myset.add("PowerPoint")
                elif match[1] in ['json', 'xml']:
                    myset.add("JSON/XML")
                elif match[1] in ['svg', 'jpeg', 'gif', 'png']:
                    myset.add("Image")
                #myset.add(match[1])
        return myset
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

                      
                    lines = _read_file_lines(file_path)
                    for line in lines:
                        line_lower = line.strip().lower()  
                        if re.search(pattern, line_lower):  
                                
                            table_name = line.split()[-1].strip().lower()
                                
                            for master in masters:
                                if master.filename.lower() == table_name:
                                    #print(f"{table_name}: {procedure.filename}")
                                    procedure.add_master(master)
                                    break    

                    procedures.append(procedure)

        return procedures
    
    @staticmethod
    def get_includes_obj(procedures, scan_directory):
        proc_dict = {procedure.file_path.lower(): procedure for procedure in procedures} 
        #print(proc_dict)   
        include_regex = re.compile(r"^(?!\s*-?\s*-\*)\s*-?\s*(INCLUDE|EX)\s*(?:=\s*)?(?:[A-Za-z]+:)?([\/\.\w]+\.fex)", re.IGNORECASE)
        for procedure in procedures:
            lines = _read_file_lines(procedure.file_path)

            for line in lines:
                line = line.strip()

                include_match = include_regex.search(line)
                if include_match:
                    include_name = include_match.group(2)
                    
                    if include_name.startswith(".") or "/" not in include_name:
                        include_name = os.path.normpath(os.path.join(os.path.dirname(procedure.file_path), include_name))
                    else:
                        include_name = f"{scan_directory}/{include_name}"
                        include_name = os.path.normpath(include_name)
                    #print(f"{line} : {include_name}")
                    if include_name.lower() in proc_dict:
                        procedure.add_include(proc_dict[include_name.lower()])
                    
                    #print(f"{procedure.filename} : Include not found for {include_name}")    
                    #found_includes.append(include_name)
    
                   
    def copy_related_objects_recurse(wfObjects, output_directory, copied_files=None):
        if copied_files is None:
            copied_files = set()
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        for wfObject in wfObjects:
            if wfObject.file_path not in copied_files:
                Procedure.__copy_parents(wfObject.file_path,output_directory)
                copied_files.add(wfObject.file_path)   
                if isinstance(wfObject,Master):
                    try:
                        Procedure.__copy_parents(wfObject.access_path, output_directory)
                    except:
                        pass
                    Procedure.copy_related_objects_recurse(wfObject.created_by_proc, output_directory, copied_files)
                    Procedure.copy_related_objects_recurse(wfObject.dependencies, output_directory, copied_files)
                elif isinstance(wfObject, Procedure):
                    Procedure.copy_related_objects_recurse(wfObject.includes, output_directory, copied_files)
                    Procedure.copy_related_objects_recurse(wfObject.masters,output_directory, copied_files)
        
    def __copy_parents(src, dest_folder, dir_offset=10):
        parent_folder = os.path.basename(dest_folder)
        
        prev_offset = 0 if dir_offset == 0 else src.replace('/', '%', dir_offset - 1).find('/') + 1
        post_offset = src.rfind('/')
        src_dirs = '' if post_offset == -1 else src[prev_offset:post_offset]
        src_filename = src[post_offset + 1:]

        os.makedirs(f'{dest_folder}/{src_dirs}', exist_ok=True)
        shutil.copy(src, f'{dest_folder}/{src_dirs}/{src_filename}')  
        return f'{parent_folder}/{dest_folder}/{src_dirs}/{src_filename}'
    
    def copy_related_objects_iterative(wfObjects, output_directory):
        copied_files = set()
        to_copy = list(wfObjects)  

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        while to_copy:
            wfObject = to_copy.pop(0) 

            if wfObject.file_path not in copied_files:
                objurl = Procedure.__copy_parents(wfObject.file_path, output_directory)[len(output_directory):]
                wfObject.update_obj_url(objurl)
                copied_files.add(wfObject.file_path)      
                if isinstance(wfObject, Master):
                    try:
                        Procedure.__copy_parents(wfObject.access_path, output_directory)
                    except:
                        pass
                    copied_files.add(wfObject.access_path) 
                    to_copy.extend(wfObject.created_by_proc)
                    to_copy.extend(wfObject.dependencies)
                elif isinstance(wfObject, Procedure):
                    to_copy.extend(wfObject.includes)
                    to_copy.extend(wfObject.masters)
    def report_proc_output(reports, csv_file_path):

        with open(csv_file_path, mode='w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Report Name', 'Object URL', 'Include Type', 'group_id', 'is duplicate', 'report_output_fmt', 'ac_report_type'])
            for report in reports:
                to_add = [(proc, 'N') for proc in report.procedures]  
                procs_added = set()
                while to_add:
                    wfObject, is_etl = to_add.pop(0)
                    if wfObject.file_path not in procs_added:
                        procs_added.add(wfObject.file_path)

                        if isinstance(wfObject, Master):
                            to_add.extend([(dep, 'Y') for dep in wfObject.created_by_proc])
                            to_add.extend([(dep, 'N') for dep in wfObject.dependencies])
                        elif isinstance(wfObject, Procedure):
                            csv_writer.writerow([report.report_name, wfObject.obj_url, is_etl,report.group_id ,report.is_duplicate, report.output_format, report.ac_type])
                            to_add.extend([(inc, 'N') for inc in wfObject.includes])
                            to_add.extend([(mast, 'N') for mast in wfObject.masters])
    
    def master_proc_output(reports, csv_file_path):

        with open(csv_file_path, mode='w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Master Name', 'created by proc OBJURL'])
            procs_added = set()
            masters = set()
            for report in reports:
                to_add = [(proc, 'N', 'None') for proc in report.procedures]  
                while to_add:
                    wfObject, is_etl, master_name = to_add.pop(0)
                    if wfObject.file_path not in procs_added:
                        procs_added.add(wfObject.file_path)

                        if isinstance(wfObject, Master):
                            masters.add(wfObject)
                            to_add.extend([(dep, 'Y', wfObject.filename) for dep in wfObject.created_by_proc])
                            to_add.extend([(dep, 'N', 'None') for dep in wfObject.dependencies])
                        elif isinstance(wfObject, Procedure):
                            #if wfObject.type == 'ETL':
                            #    csv_writer.writerow([wfObject.created_master_name, wfObject.obj_url])    
                            to_add.extend([(mast, 'N', 'None') for mast in wfObject.masters])
                            to_add.extend([(inc, 'N', 'None') for inc in wfObject.includes])
            for master in masters:
                for proc in master.created_by_proc:
                    csv_writer.writerow([master.filename, proc.obj_url])

    def proc_fmt_output(reports, csv_file_path):
        with open(csv_file_path, mode='w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['obj_url', 'output format'])
            procs_added = set()
            for report in reports:
                to_add = [(proc) for proc in report.procedures]  
                
                while to_add:
                    wfObject = to_add.pop(0)
                    if wfObject.file_path not in procs_added:
                        procs_added.add(wfObject.file_path)

                        if isinstance(wfObject, Master):
                            to_add.extend([(dep) for dep in wfObject.created_by_proc])
                            to_add.extend([(dep) for dep in wfObject.dependencies])
                        elif isinstance(wfObject, Procedure):
                            for output in wfObject.outputs:
                                csv_writer.writerow([wfObject.obj_url, output])
                            to_add.extend([(inc) for inc in wfObject.includes])
                            to_add.extend([(mast) for mast in wfObject.masters])
                            
    def report_proc_master_output(reports, csv_file_path):
        def process_procedure(proc, csv_writer, visited):
            if proc.file_path in visited:
                return
            visited.add(proc.file_path)

            # Write masters associated with the procedure
            for master in proc.masters:
                csv_writer.writerow([proc.filename, proc.obj_url, master.filename, master.obj_url])

            # Recursively process dependencies (which are procedures)
            for dep_proc in proc.includes:
                process_procedure(dep_proc, csv_writer, visited)

        # Open the CSV file and write headers
        with open(csv_file_path, mode='w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Procedure Name', 'Procedure Path', 'Master Name', 'Master Path'])

            visited = set()  # Track visited procedures to avoid infinite recursion
            for report in reports:
                for proc in report.procedures:
                    process_procedure(proc, csv_writer, visited)
    
        
            