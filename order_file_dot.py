import os
import shutil
import sys
from typing import Optional, List, Dict, Set, Tuple, Any, Union

def create_folder_structure(dot_folder: str) -> Dict[str, str]:
    """
    Crea la struttura di cartelle per l'organizzazione dei file .dot
    
    Args:
        dot_folder: Percorso della cartella contenente i file .dot
        
    Returns:
        Dizionario contenente i percorsi delle cartelle create
    """
    # Cartelle separate
    function_graphs_folder = os.path.join(dot_folder, "function_graphs")
    directory_graphs_folder = os.path.join(dot_folder, "directory_graphs")
    
    # Nuove cartelle per i tipi di grafico con nomi più descrittivi
    callee_caller_graph_folder = os.path.join(dot_folder, "callee_caller_graph")
    caller_callee_graph_folder = os.path.join(dot_folder, "caller_callee_graph")
    
    # Sottocartelle per i file .dot
    callee_caller_dot_folder = os.path.join(callee_caller_graph_folder, "dot_files")
    caller_callee_dot_folder = os.path.join(caller_callee_graph_folder, "dot_files")

    # Crea le cartelle se non esistono
    os.makedirs(function_graphs_folder, exist_ok=True)
    os.makedirs(directory_graphs_folder, exist_ok=True)
    os.makedirs(callee_caller_graph_folder, exist_ok=True)
    os.makedirs(caller_callee_graph_folder, exist_ok=True)
    os.makedirs(callee_caller_dot_folder, exist_ok=True)
    os.makedirs(caller_callee_dot_folder, exist_ok=True)
    
    return {
        "function_graphs": function_graphs_folder,
        "directory_graphs": directory_graphs_folder,
        "callee_caller_graph": callee_caller_graph_folder,
        "caller_callee_graph": caller_callee_graph_folder,
        "callee_caller_dot": callee_caller_dot_folder,
        "caller_callee_dot": caller_callee_dot_folder
    }

def process_single_file(dot_folder: str, specific_file: str, folders: Dict[str, str]) -> bool:
    """
    Processa un singolo file .dot e lo copia nelle cartelle appropriate
    
    Args:
        dot_folder: Percorso della cartella contenente i file .dot
        specific_file: Percorso del file specifico da processare
        folders: Dizionario contenente i percorsi delle cartelle
        
    Returns:
        True se il file è stato processato con successo, False altrimenti
    """
    if not os.path.isfile(specific_file):
        # Prova a vedere se è nel dot_folder
        possible_path = os.path.join(dot_folder, specific_file)
        if os.path.isfile(possible_path):
            specific_file = possible_path
        else:
            print(f"Error: File {specific_file} not found")
            return False
    
    filename = os.path.basename(specific_file)
    if filename.endswith(".dot"):
        # Prima separazione: directory o function
        if filename.startswith("dir_"):
            primary_dest_path = os.path.join(folders["directory_graphs"], filename)
            shutil.copy2(specific_file, primary_dest_path)
        else:
            primary_dest_path = os.path.join(folders["function_graphs"], filename)
            shutil.copy2(specific_file, primary_dest_path)
            
            # Seconda separazione: caller graph o call graph
            if filename.endswith("_icgraph.dot"):
                secondary_dest_path = os.path.join(folders["callee_caller_dot"], filename)
                shutil.copy2(specific_file, secondary_dest_path)
            elif filename.endswith("_cgraph.dot"):
                secondary_dest_path = os.path.join(folders["caller_callee_dot"], filename)
                shutil.copy2(specific_file, secondary_dest_path)
            
        print(f"File {filename} copied to appropriate folders")
        return True
    else:
        print(f"Error: {filename} is not a .dot file")
        return False

def process_all_files(dot_folder: str, folders: Dict[str, str]) -> bool:
    """
    Processa tutti i file .dot nella cartella specificata
    
    Args:
        dot_folder: Percorso della cartella contenente i file .dot
        folders: Dizionario contenente i percorsi delle cartelle
        
    Returns:
        True se tutti i file sono stati processati con successo, False altrimenti
    """
    files_processed = 0
    for filename in os.listdir(dot_folder):
        if filename.endswith(".dot"):
            src_path = os.path.join(dot_folder, filename)
            
            # Prima separazione: directory o function
            if filename.startswith("dir_"):
                dest_path = os.path.join(folders["directory_graphs"], filename)
                shutil.copy2(src_path, dest_path)
            else:
                # Copy to function graphs folder
                dest_path = os.path.join(folders["function_graphs"], filename)
                shutil.copy2(src_path, dest_path)
                
                # Seconda separazione: caller graph o call graph
                if filename.endswith("_icgraph.dot"):
                    secondary_dest_path = os.path.join(folders["callee_caller_dot"], filename)
                    shutil.copy2(src_path, secondary_dest_path)
                elif filename.endswith("_cgraph.dot"):
                    secondary_dest_path = os.path.join(folders["caller_callee_dot"], filename)
                    shutil.copy2(src_path, secondary_dest_path)
            
            # Move from original location after all copies are made
            shutil.move(src_path, dest_path)
            files_processed += 1
    
    print(f"Separazione completata. Processed {files_processed} files.")
    print_folder_structure(folders)
    return True

def print_folder_structure(folders: Dict[str, str]) -> None:
    """
    Stampa la struttura delle cartelle create
    
    Args:
        folders: Dizionario contenente i percorsi delle cartelle
    """
    print(f"Files are organized in the following folders:")
    print(f"- {folders['directory_graphs']}: Directory graphs")
    print(f"- {folders['function_graphs']}: All function graphs")
    print(f"- {folders['callee_caller_graph']}: Caller graphs folder [format: callee -> caller]")
    print(f"  └─ {folders['callee_caller_dot']}: .dot files")
    print(f"- {folders['caller_callee_graph']}: Call graphs folder [format: caller -> callee]")
    print(f"  └─ {folders['caller_callee_dot']}: .dot files")

def organize_dot_files(dot_folder: str, specific_file: Optional[str] = None) -> bool:
    """
    Organizza i file .dot in cartelle separate in base al tipo di grafico
    
    Args:
        dot_folder: Percorso della cartella contenente i file .dot
        specific_file: Percorso di un file specifico da processare (opzionale)
        
    Returns:
        True se i file sono stati organizzati con successo, False altrimenti
    """
    # Crea la struttura di cartelle
    folders = create_folder_structure(dot_folder)
    
    # Processa i file
    if specific_file:
        return process_single_file(dot_folder, specific_file, folders)
    else:
        return process_all_files(dot_folder, folders)

def main() -> None:
    """
    Funzione principale che gestisce gli argomenti da linea di comando
    """
    # Check if arguments were provided
    if len(sys.argv) < 2:
        print("Usage: python order_file_dot.py <dot_folder_path> [specific_file]")
        sys.exit(1)
        
    dot_folder = sys.argv[1]
    if not os.path.isdir(dot_folder):
        print(f"Error: {dot_folder} is not a valid directory")
        sys.exit(1)
    
    specific_file = None
    if len(sys.argv) > 2:
        specific_file = sys.argv[2]
    
    organize_dot_files(dot_folder, specific_file)

if __name__ == "__main__":
    main()
