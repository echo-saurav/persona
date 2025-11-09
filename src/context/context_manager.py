from . import Context
from src.template import TemplateEngine
from src.llmanager import LLMManager
from src.app.config import query_model, Prompt, Config
import re
import json


class ContextManager:
    def __init__(self, messages, config: Config, api_key: str):
        self.config = config
        self.template_engine = TemplateEngine(config)
        self.api_key = api_key
        self.llm_manager = LLMManager(self.config)
        self.context = Context(messages, config, api_key)

    def get_routing_prompt_name(self) -> Prompt:
        routing_prompt = self.config.routes.prompt
        route_json = self.render_prompt(routing_prompt, self.context, True)
        route_name = route_json.get("route")
        return self.query_routed_system_prompt(route_name)

    def query_routed_system_prompt(self, route_name: str) -> Prompt:
        for route in self.config.routes.routed_prompts:
            if route.name == route_name:
                return route
        # get default route if not found
        return self.config.default_system_prompt

    def get_context_summery(self, query_result: str, context: Context):
        summariser_prompt = self.config.context_summariser

        prompt_text = self.template_engine.render(
            prompt=summariser_prompt,
            context=context,
            cache_id=self.api_key,
            full_context=query_result
        )
        summery = self.llm_manager.gen(
            prompt_text=prompt_text,
            model=query_model(self.config, summariser_prompt.model)
        )
        return summery

    def render_system_prompt(self, context: Context, routing_prompt: Prompt, **kwargs):
        if routing_prompt:
            system_prompt = routing_prompt
        else:
            system_prompt = self.config.default_system_prompt
        system_prompt = self.template_engine.render(
            prompt=system_prompt,
            context=context,
            cache_id=self.api_key,
            **kwargs
        )
        return system_prompt

    def render_prompt(self, prompt: Prompt, context: Context, output_json=False):
        prompt_text = self.template_engine.render(
            prompt,
            context,
            self.api_key
        )
        response = self.llm_manager.gen(
            prompt_text=prompt_text,
            model=query_model(self.config, prompt.model)
        )
        if output_json:
            render_json = self.extract_json_from_markdown(response)
            return render_json

        return response

    @staticmethod
    def extract_json_from_markdown(md_text: str):
        # Try to find code blocks ```...```
        match = re.search(r"```(.*?)```", md_text, re.DOTALL)
        if match:
            content = match.group(1).strip()
            # If it starts with json or similar like `json\n{...}`, remove that part
            if content.startswith("json"):
                # remove 'json' only if it's at the start and followed by newline or space
                content = re.sub(r"^json\s*", "", content, count=1)
                # print(f"json content:{content}")
            return json.loads(content.strip()) if content else None

        # Fallback — if no code block, try to detect JSON-like structure directly
        json_match = re.search(r"(\{.*\})", md_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except:
                return None

        return None
