import os
import tempfile
import shutil  # Import shutil for removing directories
from flask import Flask, jsonify, request, render_template
from elasticsearch import Elasticsearch
from datetime import datetime
import PyPDF2
import docx
from langchain.text_splitter import RecursiveCharacterTextSplitter

from read_data.kotaemon.loaders import *
from llama_index.readers.json import JSONReader
from llama_index.readers.file import PandasCSVReader, UnstructuredReader

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=256,
    chunk_overlap=50
)

def get_extractor(file_name: str):
    map_reader = {
        "docx": DocxReader(),
        "html": UnstructuredReader(),
        "csv": PandasCSVReader(pandas_config=dict(on_bad_lines="skip")),
        "xlsx": PandasExcelReader(),
        "json": JSONReader(),
        "txt": TxtReader()
    }
    return map_reader[file_name.split('.')[-1]]

app = Flask(__name__)
es = Elasticsearch('https://localhost:9200', basic_auth=("elastic", "UOle-KXo9zL3zn8gW-aQ"), verify_certs=False)

def create_index(index_name='documents'):
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body={
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "topic": {"type":"text"},
                    "datetime": {"type":"text"}
                }
            }
        })
@app.route('/home', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_documents():
    files = request.files.getlist('files')
    index_name = request.form.get('index_name', 'documents')
    topic = request.form.get('topic','general')
    if len(files) == 0:
        return jsonify({"error": "No files uploaded"}), 400

    temp_dir = tempfile.mkdtemp()
    print(f"Temporary directory created at: {temp_dir}")
    
    try:
        for file in files:
            temp_file_path = os.path.join(temp_dir, file.filename)
            file.save(temp_file_path)

            title = file.filename
            try:
                print(f"Processing file: {file.filename}")
                extractor = get_extractor(title)
                document = extractor.load_data(temp_file_path)  
                splits = text_splitter.split_text(document[0].text)
            except Exception as e:
                return jsonify({"error": f"Unsupported file type: {title}"}), 400

            for split in splits:
                body = {
                    'title': title,
                    'content': split,
                    "topic": topic,
                    "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                try:
                    es.index(index=index_name, body=body)
                except Exception as e:
                    return jsonify({"error": f"Failed to upload file {title}: {str(e)}"}), 500

        return jsonify({"message": f"{len(files)} document(s) uploaded successfully!"}), 201
    finally:
        shutil.rmtree(temp_dir)
        print(f"Temporary directory {temp_dir} deleted")

@app.route('/search', methods=['POST'])
def search_documents():
    keyword = request.form['keyword']
    index_name = request.form.get('index_name', 'documents')

    body = {
        "query": {
            "multi_match": {
                "query": keyword,
                "fields": ["content", "title"]
            }
        }
    }

    try:
        res = es.search(index=index_name, body=body)
        return jsonify(res['hits']['hits'])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    create_index()
    app.run(port=5000, debug=True)
