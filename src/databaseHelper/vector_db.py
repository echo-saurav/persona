from typing import List
from qdrant_client import QdrantClient, models
from qdrant_client.conversions.common_types import Record, ScoredPoint


class VectorDB:
    def __init__(self, host, port, chat_collection: str, user_profile_collection: str):
        self.qdrant = QdrantClient(
            host=host,
            port=port
        )
        self.chat_collection_name = chat_collection
        self.create_chat_collection()
        # TODO: make user profile later
        # self.user_profile_collection = user_profile_collection

    def upsert_chat_summery(self, vector, payload, conversation_id: str):
        self.qdrant.upsert(
            collection_name=self.chat_collection_name,
            wait=True,
            points=[models.PointStruct(
                id=conversation_id,
                vector=vector,
                payload=payload
            )]
        )

    def get_last_conversation(self, api_key: str, model_name: str, limit=3) -> List[Record]:

        hits, _ = self.qdrant.scroll(
            collection_name=self.chat_collection_name,
            limit=limit,
            with_payload=True,
            with_vectors=False,
            order_by=models.OrderBy(
                key="updated",
                direction="asc",  # default is "asc"
                # start_from=123,  # start from this value
            ),
            # only get conversation from current user
            # and history of current model
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="api_key",
                        match=models.MatchValue(value=api_key)
                    ),
                    models.FieldCondition(
                        key="model_name",
                        match=models.MatchValue(value=model_name)
                    ),
                ]
            )
        )

        return hits

    def query_conversation(self, ignore_conversation_id, embedding, score_threshold, limit) -> List[ScoredPoint]:

        hits = self.qdrant.query_points(
            collection_name=self.chat_collection_name,
            query=embedding,
            # using="description",
            using="chat_flow",
            score_threshold=score_threshold,
            limit=limit,
            # Dont include current conversation
            query_filter=models.Filter(
                must_not=[
                    models.FieldCondition(
                        key='id',
                        match=models.MatchValue(value=ignore_conversation_id)
                    )
                ]
            )
        )
        points = hits.points
        return points

    def create_chat_collection(self, vector_size=768):
        if self.qdrant.collection_exists(self.chat_collection_name):
            print("chat collection exist")
        else:
            print("creating chat collection")
            vectors_config = {
                "description": models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
                "chat_flow": models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
                "information": models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
                "prompt": models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
            }
            self.create_collection(self.chat_collection_name, vectors_config)
            # make timestamp index
            self.qdrant.create_payload_index(
                collection_name=self.chat_collection_name,
                field_name="updated",
                field_schema="float"
            )
            # make id index
            self.qdrant.create_payload_index(
                collection_name=self.chat_collection_name,
                field_name="id",
                field_schema="keyword"
            )

    def create_collection(self, collection_name, vector_config):
        self.qdrant.create_collection(
            collection_name,
            vectors_config=vector_config
        )

    def count_collection(self, collection_name):
        res = self.qdrant.count(
            collection_name=collection_name,
            exact=True,
        )
        count = int(res.count)
        return count
