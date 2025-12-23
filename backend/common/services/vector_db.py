import logging
import os
import uuid
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

from backend.common.config import AppMode, settings

logger = logging.getLogger(__name__)


if settings.APP_MODE == AppMode.DESKTOP:
    client = QdrantClient(path=str(settings.DATA_DIR / "qdrant_db"))
else:
    qdrant_url = os.getenv("QDRANT_URL")
    if qdrant_url:
        client = QdrantClient(url=qdrant_url)
    else:
        client = QdrantClient(path="./qdrant_db_local")

embedder = SentenceTransformer("all-MiniLM-L6-v2")

COLLECTION_NAME = "user_profile"

if not client.collection_exists(COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=384,
            distance=models.Distance.COSINE,
        ),
    )


def get_user_context(user_id: int, topic: str) -> str:
    try:
        query_vector = embedder.encode(topic).tolist()
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=str(user_id)),
                    )
                ]
            ),
            limit=3,
        ).points

        if results:
            documents = [hit.payload["document"] for hit in results if "document" in hit.payload]
            return "\n".join(documents)

        return "No specific preferences found."
    except Exception as exc:
        logger.exception("Vector DB error: %s", exc)
        return "No context available."


def save_feedback(user_id: int, topic: str, feedback: str, sentiment: str) -> None:
    text = f"Topic: {topic}. User Feedback: {feedback}. Sentiment: {sentiment}"
    vector = embedder.encode(text).tolist()
    point_id = str(uuid.uuid4())

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "document": text,
                    "user_id": str(user_id),
                    "topic": topic,
                    "sentiment": sentiment,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        ],
    )


def fetch_memories(user_id: int):
    try:
        response = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=str(user_id)),
                    )
                ]
            ),
            limit=100,
        )

        points, _ = response
        return [
            {
                "id": point.id,
                "document": point.payload.get("document", ""),
                "metadata": point.payload,
            }
            for point in points
        ]
    except Exception as exc:
        logger.exception("Error fetching memories: %s", exc)
        return []
