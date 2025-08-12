# Slack Setup
> Setting up the Slackbot properly is an essential step for this project. The following walkthrough will guide you on how to setup the Slackbot for development; production configurations may differ slightly.

You can find the official instructions [here](https://api.slack.com/quickstart). I will provide the specific steps that worked for me as reference. 

## OAuth & Permissions
Start by [creating an app](https://api.slack.com/apps) and give it a name. Next, we have to request scopes so you can message your slack app and have it send messages back to you. Naviage to OAuth & Permissions and set the following for your Bot Token Scopes:
- app_mentions:read
- channels:history
- chat:write
- im:history

## Socket Mode
Since this slack app is designed for individual or organization wide-usage rather than be widely distributed, we can go to Socket Mode and enable it. As noted by official documentation, "turning on Socket Mode will route your app’s interactions and events over a WebSockets connection instead of sending these payloads to Request URLs, which are public HTTP endpoints." The following features should be impacted:
- Interactivity & Shortcuts
- Slash Commands
- Event Subscriptions


## Event Subscriptions
Navigate to Event Subscriptions and enable events with Socket Mode. Apps can subscribe to receive events such as new messages in a channel. Configure the following:
- app_mention
- message.im

## Show Tabs
In the App Home section, navigate to Show Tabs. The above configurations allowed us to mention a bot in a channel and message it. In order to message a bot directly as if chatting with another user we need to the Messages Tab is enabled. Without this we won't be to message the bot directly, the message bot would be greyed out!

## Troubleshooting
Here are some links I found helpful for troubleshooting.
- https://github.com/slackapi/python-slack-sdk/issues/1020
- https://github.com/slackapi/python-slack-sdk/issues/1015#issuecomment-842549847


