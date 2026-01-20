#!/usr/bin/env python3
"""
Document Indexer for D365 Documentation
Reads markdown files, chunks them, generates embeddings, and stores in Qdrant.
"""

import os
import glob
from pathlib import Path
from typing import Generator
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
import hashlib
import argparse

# Configuration
D365_DOCS_PATH = "/Users/bradyswanson2/D365 LLM Knowledge Base"
QDRANT_PATH = "./qdrant_storage"
COLLECTION_NAME = "d365_docs"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def get_all_markdown_files(base_path: str) -> list[str]:
    """Get all markdown files recursively."""
    return glob.glob(os.path.join(base_path, "**/*.md"), recursive=True)

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
        if start < 0:
            break
    return chunks

def generate_embedding(client: OpenAI, text: str) -> list[float]:
    """Generate embedding for text."""
    response = client.embeddings.create(
        input=text[:8000],  # Truncate to avoid token limits
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

def generate_id(source: str, chunk_idx: int) -> str:
    """Generate deterministic ID from source and chunk index."""
    content = f"{source}:{chunk_idx}"
    return hashlib.md5(content.encode()).hexdigest()

def index_documents(test_mode: bool = False, max_docs: int = 10):
    """Index all D365 markdown documents."""
    
    # Initialize clients
    openai_client = OpenAI()
    qdrant = QdrantClient(path=QDRANT_PATH)
    
    # Create collection if it doesn't exist
    collections = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION_NAME not in collections:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )
        print(f"Created collection: {COLLECTION_NAME}")
    
    # Get all markdown files
    files = get_all_markdown_files(D365_DOCS_PATH)
    print(f"Found {len(files)} markdown files")
    
    if test_mode:
        files = files[:max_docs]
        print(f"Test mode: processing only {len(files)} files")
    
    # Process files
    points = []
    total_chunks = 0
    
    for i, filepath in enumerate(files):
        try:
            # Read file
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Get relative path for source
            rel_path = os.path.relpath(filepath, D365_DOCS_PATH)
            
            # Chunk the content
            chunks = chunk_text(content)
            
            for chunk_idx, chunk in enumerate(chunks):
                # Generate embedding
                embedding = generate_embedding(openai_client, chunk)
                
                # Create point
                point_id = generate_id(rel_path, chunk_idx)
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "source": rel_path,
                        "content": chunk,
                        "chunk_index": chunk_idx
                    }
                )
                points.append(point)
                total_chunks += 1
            
            # Batch upsert every 100 points
            if len(points) >= 100:
                qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
                print(f"Indexed {i+1}/{len(files)} files ({total_chunks} chunks)")
                points = []
                
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            continue
    
    # Final upsert
    if points:
        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    
    print(f"\nDone! Indexed {total_chunks} chunks from {len(files)} files.")
    print(f"Qdrant storage location: {QDRANT_PATH}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index D365 documentation")
    parser.add_argument("--test-mode", action="store_true", help="Only index 10 files for testing")
    parser.add_argument("--max-docs", type=int, default=10, help="Max docs in test mode")
    args = parser.parse_args()
    
    index_documents(test_mode=args.test_mode, max_docs=args.max_docs)
