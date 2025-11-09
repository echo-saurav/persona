from flask import Flask
from flask import request, Response, stream_with_context
from flask_cors import CORS
from src.app.config import get_all_models_json, get_config_by_id
from src.llmanager import LLMManager
from src.context import ContextManager
from src.app.wrapper import OpenaiWrapper


def create_app(configs_dir):
    app = Flask(__name__)
    CORS(app, origins="*")

    # route
    @app.route('/chat/completions', methods=["POST"])
    def completions():
        print("completions")
        # Get all variables
        api_key = request.headers.get("Authorization")
        data = request.get_json()
        messages = data.get("messages")
        model_name = data.get("model")
        # config based on req
        config = get_config_by_id(configs_dir, model_name)

        # prepare
        context_manager = ContextManager(
            messages=messages,
            config=config,
            api_key=api_key
        )
        openai_wrapper = OpenaiWrapper(
            context_manager=context_manager
        )

        return Response(
            stream_with_context(
                # response stream with context
                openai_wrapper.generate_chat()
            ),
            content_type='text/event-stream'
        )

        pass

    @app.route('/models', methods=["GET"])
    def get_models():
        print("get default models")
        models = get_all_models_json(configs_dir)
        res = {
            "object": "list",
            "data": models,
        }
        return res

    return app
