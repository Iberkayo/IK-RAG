import os
from dotenv import load_dotenv

# Load env variables from root directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
QDRANT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "qdrant_db"))
COLLECTION_NAME = "hr_copilot_chunks"
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o"  # GPT-4o family for V1
