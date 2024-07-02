# OntoReuse

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
```

## Steps to Build and Run 'foopsReuse' on Local Machine

1. **Prerequisites are Installed**:
   - **Java Development Kit (JDK) 11**: JDK 17, is also fine
   - **Maven**: To build the project.

2. **Build the Project**:
   Open a terminal or command prompt, navigate to the project directory where `pom.xml` is located, and run:
   ```sh
   mvn install
   ```

   This command will compile the project and create a JAR file in the `target` directory.

3. **Locate the JAR File**:
   After the build is complete, you should find the JAR file, for example `fair_ontologies-0.1.0.jar`, in the `target` directory.

4. **Run the Server**:
   Execute the following command to start the server. Replace `PORT` with the desired port number (e.g., 8083):
   ```sh
   java -jar -Dserver.port=8083 target/fair_ontologies-0.1.0.jar
   ```

5. **Test the Installation**:
   Once the server is running, you can test it by sending a request using `curl`:
   ```sh
   curl -X POST "http://localhost:8083/assessOntology" -H "accept: application/json;charset=UTF-8" -H "Content-Type: application/json;charset=UTF-8" -d "{ \"ontologyUri\": \"https://w3id.org/okn/o/sd\"}"
   ```

### Notes

- **Port Conflict**: Ensure the chosen port (8083 in this example) is not being used by another application.
- **quality.py** will not give the FAIR information without running 'foopsReuse'
