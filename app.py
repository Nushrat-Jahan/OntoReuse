from flask import Flask, request, render_template, jsonify
import subprocess
import os
import tempfile
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    keyword = request.form['keyword']
    ontology_url = request.form['ontology_url']
    ontology_file = request.files['ontology_file']
    
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = None
        if ontology_file:
            file_path = os.path.join(temp_dir, ontology_file.filename)
            ontology_file.save(file_path)
        
        lexical_result = run_script('lexical.py', keyword, file_path, ontology_url)
        structural_result = run_script('structural.py', None, file_path, ontology_url)
        quality_result = run_script('quality.py', None, file_path, ontology_url)

    return jsonify({
        'lexical_result': lexical_result,
        'structural_result': structural_result,
        'quality_result': quality_result
    })

def run_script(script_name, keyword, file_path, ontology_url):
    args = ['python', script_name]
    if keyword:
        args.append(keyword)
    if file_path:
        args.append(file_path)
    if ontology_url:
        args.append(ontology_url)
    
    result = subprocess.run(args, capture_output=True, text=True)
    return result.stdout

if __name__ == '__main__':
    app.run(debug=True)
