import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN

def start_slackbot(qa):
    app = App(token=SLACK_BOT_TOKEN)

    @app.message("")
    def handle_message(message, say, logger):
        query = message.get('text', '')
        logger.debug(f"Received query: {query}")
        try:
            response = qa.run(query)
            say(response)
        except Exception as e:
            logger.error(f"Error: {e}")
            say(f"Error: {e}")

    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    logging.info("Starting Slack bot...")
    handler.start()
