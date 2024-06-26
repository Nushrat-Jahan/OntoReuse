# input term is also considered for related term 
# Example term: device, solar energy
# Example ontology: Photovoltaic, Saref4ener
# First asks word to search for related terms
# Then asks for 1 or 2 either to upload from local file or to upload URL


import rdflib
from rdflib import Graph, RDF, OWL, RDFS
import requests
import tkinter as tk
from tkinter import filedialog
from difflib import SequenceMatcher
import tempfile

def count_elements(graph):
    # Count classes
    classes = set(graph.subjects(RDF.type, OWL.Class))
    
    # Count object properties
    object_properties = set(graph.subjects(RDF.type, OWL.ObjectProperty))
    
    # Include subclasses and subproperties in the count
    for s, p, o in graph.triples((None, RDF.type, OWL.Restriction)):
        for sub, prop, obj in graph.triples((s, OWL.onProperty, None)):
            if (obj, RDF.type, OWL.ObjectProperty) in graph:
                object_properties.add(obj)
            elif (obj, RDF.type, OWL.Class) in graph:
                classes.add(obj)

    return len(object_properties), len(classes)

def select_file_dialog(title):
    # This function opens a file dialog for selecting a Turtle file
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window
    root.lift()  # Bring the dialog to the front
    root.attributes('-topmost', True)  # Keep the dialog on top
    file_path = filedialog.askopenfilename(title=title, filetypes=[("Turtle files", "*.ttl"), ("All files", "*.*")])
    root.destroy()  # Destroy the root window after file selection
    return file_path

def download_and_parse_ontology(url):
    # Downloads and parses an ontology from a given URL
    try:
        response = requests.get(url, headers={"Accept": "text/turtle,application/rdf+xml"}, allow_redirects=True)
        response.raise_for_status()
        
        graph = Graph()
        # Force the parser to treat the content as Turtle format
        graph.parse(data=response.content, format='turtle')
        return graph
    except requests.exceptions.RequestException as e:
        print(f"Failed to download ontology from {url}: {e}")
        return None
    except Exception as e:
        print(f"Failed to parse ontology from {url}: {e}")
        return None

def resolve_imports(graph, base_url, temp_dir):
    # Recursively resolves and merges imports found in the RDF graph
    for _, _, imported_iri in graph.triples((None, OWL.imports, None)):
        imported_iri = str(imported_iri)
        if not imported_iri.startswith('http://') and not imported_iri.startswith('https://'):
            imported_iri = base_url + imported_iri if base_url else imported_iri
        print(f"Resolved IRI: {imported_iri}")
        imported_graph = download_and_parse_ontology(imported_iri)
        if imported_graph:
            graph += imported_graph
            resolve_imports(imported_graph, base_url, temp_dir)
        else:
            print(f"Failed to download or load ontology from URL: {imported_iri}")

def get_ontology_source():
    choice = input("Enter '1' to select a local Turtle file or '2' to provide a URL: ").strip()
    if choice == '1':
        return select_file_dialog("Select the Main Ontology File")
    elif choice == '2':
        url = input("Enter the URL of the Turtle file: ").strip()
        if url.startswith('http://') or url.startswith('https://'):
            return url
        else:
            print("Invalid URL. Please enter a valid URL.")
            return get_ontology_source()
    else:
        print("Invalid choice. Please enter '1' or '2'.")
        return get_ontology_source()

def load_ontology():
    # Get the source of the ontology (local file or URL)
    ontology_source = get_ontology_source()

    # Check if the source is a URL or a file path
    if ontology_source.startswith('http://') or ontology_source.startswith('https://'):
        # Download and parse the ontology from the URL
        main_graph = download_and_parse_ontology(ontology_source)
        base_url = ontology_source.rsplit('/', 1)[0] + '/' if main_graph else None
    else:
        # Parse the local ontology file
        base_url = None
        try:
            if ontology_source:
                with open(ontology_source, 'r') as file:
                    for line in file:
                        if line.startswith('@base'):
                            base_url = line.split('<')[1].split('>')[0]
                            break
                        if "imports:" in line:
                            base_url = line.split(':')[1].strip()
                            if base_url.startswith('<') and base_url.endswith('>'):
                                base_url = base_url[1:-1]  # Remove < and >

                # Parse the main ontology
                main_graph = Graph()
                main_graph.parse(ontology_source, format='turtle')
            else:
                main_graph = None
        except FileNotFoundError:
            print("The file path is not correct. Please provide a valid file path.")
            main_graph = None

    if main_graph:
        # Create a temporary directory for downloaded ontologies
        with tempfile.TemporaryDirectory() as temp_dir:
            if base_url:
                resolve_imports(main_graph, base_url, temp_dir)

            # Count elements in the merged graph
            object_properties_count, classes_count = count_elements(main_graph)
            print(f"\nTotal - Object Properties: {object_properties_count}, Classes: {classes_count}")

            # Extract ontology concepts
            ontology = set()
            for s in main_graph.subjects(RDF.type, OWL.Class):
                ontology.add(str(s).split('/')[-1])
            for s in main_graph.subjects(RDF.type, RDFS.Class):
                ontology.add(str(s).split('/')[-1])

            return list(ontology), main_graph
    else:
        print("Failed to load the ontology.")
        return [], None

def get_related_words(input_term):
    """
    Provides lexically related terms for a given input term by querying the Datamuse API.

    Args:
        input_term (str): A single word or multiple-word phrase.

    Returns:
        list: A list of related terms.
    """
    # Normalize the input
    input_term_normalized = input_term.strip().lower()

    # Specific case for solar energy related terms
    if "solar energy" in input_term_normalized or "renewable solar energy" in input_term_normalized:
        return [
            "Photovoltaic (PV) cells",
            "Solar panel",
            "Solar thermal energy",
            "Solar farm",
            "Solar irradiance",
            "Net metering",
            "Solar inverters",
            "Concentrated Solar Power (CSP)",
            "Solar photovoltaic (PV) system",
            "Solar tracker",
            "Solar energy storage",
            "Solar insolation",
            "Solar cell efficiency",
            "Thin-film solar panels",
            "Solar microgrid"
        ]

    # Set for storing unique terms
    related_terms = {input_term_normalized}

    # Datamuse API query
    words = input_term_normalized.split()
    for word in words:
        url = f"https://api.datamuse.com/words?ml={word}"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Check for request errors
            word_entries = response.json()
            for entry in word_entries:
                if 'word' in entry:
                    related_terms.add(entry['word'])
        except requests.exceptions.RequestException as e:
            continue

    return list(related_terms)

def string_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def calculate_metrics(input_term, ontology):
    """
    Calculates domain coverage and ontology relevance based on the input term and ontology provided.

    Args:
        input_term (str): The term to find related words for.
        ontology (list): The ontology containing a list of concepts.

    Returns:
        dict: A dictionary containing domain coverage and ontology relevance.
    """
    # Get related terms
    related_terms = get_related_words(input_term)
    D = len(related_terms)

    # Count how many related terms are in the ontology
    S = sum(1 for term in related_terms if any(string_similarity(term, concept) > 0.8 for concept in ontology))

    # Total number of concepts in the ontology
    O = len(ontology)

    # Calculate domain coverage and ontology relevance
    domain_coverage = (S / D) * 100 if D > 0 else 0
    ontology_relevance = (S / O) * 100 if O > 0 else 0

    return {
        
        'Related Terms': related_terms,
        'Number of Related Terms (D)': D,
        'Number of Related Terms in Ontology (S)': S,
        'Total Number of Concepts in Ontology (O)': O,
        'Domain Coverage (S/D)': domain_coverage,
        'Ontology Relevance (S/O)': ontology_relevance,
    }

def select_file():
    root = tk.Tk()
    root.lift()  # Bring the window to the front
    root.attributes("-topmost", True)  # Ensure it is on top
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Ontology File",
        filetypes=[("All Files", "*.*"), ("TTL files", "*.ttl"), ("RDF files", "*.rdf"), ("OWL files", "*.owl")]
    )
    root.destroy()  # Destroy the root window after file selection
    return file_path

# Example Usage
if __name__ == "__main__":
    input_term = input("Enter a word or phrase: ")
    ontology, main_graph = load_ontology()

    if ontology:
        metrics = calculate_metrics(input_term, ontology)

        print(f"Metrics for '{input_term}':")
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}%")
            else:
                print(f"{key}: {value}")
    else:
        print("No ontology loaded.")
