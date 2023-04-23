import logging
import traceback

from flask import Flask, request, jsonify
from flask_cors import CORS

from autogpt.agent import Agent
from autogpt.memory import get_memory
from autogpt.prompt import construct_prompt
from utils import FILE_HANDLER

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(FILE_HANDLER)


@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        agent = Agent(
            ai_name='',
            memory=get_memory(init=True),
            full_message_history=[],
            next_action_count=0,
            system_prompt=construct_prompt(description=data.get('description'), goals=data.get('goals')),
            triggering_prompt="Determine which next command to use, and respond using the format specified above:",
        )
        return jsonify(agent.start_interaction_loop())
    except Exception as e:
        app.logger.error(traceback.format_exc())
        return f"Internal exception: {e}", 500


if __name__ == '__main__':
    # Set host and port to run the flast API server
    app.run(host='0.0.0.0', port=16000, debug=True)
