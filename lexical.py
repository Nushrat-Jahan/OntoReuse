import sys
import rdflib
from rdflib import Graph, RDF, OWL, RDFS
import requests
from difflib import SequenceMatcher
import tempfile
import nltk
nltk.download('wordnet')
from nltk.corpus import wordnet as wn

# Function to count elements in the ontology graph
def count_elements(graph):
    classes = set(graph.subjects(RDF.type, OWL.Class))
    object_properties = set(graph.subjects(RDF.type, OWL.ObjectProperty))
    
    for s, p, o in graph.triples((None, RDF.type, OWL.Restriction)):
        for sub, prop, obj in graph.triples((s, OWL.onProperty, None)):
            if (obj, RDF.type, OWL.ObjectProperty) in graph:
                object_properties.add(obj)
            elif (obj, RDF.type, OWL.Class) in graph:
                classes.add(obj)

    return len(object_properties), len(classes)

# Function to download and parse an ontology
def download_and_parse_ontology(url):
    try:
        response = requests.get(url, headers={"Accept": "text/turtle,application/rdf+xml"}, allow_redirects=True)
        response.raise_for_status()
        
        graph = Graph()
        graph.parse(data=response.content, format='turtle')
        return graph
    except requests.exceptions.RequestException as e:
        print(f"Failed to download ontology from {url}: {e}")
        return None
    except Exception as e:
        print(f"Failed to parse ontology from {url}: {e}")
        return None

# Function to resolve imports in the ontology
def resolve_imports(graph, base_url, temp_dir):
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

# Function to load the ontology from a source
def load_ontology(source):
    if source.startswith('http://') or source.startswith('https://'):
        main_graph = download_and_parse_ontology(source)
        base_url = source.rsplit('/', 1)[0] + '/' if main_graph else None
    else:
        base_url = None
        try:
            if source:
                with open(source, 'r') as file:
                    for line in file:
                        if line.startswith('@base'):
                            base_url = line.split('<')[1].split('>')[0]
                            break
                        if "imports:" in line:
                            base_url = line.split(':')[1].strip()
                            if base_url.startswith('<') and base_url.endswith('>'):
                                base_url = base_url[1:-1]

                main_graph = Graph()
                main_graph.parse(source, format='turtle')
            else:
                main_graph = None
        except FileNotFoundError:
            print("The file path is not correct. Please provide a valid file path.")
            main_graph = None

    if main_graph:
        with tempfile.TemporaryDirectory() as temp_dir:
            if base_url:
                resolve_imports(main_graph, base_url, temp_dir)
            object_properties_count, classes_count = count_elements(main_graph)
            print(f"\nTotal - Object Properties: {object_properties_count}, Classes: {classes_count}")
            ontology = set()
            for s in main_graph.subjects(RDF.type, OWL.Class):
                ontology.add(str(s).split('/')[-1])
            for s in main_graph.subjects(RDF.type, RDFS.Class):
                ontology.add(str(s).split('/')[-1])

            return list(ontology), main_graph
    else:
        print("Failed to load the ontology.")
        return [], None

# Function to get WordNet synonyms and related terms
def get_wordnet_synonyms(term, pos=wn.NOUN):
    synonyms = set()
    for synset in wn.synsets(term, pos=pos):
        for lemma in synset.lemmas():
            synonyms.add(lemma.name().replace('_', ' '))
        for hypernym in synset.hypernyms():
            for lemma in hypernym.lemmas():
                synonyms.add(lemma.name().replace('_', ' '))
        for hyponym in synset.hyponyms():
            for lemma in hyponym.lemmas():
                synonyms.add(lemma.name().replace('_', ' '))
    return list(synonyms)

# Function to get related words using WordNet and Datamuse
def get_related_words(input_term):
    input_term_normalized = input_term.strip().lower()
    related_terms = {input_term_normalized}

    # Add synonyms and related terms from WordNet
    wordnet_synonyms = get_wordnet_synonyms(input_term_normalized)
    related_terms.update(wordnet_synonyms)
    
    # Add words from the Datamuse API with specific tags for relevance
    tags = ['ml', 'rel_syn', 'rel_jja', 'rel_trg']
    for tag in tags:
        url = f"https://api.datamuse.com/words?{tag}={input_term_normalized}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            word_entries = response.json()
            for entry in word_entries:
                if 'word' in entry:
                    related_terms.add(entry['word'])
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch related words from Datamuse API: {e}")

    # Filter terms based on string similarity
    related_terms = filter_related_terms(related_terms, input_term_normalized, threshold=0.5)
    
    return list(related_terms)

# Function to filter related terms based on similarity
def filter_related_terms(related_terms, input_term, threshold=0.5):
    filtered_terms = [term for term in related_terms if string_similarity(input_term, term) >= threshold]
    return filtered_terms

# Function to calculate string similarity
def string_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

# Function to calculate metrics based on the related words and ontology
def calculate_metrics(input_term, ontology):
    related_terms = get_related_words(input_term)
    D = len(related_terms)
    S = sum(1 for term in related_terms if any(string_similarity(term, concept) > 0.8 for concept in ontology))
    O = len(ontology)

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

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python lexical.py <input_term> <ontology_source>")
        sys.exit(1)

    input_term = sys.argv[1]
    ontology_source = sys.argv[2]
    ontology, main_graph = load_ontology(ontology_source)

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
