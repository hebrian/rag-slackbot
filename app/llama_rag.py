from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from config import OPENAI_API_KEY
import os
import phoenix as px
from llama_index.core import set_global_handler

# Start the local Phoenix server UI
px.launch_app()

# Use LlamaIndex's integrated Phoenix handler
set_global_handler("arize_phoenix")


def create_qa_chain(documents=None):
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    # Load ChromaDB from disk
    db = chromadb.PersistentClient(path="./chroma_db")
    collection = db.get_or_create_collection("quickstart")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    #storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Set default LLM and embedding model
    Settings.llm = OpenAI(model="gpt-4o", temperature=0)
    Settings.embed_model = embed_model

    # Build index using implicit Settings
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    # Create query engine from index
    query_engine = index.as_query_engine()

    # Wrap it in a callable object for slack_bot.py
    class QAWrapper:
        def run(self, question: str) -> str:
            return str(query_engine.query(question))

    return QAWrapper()
