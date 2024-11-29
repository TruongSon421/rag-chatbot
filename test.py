from elasticsearch import Elasticsearch

es = Elasticsearch('https://localhost:9200', basic_auth=("elastic", "*VHP8vPHOY4tI5yVad_n"), verify_certs=False)

response = es.search(index='tiendoan', body={
    "query": {
        "match_all": {}
    },
    "size": 10  
})

for hit in response['hits']['hits']:
    print(hit["_source"])  