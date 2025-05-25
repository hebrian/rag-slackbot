from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from config import OPENAI_API_KEY

def create_qa_chain(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=100)
    texts = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    db = Chroma.from_documents(texts, embeddings)  # Consider using persist_directory here
    retriever = db.as_retriever()

    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-2024-08-06", openai_api_key=OPENAI_API_KEY)
    return RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
