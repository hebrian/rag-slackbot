import chromadb
from llama_index.core import (
    VectorStoreIndex,
    Settings,
    StorageContext,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore

from llama_index.core.retrievers import VectorIndexAutoRetriever
from llama_index.core.vector_stores.types import (
    VectorStoreInfo,
    MetadataInfo,
)

# Optional: Phoenix UI for monitoring
import phoenix as px
from llama_index.core import set_global_handler

px.launch_app()
set_global_handler("arize_phoenix")

def create_qa_chain():
    # --- This setup remains the same ---
    # Embedding model
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    # Load Chroma vector store
    db = chromadb.PersistentClient(path="./chroma_db")
    collection = db.get_or_create_collection("quickstart")
    vector_store = ChromaVectorStore(chroma_collection=collection)

    # Configure LLM and embedder
    Settings.llm = OpenAI(model="gpt-4o", temperature=0)
    Settings.embed_model = embed_model

    # Build index from the existing vector store
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    # This is the core of the new approach. We describe our metadata to the LLM.
    vector_store_info = VectorStoreInfo(
        content_info="Information about various youth programs at Chinatown Youth Initiatives (CYI)",
        metadata_info=[
            MetadataInfo(
                name="program",
                type="str",
                description=(
                    "The name of the program. Options include 'SLI' (Summer Leadership Institute), "
                    "'CCB' (Chinatown Community Builders), 'CBD' (Chinatown Beautification Day), "
                    "or 'CLP' (Chinatown Literacy Project)."
                ),
            ),
            MetadataInfo(
                name="year",
                type="int",
                description="The year the program, event, or report took place.",
            ),
            MetadataInfo(
                name="report_type",
                type="str",
                description="The type of document. Options include 'Board Report', 'Teacher Debrief', or 'Other'.",
            ),
        ],
    )

    # This retriever automatically infers filters from the query and the schema.
    retriever = VectorIndexAutoRetriever(
        index,
        vector_store_info=vector_store_info,
        similarity_top_k=5, # Retrieve top 5 most similar nodes after filtering
        verbose=True,      # Set to True to see the inferred filters during queries
    )

    # This replaces the agent for a more direct Q&A experience.
    #query_engine = index.as_query_engine(retriever=retriever)
    from llama_index.core.query_engine import RetrieverQueryEngine
    query_engine = RetrieverQueryEngine(retriever=retriever)

    class QAWrapper:
        def run(self, question: str) -> str:
            # The .query() method is now used instead of .chat()
            response = query_engine.query(question)
            return str(response)

    return QAWrapper()