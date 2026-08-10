#!/bin/bash
# Start FastAPI backend in background
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit frontend on port 8501 (exposed to Hugging Face / Web)
streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0
