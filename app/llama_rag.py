from urllib import response
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
        similarity_top_k=8,
        verbose=True,
    )

    def retrieve_chunks(query: str) -> str:
        # Retrieve relevant chunks from the auto-retriever and summarize them
        nodes = auto_retriever.retrieve(query)
        chunks =  [
            {
                "text": node.get_content(),
                "metadata": node.metadata,
                "score": node.score
            }
            for node in nodes
        ]
        return summarize_chunks(chunks, query)

    # Wrap the auto-retriever in a FunctionTool
    # This tool will be used by the agent to retrieve documents based on user queries
    retrieve_summarize_tool = FunctionTool.from_defaults(
        fn=retrieve_chunks,
        name="CYIDocQA",
        description="Answer questions from CYI documents by retrieving and summarizing relevant metadata and content."
    )

    def summarize_chunks(chunks_or_rows: list, question: str):
        # Create a context string from the retrieved chunks or rows
        # Handle both text chunks or SQL row dicts
        if isinstance(chunks_or_rows[0], dict):
            # SQL rows: format into a string table as needed
            context = "\n".join(
                ", ".join(f"{k}: {v}" for k, v in row.items()) for row in chunks_or_rows
            )
        else:
            # Text chunks (fallback)
            context = "\n\n".join([c["text"] for c in chunks_or_rows])

        prompt = f"""
        You are helping answer user questions about CYI documents.
        Context:
        {context}

        Question: {question}
        Provide a concise, clear answer based on the context.
        """
        return Settings.llm.complete(prompt).text
    

    from llama_index.core import SQLDatabase
    from llama_index.core.query_engine import NLSQLTableQueryEngine
    from sqlalchemy import create_engine

    # Connect to your SQLite database
    engine = create_engine("sqlite:///cyi_directory.db")
    sql_database = SQLDatabase(engine, include_tables=["Alumni"])

    from llama_index.core.prompts import PromptTemplate

    custom_sql_prompt = PromptTemplate(
        """You are an expert at writing SQL queries. 
        Here is the database schema:
        {schema}
        For the 'Alumni' table in the CYI directory database,
        here are few things to keep in mind:
        
        Guidelines:
        - "CYI" refers to the organization; do NOT filter Program = 'CYI'.
        - "Chinatown Beautification Day" means Program = 'CBD'.
        - "Chinatown Community Builders" means Program = 'CCB'.
        - "Summer Leadership Institute" means Program = 'SLI'.
        - "Community Leadership Program" means Program = 'CLP'.
        - "Alumni" refers to contacts in any of the CYI programs.
        - If the user says "CYI programs", "CYI" or "programs in CYI", you should query SLI, CCB, CBD, and CLP.
        - If the user asks about "staff", map that to roles: Director, Coordinator, Facilitator, Community Mentor.
        - Participants are not part of "staff".

        Examples:
        Q: Who are the staff for SLI 2020?
        A: SELECT * FROM Alumni WHERE Program = 'SLI' AND Year = 2020 AND Role IN ('Director', 'Coordinator', 'Facilitator', 'Community Mentor')

        Q: Who are the coordinators for CYI in 2023?
        A: SELECT * FROM Alumni WHERE Year = 2023 AND Role = 'Coordinator'

        Output instructions:
        - ONLY return the raw SQL query.
        - Do NOT include explanations, preambles, markdown formatting, or commentary.
        - Your response must start with SELECT or WITH.

        User Question: {query_str}
        SQL Query:"""
    )

    # Create a query engine that handles natural language to SQL
    sql_query_engine = NLSQLTableQueryEngine(
        sql_database=sql_database,
        tables=["Alumni"],
        llm=Settings.llm,
        text_to_sql_prompt=custom_sql_prompt,
        sql_output_key="sql_query",
    )

    def sql_query_fn(user_query: str) -> str:
        response = sql_query_engine.query(user_query)
        sql_query_str = response.metadata.get("sql_query", "[No SQL generated]")
        rows = response.metadata.get("result", [])
        
        print("\n Generated SQL Query:")
        print(sql_query_str)
        return str(response)
        #return summarize_chunks(rows, user_query)

    sql_summary_tool = FunctionTool.from_defaults(
        fn=sql_query_fn,
        name="CYIDirectoryQA",
        description="Answer questions using CYI directory data by querying and summarizing results.",
    )


    # Create the OpenAI agent with the auto-retriever tool
    agent = OpenAIAgent.from_tools(
        tools=[retrieve_summarize_tool, sql_summary_tool],
        llm=Settings.llm,
        system_prompt="""
        You are a helpful assistant for Chinatown Youth Initiatives (CYI).
        - Use CYIDirectoryQA to answer questions about alumni, programs, years, roles, and emails.
        - Use CYIDocQA for answering questions from reports or documents.
        - Prefer CYIDirectoryQA for structured questions (e.g., "Who were the directors for SLI 2020?")
        - If no relevant documents or answers are found, politely inform the user and ask for clarification.
        - If the user asks follow-up questions (e.g., "what about 2022?"), infer context from the prior question.
        For example if the user asks "What was the major feedback from SLI 2024?" and then "What about 2022?",
        you should understand that the user is asking about the same program (SLI) but for a different year (2022).
        """,
        verbose=True,
    )

    # Wrap the agent in a QAWrapper
    class QAWrapper:
        def run(self, question: str) -> str:
            response = agent.chat(question)
            return str(response)

    return QAWrapper()