import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm
from llama_index.core import Document
from elasticsearch import Elasticsearch
from constant import *
from elasticsearch.helpers import bulk
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import torch

# PREPARE DATA

corpus = pd.read_csv('./data/corpus.csv')
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=256, 
    chunk_overlap=50)

chunked_corpus = []
for text in tqdm(corpus.text):
    chunked_corpus.append(text_splitter.split_text(text))
    
total_chunks = []
chunked_documents = []
count = 0
for chunks,cid in tqdm((zip(chunked_corpus,corpus.cid))):
    for chunk in chunks:
        chunked_documents.append(Document(text=chunk,metadata={'cid':cid,'chunk_id':count}))
        total_chunks.append(chunk)
        count+=1

# INGEST TO ELASTICSEARCH

es_client = Elasticsearch(es_host)
if not es_client.indices.exists(index=es_index_name):
    es_client.indices.create(
        index=es_index_name,
        body={
            "mappings": {   
                "properties": {
                    "content": {"type": "text"},
                    "cid": {"type": "text"},
                    "chunk_id":{"type":"text"}
                }
            }
        }
    )
    
actions = [
            {
                "_index": es_index_name,
                "_source": {
                    "content": doc.text,
                    "cid": doc.metadata['cid'],
                    "chunk_id": doc.metadata['chunk_id']
                },
            }
            for doc in tqdm(chunked_documents)
        ]

success, _ = bulk(es_client, actions)
if success:
    print("Indexed documents successfully !")

es_client.indices.refresh(index=es_index_name)

# INGEST TO QDRANT

embeds = torch.load('./data/full_embed.pt')
payload = []
vectors = []
count = 0
for chunks,cid in tqdm(zip(embeds,corpus.cid)):
    for chunk in chunks:
        vectors.append(chunk)
        payload.append({'cid':cid,'chunk_id':count})
        count+=1

qdrant_client = QdrantClient(qdrant_host)

if not qdrant_client.collection_exists(qdrant_collection_name):
    qdrant_client.create_collection(
        collection_name=qdrant_collection_name,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE,on_disk=True),
    )
    
qdrant_client.upload_collection(
    collection_name=qdrant_collection_name,
    vectors=vectors,
    payload=payload,
    ids=None,  
    batch_size=256,  
)
    