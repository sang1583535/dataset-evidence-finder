#!/bin/bash

echo "Starting backend..."
cd backend
uvicorn app.main:app --reload --port 8000 &

cd ../frontend
echo "Starting frontend..."
streamlit run app.py