from urllib import request, parse
import os
import json

SOLID_SLACK_CHANNEL = os.environ['SOLID_SLACK_CHANNEL'] if os.environ['SOLID_SLACK_CHANNEL'] else None
SOLID_SLACK_TOKEN = os.environ['SOLID_SLACK_TOKEN'] if os.environ['SOLID_SLACK_TOKEN'] else None

slack_failure = {
    "ok": False
}

class SimpleSlack:
    execution_slack_thread = None

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
