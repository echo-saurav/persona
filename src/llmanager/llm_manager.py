import json
import time
from openai import OpenAI
from ollama import Client
# embedding calculation
from numpy import dot
from numpy.linalg import norm
from src.app.config import Config, Model


class LLMManager:

    def __init__(self, config: Config):
        self.config = config

    def stream_chat(self, model: Model, messages, api_key):
        # yield f"data: {self.push_streaming_text("Start thinking")}\n\n".encode("utf-8")
        # TODO: make case for ollama
        if model.api_type == "openai":
            openai = OpenAI(
                base_url=model.base_url,
                api_key=model.api_key
            )
            stream = openai.chat.completions.create(
                model=model.model_id,
                messages=messages,
                stream=True
            )
            # yield f"data: {self.push_streaming_text("Stop thinking")}\n\n".encode("utf-8")
            ai_output = ""
            try:
                for chunk in stream:
                    # print(chunk.model_dump_json(indent=2))
                    delta = chunk.choices[0].delta.content
                    if delta:
                        ai_output += delta
                    yield f"data: {chunk.model_dump_json()}\n\n".encode("utf-8")
            finally:

                ai_output = {"role": "assistant", "content": ai_output}
                all_messages = messages + [ai_output]

                from src.background import add_background_tasks
                add_background_tasks(
                    all_messages=all_messages,
                    api_key=api_key,
                    config=self.config
                )

                # summarise new conversation
                # from src.server import add_background_task
                # add_background_task(all_messages, api_key, self.config.model_name)
                # on_complete(api_key, all_messages)

    def gen(self, prompt_text: str, model: Model, system_prompt=None):
        # TODO: make case for ollama
        if model.api_type == "openai":
            messages = []
            if system_prompt:
                messages.append({"role": "assistant", "content": system_prompt})
            if prompt_text:
                messages.append({"role": "user", "content": prompt_text})

            openai = OpenAI(
                base_url=model.base_url,
                api_key=model.api_key
            )

            response = openai.chat.completions.create(
                model=model.model_id,
                messages=messages,
                stream=False
            )
            return response.choices[0].message.content

    def get_embed(self, prompt, vector_size=768):
        # TODO: make case for openai embeddings
        if self.config.embedding_model.api_type == "ollama":
            ollama_client = Client(host=self.config.embedding_model.base_url)
            embeddings = ollama_client.embed(
                model=self.config.embedding_model.model_id,
                input=prompt
            )
            if len(embeddings.embeddings) > 0:
                embedding = embeddings.embeddings[0]
                return embedding
            else:
                return [0] * vector_size
        elif self.config.embedding_model.api_type == "openai":
            openai = OpenAI(
                base_url=self.config.embedding_model.base_url,
                api_key=self.config.embedding_model.api_key
            )
            embeddings = openai.embeddings.create(
                model=self.config.embedding_model.model_id,
                input=prompt,
                encoding_format="float"
            )
            if len(embeddings.data) > 0:
                embedding = embeddings.data[0].embedding
                return embedding
            else:
                return [0] * vector_size

    def get_similarity(self, prompt1, prompt2):
        embedding1 = self.get_embed(prompt1)
        embedding2 = self.get_embed(prompt2)
        similarities = dot(embedding1, embedding2) / (norm(embedding1) * norm(embedding2))
        return similarities

    def format_instruction(self, instruction, query):
        if instruction is None:
            instruction = 'Given a web search query, retrieve relevant passages that answer the query'
        output = "<Instruct>: {instruction}\n<Query>: {query}\n".format(instruction=instruction,
                                                                        query=query)
        return output

    def instruct_similarities(self, instruction, query, documents):

        # instruct_query = f"Instruct: {instruction}\nQuery: {query}"
        instruct_query = self.format_instruction(instruction, query)
        q_embed = self.get_embed(instruct_query)
        scores = []
        for doc in documents:
            d_embed = self.get_embed(doc)
            sim = dot(q_embed, d_embed) / (norm(q_embed) * norm(d_embed))
            scores.append(sim)

        return scores

    @staticmethod
    def push_streaming_text(text):

        tmp = {
            "id": f"chatcmpl-{time.time()}",
            "choices": [
                {
                    "delta": {
                        "content": text,
                        "function_call": None,
                        "refusal": None,
                        "role": None,
                        "tool_calls": None
                    },
                    "finish_reason": None,
                    "index": 0,
                    "logprobs": None
                }
            ],
            "created": int(time.time()),
            "model": "meta-llama/llama-4-maverick-17b-128e-instruct",
            "object": "chat.completion.chunk",
            "service_tier": None,
            "system_fingerprint": "fp_d2c1f7e199",
            "usage": None
        }
        return json.dumps(tmp)

        # yield f"data: {json.dumps(tmp)}\n\n".encode("utf-8")
