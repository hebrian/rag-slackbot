import chromadb
from llama_index.core import (
    VectorStoreIndex,
    Settings,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore

# Auto-retriever imports
from llama_index.core.retrievers import VectorIndexAutoRetriever
from llama_index.core.vector_stores.types import (
    VectorStoreInfo,
    MetadataInfo,
)

# Agent imports
from llama_index.core.tools import FunctionTool
from llama_index.agent.openai import OpenAIAgent

# Optional: Phoenix UI
import phoenix as px
from llama_index.core import set_global_handler

px.launch_app()
set_global_handler("arize_phoenix")

def create_qa_chain():
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    # Load ChromaDB from disk
    db = chromadb.PersistentClient(path="./chroma_db")
    collection = db.get_or_create_collection("quickstart")
    vector_store = ChromaVectorStore(chroma_collection=collection)

    # Configure LLM and embedding model
    Settings.llm = OpenAI(model="gpt-4o", temperature=0)
    Settings.embed_model = embed_model

    # Build index using the vector store
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    # Set up the vector store information for auto-retriever
    vector_store_info = VectorStoreInfo(
        content_info="Information about CYI programs and reports",
        metadata_info=[
            MetadataInfo(
                name="program",
                type="str",
                description="The program name: 'SLI', 'CCB', 'CBD', 'CLP', etc."
            ),
            MetadataInfo(
                name="year",
                type="int",
                description="The year the document or report is from."
            ),
        ],
    )

    auto_retriever = VectorIndexAutoRetriever(
        index=index,
        vector_store_info=vector_store_info,
        similarity_top_k=5,
        verbose=True,
    )

    # Wrap the auto-retriever in a FunctionTool
    # This tool will be used by the agent to retrieve documents based on user queries
    retrieval_tool = FunctionTool.from_defaults(
        fn=lambda query: "\n\n".join(
            [n.get_content() for n in auto_retriever.retrieve(query)]
        ),
        name="CYIAutoRetriever",
        description="Retrieve CYI documents based on user queries. Supports filtering by program and year automatically."
    )

    # Create the OpenAI agent with the auto-retriever tool
    agent = OpenAIAgent.from_tools(
        tools=[retrieval_tool],
        llm=Settings.llm,
        system_prompt="""
        You are a helpful assistant for Chinatown Youth Initiatives (CYI).
        When the user asks questions, use the CYIAutoRetriever tool to retrieve documents.
        If the user asks follow-up questions (e.g., "what about 2022?"), infer context from the prior query.
        For example if the user asks "What was the major feedback from SLI 2024?" and then "What about 2022?",
        you should understand that the user is asking about the same program (SLI) but for a different year (2022).
        Always synthesize retrieved content into a clear, concise answer.
        If you cannot find relevant documents, politely ask the user to clarify the program or year.
        """,
        verbose=True,
    )

    # Wrap the agent in a QAWrapper
    class QAWrapper:
        def run(self, question: str) -> str:
            response = agent.chat(question)
            return str(response)

    return QAWrapper()