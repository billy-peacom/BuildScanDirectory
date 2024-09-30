import os
import shutil
import re
import csv
import pygraphviz as pgv
from collections import defaultdict
from wfobject import Master
from wfobject import Procedure
from report import Report
import networkx as nx
from networkx.drawing.nx_agraph import from_agraph

debug = False
class VizBuilder:
    
    def save_disconnected_subgraphs_as_svg(graph, output_dir, ignore_list=None, only_interdependent=False, output_csv=None):
        os.makedirs(output_dir, exist_ok=True)
        
        if ignore_list:
            graph = graph.copy()
            graph.remove_nodes_from(ignore_list)
        
        subgraphs = list(nx.weakly_connected_components(graph))
        csv_data = []
        group_id = 0
        for i, component in enumerate(subgraphs):
            subgraph = graph.subgraph(component).copy()
            end_nodes = [node for node in subgraph.nodes() if subgraph.out_degree(node) == 0]
            
            if only_interdependent:
                if len(end_nodes) == 1:
                    continue
            
            group_id +=1
            
            for node in end_nodes:
                csv_data.append({'Artifact Group ID': node, 'Interdependency Group ID': group_id})
            
            agraph = nx.nx_agraph.to_agraph(subgraph)
            output_path = f"{output_dir}/subgraph_{group_id}.svg"
            agraph.layout(prog="dot")
            agraph.draw(output_path)

        if output_csv:
            with open(output_csv, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=['Artifact Group ID', 'Interdependency Group ID'])
                writer.writeheader()
                writer.writerows(csv_data)
            
            print(f"CSV saved to {output_csv}")

        print(f"Saved {len(subgraphs)} disconnected subgraphs as SVG files.")
        
    @staticmethod
    def analyze_graph(nxg, output_csv, ignore_nodes=None):
        if ignore_nodes is None:
            ignore_nodes = ['common_dates_ibi.fex', 'utility_functions.fex', 'wor02_01_parameters.fex']

        
        end_nodes = [node for node in nxg.nodes if nxg.out_degree(node) == 0 and node not in ignore_nodes]

        
        dependency_trees = {}
        for node in end_nodes:
            tree = nx.ancestors(nxg, node)  
            tree.add(node)  
            tree_nodes = frozenset(n for n in tree if n not in ignore_nodes)
            if tree_nodes not in dependency_trees:
                dependency_trees[tree_nodes] = []
            dependency_trees[tree_nodes].append(node)

        
        group1 = []  
        group2 = []  
        all_seen_nodes = set()  

        for tree_nodes, reports in dependency_trees.items():
            
            if all_seen_nodes.isdisjoint(tree_nodes):
                group1.extend(reports)  
            else:
                group2.extend(reports)  
            all_seen_nodes.update(tree_nodes)  

        
        with open(output_csv, mode='w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Artifact Group ID', 'grouping'])
            for report in group1:
                csv_writer.writerow([report, 'Standalone'])
            for report in group2:
                csv_writer.writerow([report, 'Interdependent'])

        print(f"Report grouping written to {output_csv}")
    
    def label_interdependent_graphs(reports, csv_file_path, exclusion_list=None):
        if exclusion_list is None:
            exclusion_list = ['common_dates_ibi.fex','utility_functions.fex','wor02_01_parameters.fex']

        graphs = VizBuilder.generate_work_graphs(reports)
        labels = ['standalone' for _ in range(len(graphs))]
        results = []
        seen_groups = set()

        def get_end_node(graph):
            end_nodes = [node for node in graph.nodes if graph.out_degree(node) == 0]
            return end_nodes[0] if end_nodes else None

        for i in range(len(graphs)):
            graph_name = get_end_node(graphs[i])
            if graph_name is None or graph_name in seen_groups:
                continue
            
            for j in range(i + 1, len(graphs)):
                nodes_i = set(graphs[i].nodes()) - set(exclusion_list)
                nodes_j = set(graphs[j].nodes()) - set(exclusion_list)
                if nodes_i.intersection(nodes_j):
                    labels[i] = 'interdependent'
                    labels[j] = 'interdependent'
                    seen_groups.add(graph_name)  
            
            results.append((graph_name, labels[i]))

        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Report Group ID', 'Label'])
            writer.writerows(results)
    
    
    def generate_work_graphs(reports):
        graphs = []
        seen_groups = set()
        for report in reports:
            if report.group_id in seen_groups:
                continue
            else:
                seen_groups.add(report.group_id)
            
            #os.makedirs(output_directory, exist_ok=True)
            G = pgv.AGraph(directed=True)
            G.graph_attr.update(Gsize='10', Gratio='1.4', overlap='false', rankdir='LR')

            #VizBuilder.graph_related_objects_dfs(report.procedures, G, report.report_name, 'white', 'bottom', 'Used by')
            VizBuilder.graph_related_objects_recurse(report.procedures,G, parent=report.group_id, color='lightgreen', group='bottom', label='Component of Report' )
            #valid_report_name = re.sub(r'[<>:"/\\|?*]', '_', report.report_name)
            #output_image = os.path.join(output_directory, f"{valid_report_name}_dependency.svg")
            G.layout(prog='dot')
            graphs.append(nx.DiGraph(nx.drawing.nx_agraph.from_agraph(G)))
            #if debug:
            #    print(f"Generating report graph: {report.report_name}")
            
            #try:
            #    G.draw(output_image)
            #except:
            #    print(f"Could not draw report image for: {valid_report_name}")
        return graphs
    
    def generate_all_work_graph(reports, output_directory=None):
        os.makedirs(output_directory, exist_ok=True)
        G = pgv.AGraph(directed=True)
        G.graph_attr.update(Gsize='10', Gratio='1.4', overlap='false', rankdir='LR')
        for report in reports:
            VizBuilder.graph_related_objects_recurse(report.procedures,G, parent=report.group_id, color='lightgreen', group='bottom', label='Component of Report' )
            
        output_image = os.path.join(output_directory, f"All_Work_dependency.svg")
        G.layout(prog='dot')    
        G.draw(output_image)
        return G
    
    def generate_all_reports_graph(reports, output_directory=None):
        os.makedirs(output_directory, exist_ok=True)
        G = pgv.AGraph(directed=True)
        G.graph_attr.update(Gsize='10', Gratio='1.4', overlap='false', rankdir='LR')
        for report in reports:
            VizBuilder.graph_related_objects_recurse(report.procedures,G, parent=report.report_name, color='lightgreen', group='bottom', label='Component of Report' )
            
        output_image = os.path.join(output_directory, f"All_Report_dependency.svg")
        G.layout(prog='dot')    
        G.draw(output_image)
        return G
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
            if debug:
                print(f"Generating report graph: {report.report_name}")
            
            try:
                G.draw(output_image)
            except:
                print(f"Could not draw report image for: {valid_report_name}")
                      
    def generate_report_dot(reports, output_directory=None):
        
        for report in reports:
            os.makedirs(output_directory, exist_ok=True)
            G = pgv.AGraph(directed=True)
            G.graph_attr.update(Gsize='10', Gratio='1.4', overlap='false', rankdir='LR')
            
            #VizBuilder.graph_related_objects_dfs(report.procedures, G, report.report_name, 'white', 'bottom', 'Used by')
            VizBuilder.graph_related_objects_recurse(report.procedures,G, parent=report.report_name, color='lightgreen', group='bottom', label='Component of Report' )
            valid_report_name = re.sub(r'[<>:"/\\|?*]', '_', report.report_name)
            output_image = os.path.join(output_directory, f"{valid_report_name}_dependency.dot")
            G.layout(prog='dot')
            
            
            try:
                #G.draw(output_image).format(grandparent=os.path.dirname(os.path.dirname(__file__)),name=valid_report_name)
                G.write(output_image)
            except:
                print(f"Could not draw report dot for: {valid_report_name}")
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
                G.draw(output_image)
            except:
                print(f"Could not draw master image for: {master_name}")
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
                G.draw(output_image)
            except:
                print(f"Could not draw procedure image for: {procedure_name}")
    def graph_related_objects_recurse(wfObjects,graph, accessed=None, parent=None, color=None, group=None, label=None, edge_color=None):
        if accessed is None:
            accessed = set()
        for wfObject in wfObjects:
            if wfObject.file_path not in accessed:
                graph.add_node(wfObject.filename, label=wfObject.filename,shape='box', style='filled', fillcolor=color )
                if debug:
                    print(f"Node Created {wfObject.filename}")
            
                accessed.add(wfObject.file_path)   
                if isinstance(wfObject,Master):
                    if debug:
                        print(f"Adding master: {wfObject.filename}")
                    if wfObject.created_by_proc:
                        VizBuilder.graph_related_objects_recurse(wfObject.created_by_proc, graph, accessed, wfObject.filename, color='lightblue', label='created', edge_color='darkblue' )
                        if debug:
                            print(f"Adding created by proc for: {wfObject.filename}")
                    else:
                        if debug:
                            print(f"No created by proc for {wfObject.filename}")
                    VizBuilder.graph_related_objects_recurse(wfObject.dependencies, graph, accessed, wfObject.filename, color='orange',  label='segment of', edge_color='orange')
                elif isinstance(wfObject, Procedure):
                    VizBuilder.graph_related_objects_recurse(wfObject.includes, graph, accessed, wfObject.filename, color='lightgreen',  label='included in' , edge_color='darkgreen')
                    VizBuilder.graph_related_objects_recurse(wfObject.masters, graph, accessed, wfObject.filename, color='yellow',  label='used in', edge_color='red')  
            if(parent):
                    graph.add_edge(wfObject.filename, parent, label=label, color='black')
                    if debug:
                        print(f"Adding edge from {parent} to {wfObject.filename} and label= {label}") 
      
                  
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