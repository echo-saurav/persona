import importlib.util
import time
from typing import Dict, Callable, Optional
from jinja2 import Environment, FileSystemLoader
from dataclasses import dataclass
from src.app.config import Prompt, Config
from src.context import Context


@dataclass
class FunCache:
    value: str
    last_timestamp: int = 0


class TemplateFunctionLoader:
    def __init__(self, function_file_path: str):
        self.functions: Dict[str, Callable] = {}
        self._load_functions(function_file_path)

    def _load_functions(self, file_path: str):
        spec = importlib.util.spec_from_file_location("template_functions", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for name in dir(module):
            fn = getattr(module, name)
            if callable(fn) and not name.startswith("_"):
                self.functions[name] = fn


class TemplateEngine:
    def __init__(self, config: Config):
        self.loader = TemplateFunctionLoader(config.get_template_function_path())
        # key -> FunCache
        self.cache: Dict[str, FunCache] = {}
        # set base path
        self.env = Environment(loader=FileSystemLoader(config.config_path))
        self._register_functions()

    def _register_functions(self):
        for name, fn in self.loader.functions.items():
            self.env.globals[name] = self._make_cached_function(fn, name)

    def _make_cached_function(self, fn: Callable, name: str):
        """
        wrapper signature: wrapper(context=None, cache_ttl=None, cache_id=None)
        Note: fn(context, cache_ttl) stays the same.
        """

        def wrapper(context: Context, cache_ttl: Optional[int] = None, cache_id: Optional[str] = None):
            # return value if no cache id
            if cache_id is None:
                return fn(context)

            cache_key = f"{cache_id}:{name}"

            # get current time
            ttl = int(cache_ttl) if cache_ttl else 0
            now = int(time.time())

            if ttl > 0:
                existing = self.cache.get(cache_key)
                if existing and (now - existing.last_timestamp) < ttl:
                    return existing.value

            # run functions for result
            result = fn(context, cache_ttl)

            # store in cache if ttl set
            if ttl > 0:
                self.cache[cache_key] = FunCache(value=result, last_timestamp=now)

            return result

        return wrapper

    def render(self, prompt: Prompt, context: Context, cache_id: Optional[str] = None, **kwargs) -> str:
        """
        Render a template file by name. Same behavior as render_string with default cache_id support.
        """
        tpl = self.env.get_template(prompt.file_name)
        render_context = {
            "context": context,
            "cache_id": cache_id,
            **kwargs
        }
        return tpl.render(render_context).strip()
