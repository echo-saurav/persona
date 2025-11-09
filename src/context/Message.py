from pydantic import BaseModel
from enum import Enum
from typing import Optional


class Role(str, Enum):
    SYSTEM_MESSAGE = "system"
    ASSISTANT_MASSAGE = "assistant"
    USER_MESSAGE = "user"


class Message(BaseModel):
    role: Optional[Role] = None
    content: Optional[str] = None

    def is_system_message(self):
        if self.role == Role.SYSTEM_MESSAGE:
            return True
        else:
            return False
