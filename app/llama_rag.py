from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_index.core.tools import FunctionTool
from llama_index.agent.openai import OpenAIAgent
import chromadb

# Imports for metadata filtering
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

# Optional: Phoenix UI for monitoring
import phoenix as px
from llama_index.core import set_global_handler

px.launch_app()
set_global_handler("arize_phoenix")

def create_qa_chain():
    # Embedding model
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    # Load Chroma vector store
    db = chromadb.PersistentClient(path="./chroma_db")
    collection = db.get_or_create_collection("quickstart")
    vector_store = ChromaVectorStore(chroma_collection=collection)

    # Configure LLM and embedder
    Settings.llm = OpenAI(model="gpt-4o", temperature=0)
    Settings.embed_model = embed_model

    # Build index from the vector store
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    def retrieve_cyi_documents(query: str, program: str = None, year: int = None) -> str:
        """
        Retrieve CYI documents.
        - query (str): The user's question.
        - program (str): Optional. Filter results by a specific program (e.g., 'SLI', 'CCB').
        - year (int): Optional. Filter results by a specific year (e.g., 2023, 2024).
        """
        print(f"Retrieving for query: '{query}', program: {program}, year: {year}") # For debugging
        
        filter_list = []
        if program:
            filter_list.append(ExactMatchFilter(key="program", value=program))
        if year:
            # ChromaDB can be particular about types. Let's ensure year is an int.
            filter_list.append(ExactMatchFilter(key="year", value=int(year)))

        # Only create the MetadataFilters object if there are filters to apply
        query_filters = MetadataFilters(filters=filter_list) if filter_list else None

        # Create the retriever here, applying filters at creation time
        retriever = index.as_retriever(
            similarity_top_k=5,
            filters=query_filters
        )
        
        # The retriever will use the filters to retrieve relevant documents
        nodes = retriever.retrieve(query)
        
        # Add a check for empty results for better feedback
        if not nodes:
            return "No documents found matching the specified criteria."
            
        return "\n\n".join([n.get_content() for n in nodes])

    # Define the tool for the agent
    # This tool will be used to retrieve documents based on user queries
    retrieval_tool = FunctionTool.from_defaults(
        fn=retrieve_cyi_documents,
        name="CYIDocumentRetriever",
        description="Retrieve CYI documents. Use this to answer questions about specific programs and years."
    )

    agent = OpenAIAgent.from_tools(
        tools=[retrieval_tool],
        llm=Settings.llm,
        system_prompt="""
        You are a helpful assistant for Chinatown Youth Initiatives (CYI).
        Your goal is to answer user questions based on the documents you can retrieve.
        When a user asks a question, identify if they mention a specific program (like 'SLI' or 'CCB') or a year.
        Use the CYIDocumentRetriever tool and pass the identified program and year as arguments to get the most relevant information.
        After retrieving the information, synthesize it into a concise and clear answer.
        If the tool returns that no documents were found, inform the user clearly.
        """,
        verbose=True
    )
    
    # Wrapper to match Slackbot interface
    class QAWrapper:
        def run(self, question: str) -> str:
            response = agent.chat(question)
            return str(response)

    return QAWrapper()