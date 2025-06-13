import logging
#from document_loader import load_documents # Uncomment if using Langchain for document loading
#from qa_chain import create_qa_chain # Uncomment if using Langchain for QA chain creation
from slack_bot import start_slackbot
from llama_rag import create_qa_chain as create_llama_qa_chain

logging.basicConfig(level=logging.INFO)

def main():
    logging.info("Loading documents...")
    #documents = load_documents() # Langchain only
    logging.info("Documents loaded.")

    logging.info("Creating QA chain...")
    #qa = create_qa_chain(documents) # Pass documents if using Langchain
    qa = create_llama_qa_chain()  # LlamaIndex version, no documents needed
    logging.info("QA chain created.")

    # Start the Slack bot
    logging.info("Launching Slack bot...")
    start_slackbot(qa)

if __name__ == "__main__":
    main()
