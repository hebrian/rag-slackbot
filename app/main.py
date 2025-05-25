import logging
from document_loader import load_documents
from qa_chain import create_qa_chain
from slack_bot import start_slackbot

logging.basicConfig(level=logging.INFO)

def main():
    logging.info("Loading documents...")
    documents = load_documents()
    logging.info("Documents loaded.")

    logging.info("Creating QA chain...")
    qa = create_qa_chain(documents)

    logging.info("Launching Slack bot...")
    start_slackbot(qa)

if __name__ == "__main__":
    main()
