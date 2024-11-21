#!/bin/bash
python get_qdrant_embeds.py
python ingest_data.py
python retrieve.py
