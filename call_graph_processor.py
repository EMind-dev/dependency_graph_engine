import os
import re
import pydot
from typing import Optional, List, Dict, Set, Tuple, Any

def process_dot_file(dot_file_path: str) -> Optional[str]:
    """
    Process a .dot file and generate a call graph image.
    
    Args:
        dot_file_path: Path to the .dot file
    
    Returns:
        Path to the generated PNG image
    """
    try:
        # Read the dot file
        graphs = pydot.graph_from_dot_file(dot_file_path)
        if not graphs:
            print(f"Error: No graphs found in {dot_file_path}")
            return None
            
        graph = graphs[0]
        
        # Set graph attributes for better visualization
        graph.set_bgcolor('white')
        graph.set_rankdir('LR')
        
        # Set node attributes
        for node in graph.get_nodes():
            node.set_style('filled')
            node.set_fillcolor('#E8F8F5')
            node.set_color('black')
            node.set_fontname('Arial')
        
        # Set edge attributes
        for edge in graph.get_edges():
            edge.set_color('#2471A3')
            edge.set_fontname('Arial')
        
        # Generate output filename - keeping the PNG in the same location as the .dot file
        output_path = os.path.splitext(dot_file_path)[0] + ".png"
        
        # Save the graph as PNG
        graph.write_png(output_path)
        print(f"Call graph generated: {output_path}")
        
        # Generate text file with function relationships - save in parent directory of dot_files if applicable
        generate_function_relationships_text(graph, dot_file_path)
        
        return output_path
    except Exception as e:
        print(f"Error processing dot file: {e}")
        return None

def extract_function_name(node_obj: pydot.Node) -> str:
    """
    Extracts the actual function name from a node object.
    
    Args:
        node_obj: A pydot Node object
    
    Returns:
        The extracted function name as a string
    """
    try:
        # Get the node name (typically the node ID)
        node_name = node_obj.get_name().strip('"')
        
        # Get the node label if it exists, which often contains the actual function name
        node_label = None
        if node_obj.get_label():
            node_label = node_obj.get_label().strip('"')
        
        # Extract function name from the label if available
        if node_label:
            # Remove Dot language line breaks (\l, \n, etc.) and everything after them
            # This handles cases like "external_signal_handler\l_adv_mode"
            if '\\l' in node_label:
                node_label = node_label.split('\\l')[0]
            if '\\n' in node_label:
                node_label = node_label.split('\\n')[0]
            
            # Handle HTML-like labels
            if '<' in node_label and '>' in node_label:
                # Try to extract from HTML-like label
                match = re.search(r'<[^>]*>([^<]+)</[^>]*>', node_label)
                if match:
                    return match.group(1)
            
            # Return the cleaned up label
            return node_label
        
        # If no usable label, try to clean up node name
        # Node names are often in format like "Node123" or have some prefix/suffix
        # Try to extract meaningful part using regex
        match = re.search(r'[a-zA-Z_][a-zA-Z0-9_]*', node_name)
        if match:
            return match.group(0)
            
        # Fall back to the node name if all else fails
        return node_name
    except Exception as e:
        print(f"Error extracting function name: {e}")
        return node_name  # Fall back to node name

def get_output_directory(dot_file_path: str) -> str:
    """
    Determine the appropriate output directory for relationship files.
    If the dot file is in a dot_files subdirectory, use the parent directory.
    
    Args:
        dot_file_path: Path to the .dot file
    
    Returns:
        Directory path where relationship files should be saved
    """
    dir_path = os.path.dirname(dot_file_path)
    dir_name = os.path.basename(dir_path)
    
    # If the file is in a dot_files subdirectory, move up one level
    if dir_name == "dot_files":
        return os.path.dirname(dir_path)
    
    # Otherwise, use the same directory
    return dir_path

def create_node_to_function_mapping(graph: pydot.Graph) -> Dict[str, str]:
    """
    Creates a mapping from node IDs to function names.
    
    Args:
        graph: The pydot Graph object
    
    Returns:
        Dictionary mapping node IDs to function names
    """
    node_to_function: Dict[str, str] = {}
    for node in graph.get_nodes():
        node_id = node.get_name().strip('"')
        function_name = extract_function_name(node)
        node_to_function[node_id] = function_name
    return node_to_function

def extract_relationships_from_edges(
    graph: pydot.Graph, 
    node_to_function: Dict[str, str], 
    is_icgraph: bool
) -> List[str]:
    """
    Extracts relationships from graph edges.
    
    Args:
        graph: The pydot Graph object
        node_to_function: Dictionary mapping node IDs to function names
        is_icgraph: Whether this is an inverse caller graph
    
    Returns:
        List of relationship strings
    """
    relationships: List[str] = []
    for edge in graph.get_edges():
        source_id = edge.get_source().strip('"')
        dest_id = edge.get_destination().strip('"')
        
        # Get function names using the mapping
        source_func = node_to_function.get(source_id, source_id)
        dest_func = node_to_function.get(dest_id, dest_id)
        
        # For icgraph files, invert the relationship direction to match the semantic meaning
        if is_icgraph:
            relationships.append(f"{dest_func} -> {source_func}")
        else:
            relationships.append(f"{source_func} -> {dest_func}")
    
    return relationships

def write_relationships_to_file(
    output_path: str,
    relationships: List[str],
    dot_file_path: str,
    is_icgraph: bool
) -> None:
    """
    Writes relationships to a text file.
    
    Args:
        output_path: Path to the output file
        relationships: List of relationship strings
        dot_file_path: Path to the original dot file
        is_icgraph: Whether this is an inverse caller graph
    """
    with open(output_path, 'w') as f:
        f.write(f"# Function call relationships from {os.path.basename(dot_file_path)}\n")
        f.write(f"# Total relationships: {len(relationships)}\n")
        
        # Change the format description based on file type
        if is_icgraph:
            f.write("# Format: callee -> caller\n\n")
        else:
            f.write("# Format: caller -> callee\n\n")
        
        for relationship in sorted(relationships):
            f.write(f"{relationship}\n")

def generate_function_relationships_text(graph: pydot.Graph, dot_file_path: str) -> Optional[str]:
    """
    Generates a text file listing all caller-callee function relationships.
    
    Args:
        graph: The pydot Graph object
        dot_file_path: Path to the original .dot file (used to generate output filename)
    
    Returns:
        Path to the generated text file
    """
    try:
        # Determine the output directory
        output_dir = get_output_directory(dot_file_path)
        
        # Generate output filename
        filename = os.path.basename(os.path.splitext(dot_file_path)[0]) + "_relationships.txt"
        output_path = os.path.join(output_dir, filename)
        
        # Create a dictionary to map node IDs to function names
        node_to_function = create_node_to_function_mapping(graph)
        
        # Check if this is an icgraph file (inverse caller graph)
        is_icgraph = "_icgraph" in dot_file_path
        
        # Extract relationships from graph edges
        relationships = extract_relationships_from_edges(graph, node_to_function, is_icgraph)
        
        # Write relationships to file
        write_relationships_to_file(output_path, relationships, dot_file_path, is_icgraph)
        
        print(f"Function relationships text file generated: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error generating function relationships text file: {e}")
        return None

def find_dot_files(directory: str) -> List[str]:
    """
    Find all .dot files in the specified directory and its dot_files subdirectory if it exists
    
    Args:
        directory: Directory to search for .dot files
    
    Returns:
        List of paths to .dot files
    """
    dot_files: List[str] = []
    
    # Check if this is a parent directory with a dot_files subdirectory
    dot_files_subdir = os.path.join(directory, "dot_files")
    if os.path.isdir(dot_files_subdir):
        # If dot_files subdirectory exists, search only there
        for file in os.listdir(dot_files_subdir):
            if file.endswith(".dot"):
                dot_files.append(os.path.join(dot_files_subdir, file))
    else:
        # Otherwise search the provided directory normally
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".dot"):
                    dot_files.append(os.path.join(root, file))
    
    return dot_files

def find_relationship_files(dot_files: List[str]) -> List[str]:
    """
    Find all relationship files generated from dot files.
    
    Args:
        dot_files: List of dot file paths
    
    Returns:
        List of relationship file paths
    """
    rel_files: List[str] = []
    for dot_file in dot_files:
        # Get the directory where relationship files are saved
        rel_dir = get_output_directory(dot_file)
        
        # Check for relationship files in that directory
        dot_basename = os.path.basename(os.path.splitext(dot_file)[0])
        rel_filename = dot_basename + "_relationships.txt"
        rel_filepath = os.path.join(rel_dir, rel_filename)
        
        if os.path.exists(rel_filepath):
            rel_files.append(rel_filepath)
    
    return rel_files

def collect_unique_relationships(rel_files: List[str]) -> Set[str]:
    """
    Collect unique relationships from all relationship files.
    
    Args:
        rel_files: List of relationship file paths
    
    Returns:
        Set of unique relationships
    """
    all_relationships: Set[str] = set()
    for rel_file in rel_files:
        with open(rel_file, 'r') as f:
            for line in f:
                # Skip comment lines
                if line.startswith('#') or not line.strip():
                    continue
                relationship = line.strip()
                all_relationships.add(relationship)
    
    return all_relationships

def get_output_dir_for_combined_file(directory: str) -> str:
    """
    Determine the appropriate directory for the combined relationships file.
    
    Args:
        directory: Original directory
    
    Returns:
        Directory path where the combined file should be saved
    """
    if os.path.basename(directory) == "dot_files":
        return os.path.dirname(directory)
    return directory

def generate_combined_relationships_file(directory: str, dot_files: List[str]) -> Optional[str]:
    """
    Generates a combined text file with relationships from all .dot files
    
    Args:
        directory: Directory to save the combined file
        dot_files: List of .dot files that were processed
    
    Returns:
        Path to the combined relationships file
    """
    try:
        # Determine if we're processing icgraph (callee->caller) or cgraph (caller->callee) files based on the directory name
        is_callee_caller = "callee_caller" in os.path.basename(directory).lower()
        
        # Determine output directory for the combined file
        output_dir = get_output_dir_for_combined_file(directory)
        output_path = os.path.join(output_dir, "all_function_relationships.txt")
        
        # Find all relationship files
        rel_files = find_relationship_files(dot_files)
        
        # Collect unique relationships from all individual relationship files
        all_relationships = collect_unique_relationships(rel_files)
        
        # Write combined relationships to file
        with open(output_path, 'w') as f:
            f.write(f"# Combined function call relationships from all dot files in {os.path.basename(output_dir)}\n")
            f.write(f"# Total unique relationships: {len(all_relationships)}\n")
            
            # Use the appropriate format description based on the directory type
            if is_callee_caller:
                f.write("# Format: callee -> caller\n\n")
            else:
                f.write("# Format: caller -> callee\n\n")
            
            for relationship in sorted(all_relationships):
                f.write(f"{relationship}\n")
        
        print(f"Combined function relationships file generated: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error generating combined relationships file: {e}")
        return None

def read_relationships_from_file(file_path: str) -> Dict[str, bool]:
    """
    Reads relationships from a file into a dictionary.
    
    Args:
        file_path: Path to the relationships file
    
    Returns:
        Dictionary containing unique relationships
    """
    relationships: Dict[str, bool] = {}
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                # Skip comment lines
                if line.startswith('#') or not line.strip():
                    continue
                relationship = line.strip()
                relationships[relationship] = True
    return relationships

def collect_relationships_from_directory(directory: str, file_pattern: str) -> Dict[str, bool]:
    """
    Collects relationships from all relationship files in a directory.
    
    Args:
        directory: Directory to search
        file_pattern: File pattern to match (e.g., "*_relationships.txt")
    
    Returns:
        Dictionary containing unique relationships
    """
    relationships: Dict[str, bool] = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith("_relationships.txt") and file != "all_function_relationships.txt":
                rel_file = os.path.join(root, file)
                file_relationships = read_relationships_from_file(rel_file)
                relationships.update(file_relationships)
    return relationships

def write_master_relationships_file(
    output_path: str,
    base_directory: str,
    callee_caller_relationships: Dict[str, bool],
    caller_callee_relationships: Dict[str, bool]
) -> None:
    """
    Writes the master relationships file.
    
    Args:
        output_path: Path to the output file
        base_directory: The base directory name
        callee_caller_relationships: Dictionary of callee-caller relationships
        caller_callee_relationships: Dictionary of caller-callee relationships
    """
    with open(output_path, 'w') as f:
        f.write("# MASTER FUNCTION RELATIONSHIP FILE\n")
        f.write(f"# Generated on: {os.path.basename(base_directory)}\n\n")
        
        # Write callee->caller relationships section
        f.write("# ==========================================================\n")
        f.write("# CALLEE -> CALLER RELATIONSHIPS\n")
        f.write(f"# Total: {len(callee_caller_relationships)}\n")
        f.write("# ==========================================================\n\n")
        
        for relationship in sorted(callee_caller_relationships.keys()):
            f.write(f"{relationship}\n")
        
        # Write caller->callee relationships section
        f.write("\n\n# ==========================================================\n")
        f.write("# CALLER -> CALLEE RELATIONSHIPS\n")
        f.write(f"# Total: {len(caller_callee_relationships)}\n")
        f.write("# ==========================================================\n\n")
        
        for relationship in sorted(caller_callee_relationships.keys()):
            f.write(f"{relationship}\n")
        
        # Write statistics
        f.write("\n\n# ==========================================================\n")
        f.write("# STATISTICS\n")
        f.write("# ==========================================================\n")
        f.write(f"# Total callee->caller relationships: {len(callee_caller_relationships)}\n")
        f.write(f"# Total caller->callee relationships: {len(caller_callee_relationships)}\n")
        f.write(f"# Total relationships: {len(callee_caller_relationships) + len(caller_callee_relationships)}\n")

def generate_master_relationships_file(base_directory: str) -> Optional[str]:
    """
    Generates a master file with all function relationships from all subdirectories,
    clearly separated by relationship type.
    
    Args:
        base_directory: The base directory where the graph subdirectories are located
    
    Returns:
        Path to the generated master relationships file or None if generation fails
    """
    try:
        # Determine parent directory where to save the master file
        parent_directory = os.path.dirname(base_directory)
        output_path = os.path.join(parent_directory, "master_function_relationships.txt")
        
        # Define subdirectories to check with new names
        callee_caller_dir = os.path.join(base_directory, "callee_caller_graph")
        caller_callee_dir = os.path.join(base_directory, "caller_callee_graph")
        
        # Check if directories exist
        callee_caller_exists = os.path.isdir(callee_caller_dir)
        caller_callee_exists = os.path.isdir(caller_callee_dir)
        
        if not callee_caller_exists and not caller_callee_exists:
            print("Error: Neither callee_caller_graph nor caller_callee_graph directories exist")
            return None
        
        # Dictionaries to store unique relationships by type
        callee_caller_relationships: Dict[str, bool] = {}  # callee -> caller
        caller_callee_relationships: Dict[str, bool] = {}  # caller -> callee
        
        # Filenames for the combined relationship files
        callee_caller_combined = os.path.join(callee_caller_dir, "all_function_relationships.txt") if callee_caller_exists else None
        caller_callee_combined = os.path.join(caller_callee_dir, "all_function_relationships.txt") if caller_callee_exists else None
        
        # Process callee_caller_graph combined file if it exists
        if callee_caller_exists and os.path.isfile(callee_caller_combined):
            callee_caller_relationships = read_relationships_from_file(callee_caller_combined)
        elif callee_caller_exists:
            # Look for individual relationship files if no combined file
            callee_caller_relationships = collect_relationships_from_directory(callee_caller_dir, "*_relationships.txt")
        
        # Process caller_callee_graph combined file if it exists
        if caller_callee_exists and os.path.isfile(caller_callee_combined):
            caller_callee_relationships = read_relationships_from_file(caller_callee_combined)
        elif caller_callee_exists:
            # Look for individual relationship files if no combined file
            caller_callee_relationships = collect_relationships_from_directory(caller_callee_dir, "*_relationships.txt")
        
        # Write the master relationships file
        write_master_relationships_file(output_path, base_directory, callee_caller_relationships, caller_callee_relationships)
        
        print(f"Master function relationships file generated: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error generating master relationships file: {e}")
        return None

def main() -> None:
    # Check for directory in environment variable first
    directory = os.environ.get("DOT_FILES_DIRECTORY")
    
    # If not in environment variable, get from user input or use current directory
    if not directory:
        directory = input("Enter directory to search for .dot files (press Enter for current directory): ")
        if not directory:
            directory = os.getcwd()
    
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        return
    
    print(f"Processing dot files in: {directory}")
    dot_files = find_dot_files(directory)
    
    if not dot_files:
        print(f"No .dot files found in {directory}")
        return
        
    print(f"Found {len(dot_files)} .dot files")
    
    # Process each .dot file
    for dot_file in dot_files:
        process_dot_file(dot_file)
    
    # Generate a combined relationships file with all function relationships
    generate_combined_relationships_file(directory, dot_files)
    
    # Generate a master relationships file with all function relationships
    generate_master_relationships_file(directory)

if __name__ == "__main__":
    main()