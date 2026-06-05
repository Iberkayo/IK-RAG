import os
import json
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("WARNING: OPENAI_API_KEY is not set in .env! Script will fail if attempting to call OpenAI.")

# Configuration
CHUNKS_FILE = r"C:\Users\iberkayo\Desktop\IK-Rag\data\processed\chunks.jsonl"
QDRANT_PATH = r"C:\Users\iberkayo\Desktop\IK-Rag\data\qdrant_db"
COLLECTION_NAME = "hr_copilot_chunks"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536  # text-embedding-3-small dimension

def get_embeddings(texts, client):
    """Fetch embeddings from OpenAI for a batch of texts."""
    try:
        response = client.embeddings.create(
            input=texts,
            model=EMBEDDING_MODEL
        )
        return [data.embedding for data in response.data]
    except Exception as e:
        print(f"Error calling OpenAI Embeddings API: {e}")
        raise

def main():
    if not os.path.exists(CHUNKS_FILE):
        print(f"Chunks file not found at: {CHUNKS_FILE}. Please run ingest.py first.")
        return

    # Initialize OpenAI and Qdrant client
    client = OpenAI(api_key=openai_api_key)
    
    print(f"Initializing Qdrant client at local path: {QDRANT_PATH}...")
    qdrant_client = QdrantClient(path=QDRANT_PATH)

    # Read chunks
    chunks = []
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    if not chunks:
        print("No chunks found to process.")
        return

    print(f"Loaded {len(chunks)} chunks from {CHUNKS_FILE}.")

    # Recreate collection
    print(f"Recreating Qdrant collection: '{COLLECTION_NAME}'...")
    qdrant_client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )

    # Embed and upload in batches
    batch_size = 64
    points = []
    
    print("Generating embeddings and preparing data for Qdrant...")
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c["content"] for c in batch]
        
        print(f"Processing batch {i//batch_size + 1}/{(len(chunks) - 1)//batch_size + 1} (size {len(batch)})...")
        embeddings = get_embeddings(texts, client)
        
        for idx, (chunk, vector) in enumerate(zip(batch, embeddings)):
            point_id = i + idx + 1  # Integer ID for simplicity
            payload = {
                "doc_id": chunk["doc_id"],
                "title": chunk["title"],
                "category": chunk["category"],
                "section": chunk["section"],
                "source_file": chunk["source_file"],
                "chunk_id": chunk["chunk_id"],
                "page": chunk["page"],
                "content": chunk["content"]
            }
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            )

    # Upload to Qdrant
    print(f"Uploading {len(points)} points to collection '{COLLECTION_NAME}'...")
    
    # Upload in chunks of 100 points
    upload_batch_size = 100
    for i in range(0, len(points), upload_batch_size):
        sub_points = points[i:i + upload_batch_size]
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=sub_points
        )
        print(f"Uploaded points {i + 1} to {min(i + upload_batch_size, len(points))}...")

    print(f"Success! Vector database populated. You can find the database files in: {QDRANT_PATH}")

if __name__ == "__main__":
    main()
