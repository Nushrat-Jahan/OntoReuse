# OntologyReuseToolkit

## Overview
The OntologyReuseToolkit is designed to evaluate and suggest ontologies for reuse. This tool streamlines the selection process for engineers by assessing factors such as structure, lexicon, and maturity of ontologies.

## Features
- Load ontologies from local files or URLs.
- Evaluate the structure of ontologies, including the number of classes and object properties.
- Calculate metrics such as Relationship Richness, Inheritance Richness, and Average Depth of Inheritance Tree of Leaf Nodes.
- Check ontology consistency using a reasoner.
- Suggest related terms using the Datamuse API.
- Calculate domain coverage and ontology relevance based on user-provided terms.

## Installation

To run the OntologyReuseToolkit, the following Python libraries needs to be installed:

1. **rdflib**: For handling RDF graphs.
2. **requests**: For making HTTP requests.
3. **tkinter**: For creating GUI dialogs (included with the standard Python library).
4. **tempfile**: For managing temporary files (included with the standard Python library).
5. **owlready2**: For ontology manipulation and reasoning.
6. **difflib**: For comparing sequences (included with the standard Python library).

### Install External Libraries

Commands to run in the terminal or command prompt:

```sh
pip install rdflib requests owlready2
