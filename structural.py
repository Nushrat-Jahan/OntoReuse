import sys
import rdflib
from rdflib import Graph, RDF, OWL, RDFS
import requests
import tempfile
from owlready2 import get_ontology, sync_reasoner_pellet, OwlReadyInconsistentOntologyError
import time

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

def load_ontology(source):
    if not source:
        print("No source provided for ontology.")
        return None, 0
    print(f"Loading ontology from source: {source}")
    if source.startswith('http://') or source.startswith('https://'):
        start_time = time.time()
        main_graph = download_and_parse_ontology(source)
        load_time = time.time() - start_time
        base_url = source.rsplit('/', 1)[0] + '/' if main_graph else None
    else:
        base_url = None
        try:
            if source:
                start_time = time.time()
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
                load_time = time.time() - start_time
            else:
                main_graph = None
        except FileNotFoundError:
            print("The file path is not correct. Please provide a valid file path.")
            main_graph = None
            load_time = 0

    if main_graph:
        with tempfile.TemporaryDirectory() as temp_dir:
            if base_url:
                resolve_imports(main_graph, base_url, temp_dir)
            object_properties_count, classes_count = count_elements(main_graph)
            print(f"\nTotal - Object Properties: {object_properties_count}, Classes: {classes_count}")
            return main_graph, load_time
    else:
        print("Failed to load the ontology.")
        return None, 0

def get_classes(graph):
    classes = set(graph.subjects(RDF.type, OWL.Class)).union(set(graph.subjects(RDF.type, RDFS.Class)))
    return classes

def get_properties(graph):
    properties = set(graph.subjects(RDF.type, OWL.ObjectProperty)).union(set(graph.subjects(RDF.type, OWL.DatatypeProperty)))
    return properties

def get_datatype_properties(graph):
    datatype_properties = set(graph.subjects(RDF.type, OWL.DatatypeProperty))
    return datatype_properties

def concept_structure(graph):
    classes = get_classes(graph)
    components_per_class = {}
    for cls in classes:
        components = set(graph.objects(subject=cls, predicate=RDFS.subClassOf))
        components_per_class[cls] = components
    return components_per_class

def relationship_richness(graph):
    object_properties = set(graph.subjects(RDF.type, OWL.ObjectProperty))
    datatype_properties = set(graph.subjects(RDF.type, OWL.DatatypeProperty))
    num_relationships = len(object_properties) + len(datatype_properties)
    num_subclass_relationships = len(list(graph.triples((None, RDFS.subClassOf, None))))
    total_relationships = num_relationships + num_subclass_relationships
    if total_relationships == 0:
        return 0
    relationship_richness = (num_relationships / total_relationships) * 100
    return relationship_richness

def inheritance_richness(graph):
    classes = get_classes(graph)
    subclass_counts = [len(set(graph.subjects(RDFS.subClassOf, cls))) for cls in classes]
    if len(classes) == 0:
        return 0
    inheritance_richness_value = (sum(subclass_counts) / len(classes)) * 100
    return inheritance_richness_value

def inheritance_depth(graph):
    def get_depth(cls, current_depth=0):
        subclasses = set(graph.subjects(RDFS.subClassOf, cls))
        if not subclasses:
            return current_depth
        return max(get_depth(sub, current_depth + 1) for sub in subclasses)
    classes = get_classes(graph)
    depth = max(get_depth(cls) for cls in classes) if classes else 0
    return depth

def count_subclasses(graph):
    classes = get_classes(graph)
    subclass_count = {}
    total_subclasses = 0
    for cls in classes:
        subclasses = set(graph.subjects(RDFS.subClassOf, cls))
        subclass_count[cls] = len(subclasses)
        total_subclasses += len(subclasses)
    avg_subclasses_per_class = total_subclasses / len(classes) if len(classes) > 0 else 0
    return subclass_count, total_subclasses, avg_subclasses_per_class

def count_roots_leaves(graph):
    classes = get_classes(graph)
    roots = set(cls for cls in classes if not list(graph.objects(subject=cls, predicate=RDFS.subClassOf)))
    leaves = set(cls for cls in classes if not list(graph.subjects(RDFS.subClassOf, cls)))
    return len(roots), len(leaves)

def average_depth_of_inheritance_tree(graph):
    def get_all_paths_to_leaves(cls, current_path):
        subclasses = list(graph.subjects(RDFS.subClassOf, cls))
        if not subclasses:
            return [current_path]
        paths = []
        for sub in subclasses:
            paths.extend(get_all_paths_to_leaves(sub, current_path + [sub]))
        return paths

    classes = get_classes(graph)
    root_classes = [cls for cls in classes if not list(graph.objects(cls, RDFS.subClassOf))]
    all_paths = []
    
    for root in root_classes:
        all_paths.extend(get_all_paths_to_leaves(root, [root]))

    if not all_paths:
        return 0

    total_depth = sum(len(path) - 1 for path in all_paths)
    return (total_depth / len(all_paths)) * 100

def check_consistency(graph):
    try:
        temp_owl_path = tempfile.NamedTemporaryFile(suffix=".owl", delete=False).name
        graph.serialize(destination=temp_owl_path, format='xml')
        ontology = get_ontology(f"file://{temp_owl_path}").load()
        try:
            start_time = time.time()
            sync_reasoner_pellet(infer_property_values=True)
            reasoning_time = time.time() - start_time
            return 1, reasoning_time  # Consistent
        except OwlReadyInconsistentOntologyError:
            return 0, 0  # Inconsistent
    except Exception as e:
        print(f"Error during consistency check: {e}")
        return 0, 0

def execute_queries(graph):
    queries = [
        """
        SELECT ?class WHERE {
            ?class a owl:Class .
        }
        """,
        """
        SELECT ?property WHERE {
            ?property a owl:ObjectProperty .
        }
        """,
        """
        SELECT ?subject ?predicate ?object WHERE {
            ?subject ?predicate ?object .
        } LIMIT 100
        """
    ]
    query_times = []
    for query in queries:
        start_time = time.time()
        list(graph.query(query))
        query_times.append(time.time() - start_time)
    return query_times


def evaluate_ontology(graph, load_time):
    concept_structure_result = concept_structure(graph)
    relationship_richness_result = relationship_richness(graph)
    inheritance_richness_result = inheritance_richness(graph)
    inheritance_depth_result = inheritance_depth(graph)
    subclass_count_result, total_subclasses, avg_subclasses_per_class = count_subclasses(graph)
    num_roots, num_leaves = count_roots_leaves(graph)
    avg_depth_leaves = average_depth_of_inheritance_tree(graph)
    consistency_result, reasoning_time = check_consistency(graph)
    query_times = execute_queries(graph)
    
    object_properties = set(graph.subjects(RDF.type, OWL.ObjectProperty))
    datatype_properties = get_datatype_properties(graph)
    total_properties = len(object_properties) + len(datatype_properties)
    
    # Prepare a dictionary to store all results
    structural_result = {
        "Relationship Richness": f"{relationship_richness_result:.2f}%",
        "Inheritance Richness": f"{inheritance_richness_result:.2f}%",
        "Sum of the number of subclasses": total_subclasses,
        "Average number of subclasses per class": avg_subclasses_per_class,
        "Inheritance Depth": inheritance_depth_result,
        "Number of object properties": len(object_properties),
        "Number of datatype properties": len(datatype_properties),
        "Total number of relationships (properties)": total_properties,
        "Number of Roots (NoR)": num_roots,
        "Number of Leaves (NoL)": num_leaves,
        "Average Depth of Inheritance Tree of Leaf Nodes (ADIT-LN)": f"{avg_depth_leaves:.2f}%",
        "Consistency": consistency_result,
        "Time to load ontology": f"{load_time:.4f} seconds",
        "Time to perform reasoning": f"{reasoning_time:.4f} seconds",
        "Time to execute query 1": f"{query_times[0]:.4f} seconds",
        "Time to execute query 2": f"{query_times[1]:.4f} seconds",
        "Time to execute query 3": f"{query_times[2]:.4f} seconds",
    }
    
    return structural_result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python structural.py <ontology_source>")
        sys.exit(1)

    ontology_source = sys.argv[1]
    graph, load_time = load_ontology(ontology_source)

    if graph:
        structural_result = evaluate_ontology(graph, load_time)
        for key, value in structural_result.items():
            print(f"{key}: {value}")
    else:
        print("No ontology loaded.")