from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import pandas as pd
from constant import *
from tqdm import tqdm
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

public_test = pd.read_csv('./data/public_test.csv')

class NeuralSearcher:
    def __init__(self,client, collection_name):
        self.collection_name = collection_name
        self.client = client
        self.model = SentenceTransformer('bkai-foundation-models/vietnamese-bi-encoder',device = 'cuda')
    def search(self, text: str,limit:int):
        vector = self.model.encode(text).tolist()
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            query_filter=None,  
            limit=limit
        ).points
        payloads = [hit.payload for hit in search_result]
        return payloads

qdrant_client = QdrantClient(qdrant_host)
qdrant_searcher = NeuralSearcher(qdrant_client,qdrant_collection_name)

def combine_search(query, qdrant_searcher, es_client, num_chunks_to_recall=50, semantic_weight=1.0, bm25_weight=1.0, k=10):
    semantic_results = qdrant_searcher.search(query, limit = num_chunks_to_recall)  
    ranked_chunk_ids = [(result['chunk_id'], result['cid']) for result in semantic_results]

    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["content"],  
            }
        },
        "size": num_chunks_to_recall,
    }
    bm25_results = es_client.search(index=es_index_name, body=search_body)['hits']['hits']
    ranked_bm25_chunk_ids = [(result['_source']['chunk_id'], result['_source']['cid']) for result in bm25_results]

    chunk_ids = list(set(ranked_chunk_ids + ranked_bm25_chunk_ids))
    chunk_id_to_score = {}

    for chunk_id in chunk_ids:
        score = 0
        if chunk_id in ranked_chunk_ids:
            index = ranked_chunk_ids.index(chunk_id)
            score += semantic_weight * (1 / (index + 1))  
        if chunk_id in ranked_bm25_chunk_ids:
            index = ranked_bm25_chunk_ids.index(chunk_id)
            score += bm25_weight * (1 / (index + 1))  
        chunk_id_to_score[chunk_id] = score

    sorted_chunk_ids = sorted(chunk_id_to_score.keys(), key=lambda x: chunk_id_to_score[x], reverse=True)

    for index, chunk_id in enumerate(sorted_chunk_ids):
        chunk_id_to_score[chunk_id] = 1 / (index + 1)  

    final_results = []
    semantic_count = 0
    bm25_count = 0
    dem = 0
    set_cids = set()
    while(dem<num_chunks_to_recall and len(set_cids)<k):
        chunk_metadata = (sorted_chunk_ids[dem][0],sorted_chunk_ids[dem][1])
        is_from_semantic = sorted_chunk_ids[dem] in ranked_chunk_ids
        is_from_bm25 = sorted_chunk_ids[dem] in ranked_bm25_chunk_ids
        set_cids.add(chunk_metadata['cid'])
        final_results.append({
            'chunk': chunk_metadata,
            'score': chunk_id_to_score[sorted_chunk_ids[dem]],
            'from_semantic': is_from_semantic,
            'from_bm25': is_from_bm25
        })
        
        if is_from_semantic and not is_from_bm25:
            semantic_count += 1
        elif is_from_bm25 and not is_from_semantic:
            bm25_count += 1
        else:  
            semantic_count += 0.5
            bm25_count += 0.5
        dem+=1
    return final_results, semantic_count, bm25_count,set_cids
total_cids = []
total_final_results = []
print("Start retrieving public test questions")
for q in tqdm(public_test.question):
    final_results, semantic_count, bm25_count,set_cids = combine_search(q, qdrant_searcher, es_client)
    total_cids.append(set_cids)
    total_final_results.append(final_results)

with open('./predict.txt','w') as f:
    for qid,ans in tqdm(zip(public_test['qid'],total_cids)):
        f.write(str(qid)+' '+' '.join(list(map(str,list(ans))))+'\n')
