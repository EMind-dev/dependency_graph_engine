#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import shutil
import argparse
from typing import Optional, List, Dict, Tuple, Any, Union, Callable

# Define the path to the virtual environment
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(SCRIPT_DIR, "venv")
REQUIREMENTS = ["pydot", "graphviz"]

def is_venv_installed() -> bool:
    """
    Verifica se l'ambiente virtuale esiste.
    
    Returns:
        True se l'ambiente virtuale esiste, False altrimenti
    """
    return os.path.isdir(VENV_DIR) and (
        os.path.isfile(os.path.join(VENV_DIR, "bin", "python")) or  # Unix/macOS
        os.path.isfile(os.path.join(VENV_DIR, "Scripts", "python.exe"))  # Windows
    )

def create_venv() -> bool:
    """
    Crea un ambiente virtuale.
    
    Returns:
        True se l'ambiente virtuale è stato creato con successo, False altrimenti
    """
    print("Creating virtual environment...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])
        print("Virtual environment created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        return False

def get_python_path() -> str:
    """
    Ottiene il percorso dell'eseguibile Python nell'ambiente virtuale in base al sistema operativo.
    
    Returns:
        Percorso dell'interprete Python nell'ambiente virtuale
    """
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "python")
    else:
        return os.path.join(VENV_DIR, "bin", "python")

def get_pip_path() -> str:
    """
    Ottiene il percorso dell'eseguibile pip nell'ambiente virtuale in base al sistema operativo.
    
    Returns:
        Percorso dell'eseguibile pip nell'ambiente virtuale
    """
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "pip")
    else:
        return os.path.join(VENV_DIR, "bin", "pip")

def install_dependencies() -> bool:
    """
    Installa le dipendenze richieste nell'ambiente virtuale.
    
    Returns:
        True se le dipendenze sono state installate con successo, False altrimenti
    """
    print("Installing dependencies...")
    
    # Ottieni il percorso di pip
    pip_path = get_pip_path()
    
    try:
        # Upgrade pip first
        subprocess.check_call([pip_path, "install", "--upgrade", "pip"])
        
        # Install required packages
        for package in REQUIREMENTS:
            print(f"Installing {package}...")
            subprocess.check_call([pip_path, "install", package])
        
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def run_order_file_dot(dot_folder: str, filename: Optional[str] = None) -> bool:
    """
    Esegue lo script order_file_dot.py con la cartella dot_folder e il filename opzionale.
    
    Args:
        dot_folder: Percorso della cartella contenente i file .dot
        filename: Nome del file specifico da processare (opzionale)
        
    Returns:
        True se lo script è stato eseguito con successo, False altrimenti
    """
    print("Running file organization script...")
    
    # Ottieni il percorso dell'interprete Python
    python_path = get_python_path()
    
    script_path = os.path.join(SCRIPT_DIR, "order_file_dot.py")
    
    try:
        command = [python_path, script_path, dot_folder]
        if filename:
            command.append(filename)
        subprocess.check_call(command)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running file organization script: {e}")
        return False

def run_call_graph_processor(directory: Optional[str] = None) -> bool:
    """
    Esegue lo script call_graph_processor.py su una directory specifica.
    
    Args:
        directory: Percorso della directory da processare (opzionale)
        
    Returns:
        True se lo script è stato eseguito con successo, False altrimenti
    """
    print(f"Running call graph processor on {directory}...")
    
    # Ottieni il percorso dell'interprete Python
    python_path = get_python_path()
    
    script_path = os.path.join(SCRIPT_DIR, "call_graph_processor.py")
    
    try:
        # We'll use environment variables to pass the directory to the script
        # This avoids having to modify call_graph_processor.py
        env = os.environ.copy()
        if directory:
            env["DOT_FILES_DIRECTORY"] = directory
            
        subprocess.check_call([python_path, script_path], env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running call graph processor: {e}")
        return False

def create_temp_script_for_master_file(dot_folder: str) -> str:
    """
    Crea uno script temporaneo per generare il file master delle relazioni.
    
    Args:
        dot_folder: Percorso della cartella contenente i file .dot
        
    Returns:
        Percorso dello script temporaneo creato
    """
    temp_script_path = os.path.join(SCRIPT_DIR, "temp_generate_master.py")
    with open(temp_script_path, 'w') as f:
        f.write(f"""
import sys
sys.path.append("{SCRIPT_DIR}")
from call_graph_processor import generate_master_relationships_file

if __name__ == "__main__":
    generate_master_relationships_file("{dot_folder}")
""")
    return temp_script_path

def generate_master_file(dot_folder: str) -> bool:
    """
    Genera un file master con tutte le relazioni di funzione nella directory principale.
    
    Args:
        dot_folder: Percorso della cartella contenente i file .dot
        
    Returns:
        True se il file è stato generato con successo, False altrimenti
    """
    print("Generating master relationship file...")
    
    # Ottieni il percorso dell'interprete Python
    python_path = get_python_path()
    
    try:
        # Crea uno script temporaneo
        temp_script_path = create_temp_script_for_master_file(dot_folder)
        
        # Esegui lo script temporaneo
        subprocess.check_call([python_path, temp_script_path])
        
        # Pulisci
        os.remove(temp_script_path)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating master relationships file: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def check_graphviz_installation(auto_yes: bool) -> bool:
    """
    Verifica se Graphviz è installato nel sistema.
    
    Args:
        auto_yes: Se True, continua automaticamente anche se Graphviz non è installato
        
    Returns:
        True se si può continuare, False se bisogna uscire
    """
    if shutil.which("dot") is None:
        print("WARNING: Graphviz does not appear to be installed on your system.")
        print("The pydot library requires Graphviz to generate graphs.")
        print("Please install Graphviz from https://graphviz.org/download/")
        
        if not auto_yes:
            user_continue = input("Continue anyway? (y/n): ")
            if user_continue.lower() != "y":
                print("Exiting...")
                return False
        else:
            print("Continuing automatically due to --yes flag...")
    
    return True

def setup_environment(auto_yes: bool) -> bool:
    """
    Configura l'ambiente virtuale e installa le dipendenze.
    
    Args:
        auto_yes: Se True, risponde automaticamente sì a tutti i prompt
        
    Returns:
        True se l'ambiente è stato configurato con successo, False altrimenti
    """
    # Check and create virtual environment if needed
    if not is_venv_installed():
        if not create_venv():
            print("Failed to create virtual environment. Exiting.")
            return False
        
        if not install_dependencies():
            print("Failed to install dependencies. Exiting.")
            return False
    else:
        print("Virtual environment already exists.")
        if not auto_yes:
            update = input("Do you want to update dependencies? (y/n): ")
            should_update = update.lower() == "y"
        else:
            print("Automatically updating dependencies due to --yes flag...")
            should_update = True
            
        if should_update:
            if not install_dependencies():
                print("Failed to update dependencies, but continuing...")
    
    return True

def process_graph_folders(dot_folder: str) -> bool:
    """
    Processa le cartelle dei grafi generate da order_file_dot.py.
    
    Args:
        dot_folder: Percorso della cartella contenente i file .dot
        
    Returns:
        True se le cartelle sono state processate con successo, False altrimenti
    """
    # Define graph folders paths with new names
    function_graphs_dir = os.path.join(dot_folder, "function_graphs")
    callee_caller_graph_dir = os.path.join(dot_folder, "callee_caller_graph")
    caller_callee_graph_dir = os.path.join(dot_folder, "caller_callee_graph")
    
    # Process each graph folder with call_graph_processor.py
    print("\nProcessing function graphs...")
    if not run_call_graph_processor(function_graphs_dir):
        print("Warning: Failed to fully process function_graphs directory")
        return False
    
    print("\nProcessing callee->caller graphs (formerly caller_graphs)...")
    if not run_call_graph_processor(callee_caller_graph_dir):
        print("Warning: Failed to fully process callee_caller_graph directory")
        return False
    
    print("\nProcessing caller->callee graphs (formerly call_graphs)...")
    if not run_call_graph_processor(caller_callee_graph_dir):
        print("Warning: Failed to fully process caller_callee_graph directory")
        return False
    
    return True

def main() -> None:
    """
    Funzione principale che coordina l'intero processo.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Setup and run call graph processor')
    parser.add_argument('--yes', '-y', action='store_true', help='Automatically answer yes to all prompts')
    parser.add_argument('--filename', '-f', help='Filename to process with order_file_dot.py')
    parser.add_argument('--dot-folder', '-d', required=True, help='Path to the folder containing .dot files')
    args = parser.parse_args()
    
    print("Setting up environment for call graph processor...")
    
    # Verifica se Graphviz è installato
    if not check_graphviz_installation(args.yes):
        return
    
    # Configura l'ambiente virtuale e installa le dipendenze
    if not setup_environment(args.yes):
        return
    
    # Verifica che la cartella dot_folder esista
    if not os.path.isdir(args.dot_folder):
        print(f"Error: The dot folder '{args.dot_folder}' does not exist or is not a directory")
        return
    
    # Esegui lo script order_file_dot.py
    if not run_order_file_dot(args.dot_folder, args.filename):
        print("Failed to organize files. Exiting.")
        return
    
    # Processa le cartelle dei grafi
    process_graph_folders(args.dot_folder)
    
    # Genera il file master delle relazioni
    print("\nGenerating master relationship file...")
    if not generate_master_file(args.dot_folder):
        print("Warning: Failed to generate master relationship file")
    
    print("\nProcessing completed!")

if __name__ == "__main__":
    main()
