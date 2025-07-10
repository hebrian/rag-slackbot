from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
#from llama_index.tools import QueryEngineTool
from llama_index.core.tools import QueryEngineTool
#from llama_index.agent_openai import OpenAIAgent  # <-- agent import
from llama_index.agent.openai import OpenAIAgent
import chromadb

# Optional: Phoenix UI for monitoring
import phoenix as px
from llama_index.core import set_global_handler

px.launch_app()
set_global_handler("arize_phoenix")

def create_qa_chain(documents=None):
    # Embedding model
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    # Load Chroma vector store
    db = chromadb.PersistentClient(path="./chroma_db")
    collection = db.get_or_create_collection("quickstart")
    vector_store = ChromaVectorStore(chroma_collection=collection)

    # Configure LLM and embedder
    Settings.llm = OpenAI(model="gpt-4o", temperature=0)
    Settings.embed_model = embed_model

    # Build index and query engine
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    query_engine = index.as_query_engine(similarity_top_k=5)

    # Create retrieval tool wrapping the index
    retrieval_tool = QueryEngineTool.from_defaults(
        query_engine=query_engine,
        description="Retrieve CYI documents. Supports filtering by metadata fields like year and program.",
    )

    # Create the agent with tool and LLM
    agent = OpenAIAgent.from_tools(
        tools=[retrieval_tool],
        llm=Settings.llm,
        system_prompt="""
    You are a helpful assistant for CYI. When retrieving documents:
    - If the user specifies a year (e.g., 2024), apply a metadata filter for year=2024.
    - Only return chunks relevant to the specified program and year.
    - If no year is specified, return the most relevant chunks.
    - If the user asks for a specific program, filter results by that program.
    - Synthesize the retrieved chunks into a concise answer.
    """,
    )


    # Wrapper to match Slackbot interface
    class QAWrapper:
        def run(self, question: str) -> str:
            response = agent.chat(question)
            return str(response)

    return QAWrapper()
