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

   This command will compile the project and create a JAR file in the `target` directory for example `fair_ontologies-0.1.0.jar`, in the `target` directory.

4. **Run the Server**:
   Executing the following command will start the server. `PORT` can be replaced with the desired port number (e.g., 8083):
   ```sh
   java -jar -Dserver.port=8083 target/fair_ontologies-0.1.0.jar
   ```

5. **Test the Installation**:
   Once the server is running, sending a request using `curl`, it can be tested:
   ```sh
   curl -X POST "http://localhost:8083/assessOntology" -H "accept: application/json;charset=UTF-8" -H "Content-Type: application/json;charset=UTF-8" -d "{ \"ontologyUri\": \"https://w3id.org/okn/o/sd\"}"
   ```

   
# Running app.py

After successfully running `foopsReuse`, you can proceed with running the `app.py` file to start the web application that allows you to analyze ontologies through a user-friendly interface.

## Steps to Run app.py:

### 1. Navigate to the Project Directory

Open a terminal or command prompt and navigate to the directory where `app.py` is located.

### 2. Ensure Python Dependencies are Installed

Before running the Flask application, ensure that the necessary Python libraries are installed by running:

```sh
pip install rdflib requests owlready2 flask
```

### 3. Start the Flask Application

Run the Flask application by executing:

```sh
python app.py
```

The application will start on `http://127.0.0.1:5000` by default.

### 4. Access the Application

Open a web browser and navigate to `http://127.0.0.1:5000`. You can now upload ontology files or provide ontology URLs to analyze them.

### 5. Test Ontologies

You can test the application with sample ontology URLs provided in `Test.txt`:

```txt
1. https://raw.githubusercontent.com/FZ-HANNOU/Omega-X/main/EventsTimeSeriesOntology/EventsTimeSeriesOntology-1.0.ttl
2. https://saref.etsi.org/saref4ener/v1.2.1/
3. https://ci.mines-stetienne.fr/seas/PhotovoltaicOntology-1.0.ttl
4. https://saref.etsi.org/saref4grid/v1.1.1/saref4grid.ttl
```

### Notes

- **Port Conflict**: Ensure the chosen port (8083 in this example) is not being used by another application.
- **quality.py** will not give the FAIR information without running 'foopsReuse'
