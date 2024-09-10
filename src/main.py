import os
from wf_object import Master
from wf_object import Procedure
from report import Report
from typing import List

if __name__ == "__main__":
    scan_directory = os.path.normpath("../OD/CM/Ops")
    output_directory = os.path.normpath("../output")
    inventory_file = os.path.normpath("../inventory.csv")

    masters: List[Master] = Master.get_masters(scan_directory)
    print(f"Number of Masters found: {len(masters)}")

    procedures: List[Procedure] = Procedure.get_procedures(scan_directory, masters)
    print(f"Number of Procedures found: {len(procedures)}")

    master_path_dict = {str(master.file_path).lower(): master for master in masters}
    procedure_path_dict = {str(procedure.file_path).lower(): procedure for procedure in procedures}
    master_name_dict = {master.name.lower(): master for master in masters}  