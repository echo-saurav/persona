from textwrap import dedent
import hashlib
from src.app.config import Config
from typing import List
import re
from src.context.Message import Role, Message
from src.databaseHelper.vector_db import VectorDB
from src.databaseHelper.sql_db import UserProfileDatabase
from datetime import datetime, timezone, timedelta
from src.template.TemplateEngine import TemplateEngine
from src.llmanager import LLMManager


class Context:
    def __init__(self, messages, config: Config, api_key: str):
        self.messages = self._message_to_dataclass(messages)

        self.config = config
        self.api_key = api_key
        self.vectorDB = VectorDB(
            config.vector_database.host,
            config.vector_database.port,
            config.vector_database.collection_name,
            ""
        )
        self.user_profile_db = UserProfileDatabase()
        self.llm_manager = LLMManager(self.config)
        self.template_engine = TemplateEngine(config)

    @staticmethod
    def _message_to_dataclass(messages):
        if not messages:
            return []
        messages_data: List[Message] = []
        if messages:
            for m in messages:
                if isinstance(m, Message):
                    messages_data.append(m)
                else:
                    message = Message(**m)
                    messages_data.append(message)

        return messages_data

    def query_similar_conversations(self, query=None):
        # prepare query
        if query:
            query_prompt = query
        else:
            query_prompt = self.message_to_prompt()

        # create embedding of query
        embedding = self.llm_manager.get_embed(query_prompt)
        conversation_id = self.get_conversation_id()

        points = self.vectorDB.query_conversation(
            ignore_conversation_id=conversation_id,
            embedding=embedding,
            score_threshold=self.config.vector_database.default_score_threshold,
            limit=self.config.vector_database.default_limit
        )

        # formate the result in a prompt
        chats = ""
        for point in points:
            updated = point.payload.get("updated")
            timestamp = self.get_timestamp(updated)
            description = point.payload.get("description")
            chat_flow = point.payload.get("chat_flow")
            chat_flow = "\n".join(chat_flow)

            chats = f"<chat>\n{timestamp}\n{description}\n{chat_flow}\n</chat>\n{chats}"

        formated_prompt = None
        if len(points) > 0:
            formated_prompt = dedent(f"""
            Here are {len(points)} similar conversation from the past with the user 
            {chats} 
            """.strip())

        return formated_prompt

    def get_conversation_id(self, messages: List[Message] = None):

        if len(self.messages) >= 2:
            without_system_prompt = self.message_without_system_prompt()
            # only two for consistent hash id
            first_two_text = without_system_prompt[:2]
            messages_prompt = self.message_to_prompt(input_messages=first_two_text)
            hash_sting = hashlib.md5(messages_prompt.encode()).hexdigest()
            return hash_sting
        return ""

    def inject_system_message(self, system_prompt, include_old=False):
        new_massages = self.messages.copy()

        if include_old:
            existing_system_message = self.get_system_message()
            merged_system_message = f"{system_prompt}\n{existing_system_message}"
            message = Message(role=Role.SYSTEM_MESSAGE, content=merged_system_message)
        else:
            message = Message(role=Role.SYSTEM_MESSAGE, content=system_prompt)

        system_index = self.get_system_index()
        if system_index:
            new_massages.insert(system_index, message)
        else:
            new_massages.insert(0, message)

        return new_massages

    def get_system_message(self):
        index = self.get_system_index()
        if index:
            system_message = self.messages[index]
            system_message = system_message.content
            return system_message
        else:
            return ""

    def get_system_index(self):
        for index, message in enumerate(self.messages):
            if not message.is_system_message():
                return index
        return None

    def message_without_system_prompt(self, messages: List[Message] = None):
        new_messages = []
        if messages:
            for message in messages:
                if not message.is_system_message():
                    new_messages.append(message)
        else:
            for message in self.messages:
                if not message.is_system_message():
                    new_messages.append(message)
        return new_messages

    def message_to_prompt(
            self,
            input_messages: List[Message] = None,
            remove_thinking=True,
            user_tag="User: ",
            assistant_tag="Assistant: "
    ):
        prompt = ""

        if input_messages:
            messages = input_messages
        else:
            messages = self.messages

        for message in messages:
            content = message.content
            if remove_thinking:
                content = re.sub(
                    r'<think>.*?</think>',
                    '',
                    message.content,
                    flags=re.DOTALL
                )
            # user message
            if message.role == Role.USER_MESSAGE:
                prompt = f"{prompt}\n{user_tag}{content.strip()}"
            # assistant massage
            if message.role == Role.ASSISTANT_MASSAGE:
                prompt = f"{prompt}\n{assistant_tag}{content.strip()}"

        return prompt.strip()

    @staticmethod
    def get_timestamp(timestamp):
        now = datetime.now(timezone(timedelta(hours=6)))
        dt = datetime.fromtimestamp(timestamp, tz=timezone(timedelta(hours=6)))
        diff = now - dt

        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "just now"

    #
    # Template helper function for context
    #
    def current_chat(self, limit=10):
        # TODO: implement limit
        return dedent(f"""
        Here is the current chat with the user
        <chat>
        {self.message_to_prompt()}
        <chat>
        """)

    def get_last_conversations(self, api_key, include_info=False, limit=5):
        points = self.vectorDB.get_last_conversation(
            api_key=api_key,
            model_name=self.config.model_name,
            limit=limit
        )
        # if there is no conversation
        if points and len(points) == 0:
            return dedent("""
            This the first conversation with the user
            """)

        # if there are past conversations
        conversation_prompt = ""
        for point in points:
            chat_flow = point.payload.get("chat_flow")
            if chat_flow:
                chat_flow = "\n".join(chat_flow)
            if include_info:
                information = point.payload.get("information")
            else:
                information = ""

            updated = self.get_timestamp(
                point.payload.get("updated")
            )

            formate_message = f"{updated}\n{chat_flow}\n{information}".strip()

            conversation_prompt = dedent(f"""
            {conversation_prompt}
            <chat>
            {formate_message}
            </chat>
            """)

        formated_prompt = dedent(f"""
        Here is last {len(points)} chats with user
        <chats>
        {conversation_prompt}
        </chats>
        """)

        return formated_prompt

    def user_profile(self):
        profile = self.user_profile_db.get_profile(
            model_name=self.config.model_name,
            api_key=self.api_key
        )
        if profile:
            return profile
        else:
            return ""

    # TODO: include other template file
    def template_file(self, template_name: str):
        self.template_engine.render(self.config.user_profiling, self)
        return "Run template recursively"

    @staticmethod
    def current_time():
        from datetime import datetime
        __time_formate_string = "%I:%m %p , %d %B %A , %Y"
        __current_time = datetime.now().strftime(__time_formate_string)
        time_prompt = f"Currently the time is {__current_time}"
        return time_prompt
