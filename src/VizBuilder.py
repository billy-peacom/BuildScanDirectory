import os
import shutil
import re
import csv
import pygraphviz as pgv
from collections import defaultdict
from wfobject import Master
from wfobject import Procedure
from report import Report


class VizBuilder:

    
    def generate_report_graph(reports, output_directory=None):
        
        for report in reports:
            os.makedirs(output_directory, exist_ok=True)
            G = pgv.AGraph(directed=True)
            G.graph_attr.update(Gsize='10', Gratio='1.4', overlap='false', rankdir='LR')
            
            #VizBuilder.graph_related_objects_dfs(report.procedures, G, report.report_name, 'white', 'bottom', 'Used by')
            VizBuilder.graph_related_objects_recurse(report.procedures,G, parent=report.report_name, color='lightgreen', group='bottom', label='Component of Report' )
            valid_report_name = re.sub(r'[<>:"/\\|?*]', '_', report.report_name)
            output_image = os.path.join(output_directory, f"{valid_report_name}_dependency.svg")
            G.layout(prog='dot')
            
            
            try:
                G.draw(output_image).format(grandparent=os.path.dirname(os.path.dirname(__file__)),name=valid_report_name)
            except:
                pass
    def get_all_masters(reports):
        procs_added = set()
        masters = set()
        for report in reports:
            to_add = [(proc) for proc in report.procedures]  
            
            while to_add:
                wfObject = to_add.pop(0)
                if wfObject.file_path not in procs_added:
                    procs_added.add(wfObject.file_path)

                    if isinstance(wfObject, Master):
                        masters.add(wfObject)
                        to_add.extend(wfObject.created_by_proc)
                        to_add.extend(wfObject.dependencies)
                    elif isinstance(wfObject, Procedure):
                        to_add.extend(wfObject.includes)
                        to_add.extend(wfObject.masters)
        return masters
    def get_all_procedures(reports):
        procs_added = set()
        procedures = set()
        for report in reports:
            to_add = [(proc) for proc in report.procedures]  
            
            while to_add:
                wfObject = to_add.pop(0)
                if wfObject.file_path not in procs_added:
                    procs_added.add(wfObject.file_path)

                    if isinstance(wfObject, Master):
                        to_add.extend(wfObject.created_by_proc)
                        to_add.extend(wfObject.dependencies)
                    elif isinstance(wfObject, Procedure):
                        procedures.add(wfObject)
                        to_add.extend(wfObject.includes)
                        to_add.extend(wfObject.masters)
        return procedures
    def generate_master_graph(reports, output_directory=None):
        masters = VizBuilder.get_all_masters(reports)
        
        for master in masters:
            master_list = [master]
            os.makedirs(output_directory, exist_ok=True)
            G = pgv.AGraph(directed=True)
            G.graph_attr.update(Gsize='10', Gratio='1.4', overlap='false', rankdir='LR')
            #VizBuilder.graph_related_objects_dfs(report.procedures, G, report.report_name, 'white', 'bottom', 'Used by')
            VizBuilder.graph_related_objects_recurse(master_list,G, parent=None, color='yellow', label=None )
            master_name = re.sub(r'[<>:"/\\|?*]', '_', master.filename)
            output_image = os.path.join(output_directory, f"{master_name}_dependency.svg")
            G.layout(prog='dot')
            
            
            try:
                G.draw(output_image).format(grandparent=os.path.dirname(os.path.dirname(__file__)),name=master_name)
            except:
                pass
    def generate_procedure_graph(reports, output_directory=None):
        procedures = VizBuilder.get_all_procedures(reports)
        
        for procedure in procedures:
            procedure_list = [procedure]
            os.makedirs(output_directory, exist_ok=True)
            G = pgv.AGraph(directed=True)
            G.graph_attr.update(Gsize='10', Gratio='1.4', overlap='false', rankdir='LR')
            #VizBuilder.graph_related_objects_dfs(report.procedures, G, report.report_name, 'white', 'bottom', 'Used by')
            VizBuilder.graph_related_objects_recurse(procedure_list,G, parent=None, color='lightgreen', label=None )
            procedure_name = re.sub(r'[<>:"/\\|?*]', '_', procedure.filename)
            output_image = os.path.join(output_directory, f"{procedure_name}_dependency.svg")
            G.layout(prog='dot')
            
            
            try:
                G.draw(output_image).format(grandparent=os.path.dirname(os.path.dirname(__file__)),name=master_name)
            except:
                pass
    def graph_related_objects_recurse(wfObjects,graph, accessed=None, parent=None, color=None, group=None, label=None, edge_color=None):
        if accessed is None:
            accessed = set()
        for wfObject in wfObjects:
            if wfObject.file_path not in accessed:
                graph.add_node(wfObject.filename, label=wfObject.filename,shape='box', style='filled', fillcolor=color )
                
            
                accessed.add(wfObject.file_path)   
                if isinstance(wfObject,Master):
                    VizBuilder.graph_related_objects_recurse(wfObject.created_by_proc, graph, accessed, wfObject.filename, color='lightblue', label='created', edge_color='darkblue' )
                    VizBuilder.graph_related_objects_recurse(wfObject.dependencies, graph, accessed, wfObject.filename, color='orange',  label='segment of', edge_color='orange')
                elif isinstance(wfObject, Procedure):
                    VizBuilder.graph_related_objects_recurse(wfObject.includes, graph, accessed, wfObject.filename, color='lightgreen',  label='included in' , edge_color='darkgreen')
                    VizBuilder.graph_related_objects_recurse(wfObject.masters, graph, accessed, wfObject.filename, color='yellow',  label='used in', edge_color='red')  
            if(parent):
                    graph.add_edge(wfObject.filename, parent, label=label, color='black')
                              
    """@staticmethod
    def create_single_master_image(master, output_dir='master_dependency_images'):
        
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
    def create_single_report_image(report, output_dir='../report_dependency_images'):
        
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
        
        # Loop through each master and create a separate image
        for master in masters:
            MasterCentricVisualization.create_single_master_image(master, output_dir)
    def load_report_mapping(report_mapping_file):
        
        report_mapping = {}
        with open(report_mapping_file, mode='r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) == 2:
                    report_name, procedure_path = row
                    if procedure_path not in report_mapping:
                        report_mapping[procedure_path] = []
                    report_mapping[procedure_path].append(report_name)
        return report_mapping"""