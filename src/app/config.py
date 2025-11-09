import json
from typing import Literal, List, Optional
from pydantic import BaseModel
from dotenv import dotenv_values
from string import Template
import os

ModelAPIType = Literal["openai", "ollama"]
ModelType = Literal["embedding", "completion"]


class Model(BaseModel):
    name: Optional[str] = None
    api_type: Optional[ModelAPIType] = None
    model_type: Optional[ModelType] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = ""
    model_id: Optional[str] = None


class VectorDatabase(BaseModel):
    type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    api_key: Optional[str] = ""
    collection_name: Optional[str] = None
    default_score_threshold: Optional[float] = 0.7
    default_limit: Optional[int] = 10


class Prompt(BaseModel):
    name: Optional[str] = None
    file_name: Optional[str] = None
    model: Optional[str] = None


class Routes(BaseModel):
    prompt: Optional[Prompt]
    routed_prompts: Optional[List[Prompt]]


class Config(BaseModel):
    model_name: Optional[str] = None
    description: Optional[str] = None
    chat_model: Optional[Model] = None
    # query and database
    embedding_model: Optional[Model] = None
    vector_database: Optional[VectorDatabase] = None
    # multi models
    models: Optional[List[Model]] = None
    # dynamic prompt
    routes: Optional[Routes] = None
    # default prompts
    default_system_prompt: Optional[Prompt] = None
    context_summariser: Optional[Prompt] = None
    chat_summariser: Optional[Prompt] = None
    user_profiling: Optional[Prompt] = None
    # others
    function_path: Optional[str] = "TemplateFunctions.py"
    config_path: Optional[str] = ""

    def set_config_path(self, config_path: str):
        self.config_path = config_path

    def get_template_function_path(self):
        return f"{self.config_path}/{self.function_path}"


def __read_file(file_path: str):
    with open(file_path, 'r') as file:
        content = file.read()
        return content


def __wrap_env(config_path: str):
    env_vars = dict(os.environ)
    config_content = __read_file(config_path)
    config_with_env = Template(config_content).safe_substitute(env_vars)
    return config_with_env


def formate_model_json(model_name):
    model = {
        "active": True,
        "context_window": 512,
        "created": 1748632101,
        "id": model_name,
        "max_completion_tokens": 512,
        "object": "model",
        "owned_by": "ai",
        "public_apps": None
    }
    return model


def get_configs(parent_config_dir):
    models = []
    for config_dir in os.listdir(parent_config_dir):
        config = get_config(f"{parent_config_dir}/{config_dir}")
        models.append(config)

    return models


def get_all_models_json(parent_config_dir):
    models_json = []
    configs = get_configs(parent_config_dir)
    for config in configs:
        model_json = formate_model_json(config.model_name)
        models_json.append(model_json)

    return models_json


# TODO: make a default model
def query_model(config: Config, model_name: str) -> Model:
    for model in config.models:
        if model.name == model_name:
            return model


def get_config_by_id(parent_config_dir: str, model_name: str) -> Optional[Config]:
    for config_dir in os.listdir(parent_config_dir):
        config = get_config(f"{parent_config_dir}/{config_dir}")
        if config.model_name == model_name:
            return config

    return None


def get_config(config_path: str, file_name: str = "config.json") -> Config:
    config_json_path = f"{config_path}/{file_name}"
    config_with_env = __wrap_env(config_json_path)
    data = json.loads(config_with_env)
    config = Config(**data)
    config.set_config_path(config_path)
    return config
