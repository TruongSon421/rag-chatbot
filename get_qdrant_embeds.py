import torch
from sentence_transformers import SentenceTransformer
import numpy as np
import json
import pandas as pd
from tqdm import tqdm
import pandas as pd
corpus = pd.read_csv('./data/corpus.csv')
from langchain.text_splitter import RecursiveCharacterTextSplitter
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=256, 
    chunk_overlap=50)


model = SentenceTransformer('bkai-foundation-models/vietnamese-bi-encoder',device = 'cuda')

all_features = []
print("Start encoding corpus to ingest to Qdrant")
for chunks in tqdm(corpus.text):
    embeddings = model.encode(chunks)

    all_features.append(embeddings)
    
torch.save(all_features,'./data/full_embed.pt')