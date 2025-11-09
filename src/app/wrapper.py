from src.context import ContextManager
from src.databaseHelper.sql_db import UserProfileDatabase
from src.app.config import Config, query_model


class OpenaiWrapper:
    def __init__(self, context_manager: ContextManager):
        self.context_manager = context_manager
        self.llm_manager = context_manager.llm_manager
        self.user_db = UserProfileDatabase()

    def generate_chat(self):
        # context = Context(messages, config, api_key)

        # get a prompt based on current context
        # TODO: add a required context field
        routing_prompt = self.context_manager.get_routing_prompt_name()
        print(f"routing_prompt: {routing_prompt.name}")

        # get similar context
        # TODO: add other query source for similar context
        similar_context = self.context_manager.context.query_similar_conversations()

        # create summery
        # if query is much bigger
        max_query_result_char_limit = 2500
        if similar_context and len(similar_context) > max_query_result_char_limit:
            similar_context = self.context_manager.get_context_summery(similar_context, self.context_manager.context)

        # render system prompt based on route with all context
        system_prompt = self.context_manager.render_system_prompt(
            context=self.context_manager.context,
            routing_prompt=routing_prompt,
            context_summery=similar_context
        )

        payload = self.context_manager.context.inject_system_message(system_prompt)
        return self.llm_manager.stream_chat(
            model=query_model(
                self.context_manager.config,
                self.context_manager.config.default_system_prompt.model
            ),
            messages=payload,
            api_key=self.context_manager.api_key
        )

    def stream_once(self, message):
        tmp = self.llm_manager.push_streaming_text(message)
        yield f"data: {tmp}\n\n"
        # try:
        #     tmp = self.llm_manager.push_streaming_text(message)
        #     yield f"data: {tmp}\n\n"
        # except Exception as e:
        #     # SSE standard error way
        #     yield f"data: {json.dumps({'error': str(e)})}\n\n"
        # finally:
        #     # Always close nicely
        #     yield "data: [DONE]\n\n"
