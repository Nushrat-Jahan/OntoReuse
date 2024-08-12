import sys
import rdflib
import requests
import os
import tempfile
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

def count_elements(graph):
    object_properties_count = len(list(graph.subjects(rdflib.RDF.type, rdflib.OWL.ObjectProperty)))
    classes_count = len(list(graph.subjects(rdflib.RDF.type, rdflib.OWL.Class)))
    return object_properties_count, classes_count

def download_and_parse_ontology(url):
    try:
        response = requests.get(url, headers={"Accept": "text/turtle,application/rdf+xml,application/owl+xml,application/ld+json"}, allow_redirects=True)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type')
        
        if 'text/turtle' in content_type:
            format = 'turtle'
        elif 'application/rdf+xml' in content_type:
            format = 'xml'
        elif 'application/owl+xml' in content_type:
            format = 'xml'
        elif 'application/ld+json' in content_type:
            format = 'json-ld'
        else:
            print(f"Unexpected content type: {content_type}")
            return None
        
        graph = rdflib.Graph()
        graph.parse(data=response.content, format=format)
        return graph
    except requests.exceptions.RequestException as e:
        print(f"Failed to download ontology from {url}: {e}")
        return None

def resolve_imports(graph, base_url, temp_dir):
    for _, _, imported_iri in graph.triples((None, rdflib.OWL.imports, None)):
        if not imported_iri.startswith('http://') and not imported_iri.startswith('https://'):
            imported_iri = base_url + imported_iri if base_url else imported_iri
        print(f"Resolved IRI: {imported_iri}")
        imported_graph = download_and_parse_ontology(imported_iri)
        if imported_graph:
            graph += imported_graph  # Merge the graphs
            resolve_imports(imported_graph, base_url, temp_dir)  # Recursively resolve imports
        else:
            print(f"Failed to download or load ontology from URL: {imported_iri}")

def evaluate_with_foops(ontology_url):
    url = "http://localhost:8083/assessOntology"
    headers = {
        'accept': 'application/json;charset=UTF-8',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    data = {"ontologyUri": ontology_url}

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to evaluate ontology with FOOPS!: {e}")
        return None

def check_content_negotiation(base_url):
    formats = [".ttl", ".rdf", ".owl", ".jsonld", ".n3", ".nt"]
    found_formats = set()
    
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)

        for link in links, href in link:
            for fmt in formats:
                if href.endswith(fmt):
                    found_formats.add(fmt)
    
    except requests.exceptions.RequestException as e:
        print(f"Failed to check content negotiation for {base_url}: {e}")

    return found_formats

def main():
    if len(sys.argv) < 2:
        print("Usage: python quality.py <ontology_source>")
        sys.exit(1)
    
    ontology_source = sys.argv[1]

    if ontology_source.startswith('http://') or ontology_source.startswith('https://'):
        parsed_url = urlparse(ontology_source)
        base_url = urljoin(ontology_source, '/'.join(parsed_url.path.split('/')[:-1]) + '/')
        
        foops_results = evaluate_with_foops(ontology_source)
        if foops_results:
            print("\nFOOPS! Evaluation Results:")
            print(foops_results)
        else:
            print("Failed to get results from FOOPS!")
        
        found_formats = check_content_negotiation(base_url)
        content_negotiation_score = len(found_formats)
        print(f"\nContent Negotiation Score: {content_negotiation_score}/6")
        print("Found formats:", ", ".join(found_formats))
    else:
        base_url = None
        try:
            with open(ontology_source, 'r') as file:
                for line in file:
                    if line.startswith('@base'):
                        base_url = line.split('<')[1].split('>')[0]
                        break
                    if "imports:" in line:
                        base_url = line.split(':')[1].strip()
                        if base_url.startswith('<') and base_url.endswith('>'):
                            base_url = base_url[1:-1]
        except FileNotFoundError:
            print("The file path is not correct. Please provide a valid file path.")
            return

        main_graph = rdflib.Graph()
        main_graph.parse(ontology_source, format='turtle')

        with tempfile.TemporaryDirectory() as temp_dir:
            if base_url:
                resolve_imports(main_graph, base_url, temp_dir)
            
            main_object_properties_count, main_classes_count = count_elements(main_graph)
            print(f"\nTotal - Object Properties: {main_object_properties_count}, Classes: {main_classes_count}")
            
            if base_url:
                foops_results = evaluate_with_foops(base_url)
                if foops_results:
                    print("\nFOOPS! Evaluation Results:")
                    print(foops_results)
                else:
                    print("Failed to get results from FOOPS!")
            else:
                print("Base URL not found. Cannot perform FOOPS! evaluation.")

if __name__ == "__main__":
    main()
