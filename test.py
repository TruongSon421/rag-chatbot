import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm
from elasticsearch import Elasticsearch
from constant import *
from elasticsearch.helpers import bulk
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import torch

from read_data.kotaemon.loaders import *
from llama_index.readers.json import JSONReader
from llama_index.readers.file import PandasCSVReader,PptxReader,UnstructuredReader
def get_extractor(file_name:str):
    map_reader = {"docx": DocxReader(),
        "html": UnstructuredReader(),
        "csv": PandasCSVReader(pandas_config=dict(on_bad_lines="skip")),
        "xlsx": PandasExcelReader(),
        "json": JSONReader(),
        "txt": TxtReader()}
    return map_reader[file_name.split('.')[-1]]

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=256, 
    chunk_overlap=50)

data_dir = 'data'
for file_name in os.listdir(data_dir):
    print(file_name)
    extractor = get_extractor(file_name)
    document = extractor.load_data(os.path.join(data_dir,file_name))
    print(extractor)
    split = text_splitter.split_text(document[0].text)
