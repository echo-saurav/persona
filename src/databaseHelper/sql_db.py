import sqlite3
import time
from pathlib import Path
import os
from dataclasses import dataclass
from typing import List


class UserProfileDatabase:
    @dataclass
    class UserProfile:
        id: int
        key: str
        model_name: str
        api_key: str
        content: str
        timestamp: float

    def __init__(self, database_file="user_profile.db", databases_dir="database"):
        os.makedirs(databases_dir, exist_ok=True)
        database_file_path = os.path.join(databases_dir, database_file)

        self.__table_name = "user_profile"
        self.db = LocalDB(database_file_path)
        self.db.create_table(self.__table_name, {
            "id": "INTEGER PRIMARY KEY",
            "key": "TEXT",
            "api_key": "TEXT",
            "model_name": "TEXT",
            "content": "TEXT",
            "timestamp": "REAL"
        }, unique_fields=["key"])

    def update_profile(self, model_name: str, api_key: str, content: str):
        data = {
            "key": self.get_key(api_key, model_name),
            "api_key": api_key,
            "model_name": model_name,
            "content": content,
            "timestamp": time.time()
        }
        self.db.upsert(self.__table_name, data, "key")

    def get_profile(self, model_name: str, api_key: str) -> UserProfile|None:
        key = self.get_key(api_key, model_name)
        rows = self.db.filter_by_field(self.__table_name, "key", key, limit=1)
        user_profile = [UserProfileDatabase.UserProfile(*profile) for profile in rows]
        if len(user_profile):
            return user_profile[0]
        else:
            return None

    def all_profiles(self, limit=10) -> List[UserProfile]:
        rows = self.db.list(self.__table_name, limit)
        user_profile = [UserProfileDatabase.UserProfile(*profile) for profile in rows]
        return user_profile

    @staticmethod
    def get_key(api_key: str, model_name: str):
        return f"{api_key}-{model_name}"


class ConversationsNotesDatabase:
    @dataclass
    class ConvoNotes:
        id: int
        conversation_id: str
        content: str
        timestamp: float

    def __init__(self, database_file="conversation_notes.db", databases_dir="database"):
        os.makedirs(databases_dir, exist_ok=True)
        database_file_path = os.path.join(databases_dir, database_file)

        self.__table_name = "Memory"
        self.db = LocalDB(database_file_path)
        self.db.create_table(self.__table_name, {
            "id": "INTEGER PRIMARY KEY",
            "conversation_id": "TEXT",
            "content": "TEXT",
            "timestamp": "REAL"
        })

    def insert_note(self, conversation_id: str, content: str):
        data = {
            "conversation_id": conversation_id,
            "content": content,
            "timestamp": time.time()
        }
        self.db.insert(self.__table_name, data)

    def get_notes(self, limit=5):
        rows = self.db.list(self.__table_name, limit)
        notes = [ConversationsNotesDatabase.ConvoNotes(*note) for note in rows]
        return notes


class MemoryDatabase:
    def __init__(self, database_file="memory.db", databases_dir="database"):
        os.makedirs(databases_dir, exist_ok=True)
        database_file_path = os.path.join(databases_dir, database_file)

        self.__memory_table = "Memory"
        self.db = LocalDB(database_file_path)
        self.db.create_table(self.__memory_table, {
            "id": "INTEGER PRIMARY KEY",
            "category": "TEXT",
            "content": "TEXT",
            "timestamp": "REAL"
        })

    def insert_memory(self, content: str):
        data = {"content": content, "timestamp": time.time()}
        self.db.insert(self.__memory_table, data)

    def get_last_memories(self, limit=5):
        memories = self.db.list(self.__memory_table, limit)
        for memory in memories:
            print(memory)


class ContextDatabase:
    def __init__(self, database_file_path="database/local.db"):
        self.__context_table = "Context"
        self.db = LocalDB(database_file_path)
        self.db.create_table(self.__context_table, {
            "id": "INTEGER PRIMARY KEY",
            "category": "TEXT",
            "content": "TEXT",
            "description": "TEXT"
        })

    def insert_context(self, category, content, description):
        self.db.insert(
            self.__context_table,
            {
                "category": category,
                "content": content,
                "description": description
            }
        )

    def get_context(self, limit):
        res = self.db.list(self.__context_table, limit)
        print(res)

    def search_category(self, category_name, limit):
        res = self.db.filter_by_field(
            self.__context_table,
            "category",
            category_name,
            limit
        )
        return res

        # print(db.search_by_start("people", "name", "S"))
        # print(db.filter_by_field("people", "age", 22))
        #
        # db.update("people", {"age": 26}, "name", "Saurav")
        # db.delete("people", "name", "Adike")
        # db.close()


class LocalDB:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    # def create_table(self, table_name, fields):
    #     """
    #     fields example: {'id': 'INTEGER PRIMARY KEY', 'name': 'TEXT', 'age': 'INTEGER'}
    #     """
    #     cols = ", ".join([f"{k} {v}" for k, v in fields.items()])
    #     query = f"CREATE TABLE IF NOT EXISTS {table_name} ({cols})"
    #     self.cursor.execute(query)
    #     self.conn.commit()
    def create_table(self, table_name, fields, unique_fields=None):
        """
        Create a table with optional UNIQUE constraints.

        fields example: {'id': 'INTEGER PRIMARY KEY', 'api_key': 'TEXT', 'age': 'INTEGER'}
        unique_fields example: ['api_key']
        """
        cols = ", ".join([f"{k} {v}" for k, v in fields.items()])
        unique_clause = ""
        if unique_fields:
            uniques = ", ".join(unique_fields)
            unique_clause = f", UNIQUE ({uniques})"

        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({cols}{unique_clause})"
        self.cursor.execute(query)
        self.conn.commit()

    def insert(self, table_name, data):
        """
        data example: {'name': 'Saurav', 'age': 24}
        """
        keys = ", ".join(data.keys())
        values = tuple(data.values())
        placeholders = ", ".join(["?"] * len(values))
        query = f"INSERT INTO {table_name} ({keys}) VALUES ({placeholders})"
        self.cursor.execute(query, values)
        self.conn.commit()

    # def upsert(self, table_name, data, conflict_field):
    #     keys = ", ".join(data.keys())
    #     values = tuple(data.values())
    #     placeholders = ", ".join(["?"] * len(values))
    #     update_clause = ", ".join([f"{k}=excluded.{k}" for k in data.keys()])
    #
    #     query = f"""
    #         INSERT INTO {table_name} ({keys})
    #         VALUES ({placeholders})
    #         ON CONFLICT({conflict_field}) DO UPDATE SET
    #         {update_clause}
    #     """
    #     self.cursor.execute(query, values)
    #     self.conn.commit()

    def upsert(self, table_name, data, conflict_field="api_key"):
        """
        Insert a record if not exists, or update if api_key already exists.

        data example: {'api_key': 'xoxo', 'age': 24}
        """
        keys = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        update_clause = ", ".join([f"{k}=excluded.{k}" for k in data.keys() if k != conflict_field])

        query = f"""
        INSERT INTO {table_name} ({keys})
        VALUES ({placeholders})
        ON CONFLICT({conflict_field}) DO UPDATE SET
            {update_clause}
        """

        self.cursor.execute(query, tuple(data.values()))
        self.conn.commit()

    def update(self, table_name, data, where_field, where_value):
        # """
        # updates example: {'name': 'Adike', 'age': 25}
        # """
        # set_clause = ", ".join([f"{k}=?" for k in updates.keys()])
        # values = list(updates.values()) + [where_value]
        # query = f"UPDATE {table_name} SET {set_clause} WHERE {where_field}=?"
        # self.cursor.execute(query, values)
        # self.conn.commit()
        """
        data example: {'name': 'Saurav', 'age': 24}
        """
        keys = ", ".join(data.keys())
        values = tuple(data.values())
        placeholders = ", ".join(["?"] * len(values))
        update_clause = ", ".join([f"{k}=excluded.{k}" for k in data.keys()])
        query = f"""
            INSERT INTO {table_name} ({keys}) VALUES ({placeholders})
            ON CONFLICT api_key DO UPDATE SET
            {update_clause}
        """
        self.cursor.execute(query, values)
        self.conn.commit()

    def list(self, table_name, limit):
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def delete(self, table_name, where_field, where_value):
        query = f"DELETE FROM {table_name} WHERE {where_field}=?"
        self.cursor.execute(query, (where_value,))
        self.conn.commit()

    def search_by_start(self, table_name, field, prefix):
        query = f"SELECT * FROM {table_name} WHERE {field} LIKE ?"
        self.cursor.execute(query, (f"{prefix}%",))
        return self.cursor.fetchall()

    # def filter_by_field(self, table_name, field, value, limit=None):
    #     # query = f"SELECT * FROM {table_name} WHERE {field}={value} LIMIT {limit} "
    #     query = f"SELECT * FROM {table_name} WHERE {field}=?"
    #     if limit is not None:
    #         query += f" LIMIT {int(limit)}"
    #     self.cursor.execute(query, (value,))
    #     # self.cursor.execute(query)
    #     return self.cursor.fetchall()

    def filter_by_field(self, table_name, field, value, limit=None):
        query = f"SELECT * FROM {table_name} WHERE {field} = ?"
        params = [value]
        if limit is not None:
            query += " LIMIT ?"
            params.append(int(limit))
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()
