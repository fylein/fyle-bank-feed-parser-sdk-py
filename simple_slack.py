from urllib import request, parse
import os
import json

SOLID_SLACK_CHANNEL = os.environ.get('SOLID_SLACK_CHANNEL')
SOLID_SLACK_TOKEN = os.environ.get('SOLID_SLACK_TOKEN')

slack_failure = {
    "ok": False
}

class SimpleSlack:
    execution_slack_thread = None
    messages = []

    @staticmethod
    def post_message_to_slack(text: str):
        if SOLID_SLACK_CHANNEL is None or SOLID_SLACK_TOKEN is None:
            return slack_failure
        try:
            params = {
                'token': SOLID_SLACK_TOKEN,
                'channel': SOLID_SLACK_CHANNEL,
                'text': text
            }
            if SimpleSlack.execution_slack_thread is not None:
                params["thread_ts"] = SimpleSlack.execution_slack_thread

            data = parse.urlencode(params).encode()
            req = request.Request('https://slack.com/api/chat.postMessage', data=data)
            responseObject = request.urlopen(req)

            # Turn to JSON.
            raw_data = responseObject.read()
            encoding = responseObject.info().get_content_charset('utf8')
            response = json.loads(raw_data.decode(encoding))

            if SimpleSlack.execution_slack_thread is None and response["ok"] is True and response["ts"] is not None:
                SimpleSlack.execution_slack_thread = response["ts"]

            return response
        except Exception as e:
            return slack_failure

    @staticmethod
    def add_message_to_slack(text: str):
        SimpleSlack.messages.append(text)

    @staticmethod
    def send_messages_to_slack():
        for message in SimpleSlack.messages:
            SimpleSlack.post_message_to_slack(message)
        # Clean messages queue
        SimpleSlack.messages = []

