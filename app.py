from flask import Flask, render_template, request
import lexical
import structural
import quality
import tempfile
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    lexical_result = {}
    structural_result = {}
    quality_result = {}

    if request.method == 'POST':
        ontology_file = request.files.get('ontology_file')
        ontology_url = request.form.get('ontology_url')
        keyword = request.form.get('keyword')

        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                ontology_file.save(temp_file.name)

            ontology_terms, main_graph = lexical.load_ontology(temp_file.name)
            if main_graph:
                lexical_result = lexical.calculate_metrics(keyword, ontology_terms)
                structural_result = structural.evaluate_ontology(main_graph, 0)
                quality_result = quality.evaluate_with_foops(ontology_url)

                # Handle content negotiation (if necessary)
                base_url = ontology_url.rsplit('/', 1)[0] + '/'
                found_formats = quality.check_content_negotiation(base_url)
                quality_result['found_formats'] = found_formats
                quality_result['content_negotiation_score'] = len(found_formats)

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)

    return render_template('index.html', 
                           lexical_result=lexical_result, 
                           structural_result=structural_result, 
                           quality_result=quality_result)

if __name__ == '__main__':
    app.run(debug=True)
