from flask import Blueprint, jsonify, request
from models import db, Admin, User, Document, Chunk
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from read_data.kotaemon.loaders import *
from llama_index.readers.json import JSONReader
from llama_index.readers.file import PandasCSVReader, UnstructuredReader
import tempfile
import os
from elasticsearch import Elasticsearch

es = Elasticsearch('https://localhost:9200', basic_auth=("elastic", "*VHP8vPHOY4tI5yVad_n"), verify_certs=False)
crud_blueprint = Blueprint('crud', __name__)
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

@crud_blueprint.route('/user', methods=['POST'])
def create_user():
    data = request.form
    user = User(username=data['username'], email=data['email'], password=data['password'])
    db.session.add(user)
    index_name = data['username']
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body={
            "mappings": {
                "properties": {
                    "document_id": {"type": "integer"},
                    "chunk_order": {"type": "integer"},
                    "content": {"type":"text"},
                }
            }
        })
    db.session.commit()
    return jsonify({"message": f"User {user.username} created successfully!"}), 201

# Read User
@crud_blueprint.route('/user/<int:id>', methods=['GET'])
def read_user(id):
    user = User.query.get(id)
    if user:
        return jsonify({"id": user.id, "username": user.username, "email": user.email, "created_at": user.created_at})
    return jsonify({"error": "User not found"}), 404

# Update User
@crud_blueprint.route('/user/<int:id>', methods=['PUT'])
def update_user(id):
    data = request.form
    user = User.query.get(id)
    if user:
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.password = data.get('password', user.password)
        db.session.commit()
        return jsonify({"message": f"User {user.username} updated successfully!"})
    return jsonify({"error": "User not found"}), 404

# Delete User
@crud_blueprint.route('/user/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": f"User {user.username} deleted successfully!"})
    return jsonify({"error": "User not found"}), 404

# Create Document
@crud_blueprint.route('/document', methods=['POST'])
def create_document():
    data = request.form
    files = request.files.getlist('files')
    temp_dir = tempfile.mkdtemp()
    for file in files:
        temp_file_path = os.path.join(temp_dir, file.filename)
        file.save(temp_file_path)
        try:
            print(f"Processing file: {file.filename}")
            extractor = get_extractor(file.filename)
            document = extractor.load_data(temp_file_path)  
            splits = text_splitter.split_text(document[0].text)
        except Exception as e:
            return jsonify({"error": f"Unsupported file type: {file.filename}"}), 400
         
        document = Document(
            title=data['title'],filename=file.filename, content=document[0].text, topic=data['topic'],creator_id=data['creator_id']
        )
        
        db.session.add(document)
        db.session.flush()
        for idx,split in enumerate(splits):
            body = {
                'document_id': int(document.id),
                'chunk_order': idx+1,
                "content": split,
            }
            try:
                print(User.query.get(int(data['creator_id'])).username)
                es.index(index=User.query.get(int(data['creator_id'])).username, body=body,id = f'{document.id}_{idx+1}')
            except Exception as e:
                return jsonify({"error": f"Failed to upload chunk of {file.filename}: {str(e)}"}), 500
    db.session.commit()
    return jsonify({"message": f"Document {document.title} created successfully!"}), 201

# Read Document
@crud_blueprint.route('/document/<int:id>', methods=['GET'])
def read_document(id):
    document = Document.query.get(id)
    if document:
        return jsonify({
            "id": document.id, "title": document.title, "content": document.content,
            "topic": document.topic, "creator_id": document.creator_id, "created_at": document.created_at
        })
    return jsonify({"error": "Document not found"}), 404

# Update Document
@crud_blueprint.route('/document/<int:id>', methods=['PUT'])
def update_document(id):
    data = request.form
    document = Document.query.get(id)
    if document:
        document.title = data.get('title', document.title)
        document.content = data.get('content', document.content)
        document.topic = data.get('topic', document.topic)
        db.session.commit()
        return jsonify({"message": f"Document {document.title} updated successfully!"})
    return jsonify({"error": "Document not found"}), 404

# Delete Document
@crud_blueprint.route('/document/<int:id>', methods=['DELETE'])
def delete_document(id):
    document = Document.query.get(id)
    if document:
        db.session.delete(document)
        db.session.commit()
        return jsonify({"message": f"Document {document.title} deleted successfully!"})
    return jsonify({"error": "Document not found"}), 404
