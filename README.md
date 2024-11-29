```
pip install -r requirements.txt
```

```
docker compose up elasticsearch
```

Create new username and password 
```
docker exec -it elasticsearch sh
bin/elasticsearch-reset-password -u elastic
```
Paste password in flash_app.py elasticsearch basic_auth
```
python flask_app.py
```