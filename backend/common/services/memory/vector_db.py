import logging
import os
import uuid
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

from backend.common.config import AppMode, settings

logger = logging.getLogger(__name__)


def _create_client() -> QdrantClient:
    if settings.APP_MODE == AppMode.DESKTOP:
        return QdrantClient(path=str(settings.DATA_DIR / "qdrant_db"))
    qdrant_url = os.getenv("QDRANT_URL")
    if qdrant_url:
        return QdrantClient(url=qdrant_url)
    return QdrantClient(path="./qdrant_db_local")


client = _create_client()
embedder = SentenceTransformer("all-MiniLM-L6-v2")


def ensure_collection(name: str) -> None:
    if client.collection_exists(name):
        return
    client.create_collection(
        collection_name=name,
        vectors_config=models.VectorParams(
            size=384,
            distance=models.Distance.COSINE,
        ),
    )


def _query_collection(collection: str, user_id: int, query: str, limit: int = 3) -> list[str]:
    try:
        ensure_collection(collection)
        query_vector = embedder.encode(query).tolist()
        results = client.query_points(
            collection_name=collection,
            query=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=str(user_id)),
                    )
                ]
            ),
            limit=limit,
        ).points
        return [hit.payload.get("document", "") for hit in results if hit.payload.get("document")]
    except Exception as exc:
        logger.exception("Vector DB query error (%s): %s", collection, exc)
        return []


def get_user_context(user_id: int, topic: str) -> str:
    try:
        documents = _query_collection(settings.QDRANT_COLLECTION_USER_PROFILE, user_id, topic, limit=3)
        return "\n".join(documents) if documents else "No specific preferences found."
    except Exception as exc:
        logger.exception("Vector DB error: %s", exc)
        return "No context available."


def save_feedback(user_id: int, topic: str, feedback: str, sentiment: str) -> None:
    ensure_collection(settings.QDRANT_COLLECTION_USER_PROFILE)
    text = f"Topic: {topic}. User Feedback: {feedback}. Sentiment: {sentiment}"
    vector = embedder.encode(text).tolist()
    point_id = str(uuid.uuid4())

    client.upsert(
        collection_name=settings.QDRANT_COLLECTION_USER_PROFILE,
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
        ensure_collection(settings.QDRANT_COLLECTION_USER_PROFILE)
        response = client.scroll(
            collection_name=settings.QDRANT_COLLECTION_USER_PROFILE,
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


def get_memory_context(user_id: int, topic: str, session_id: str | None = None) -> str:
    sections: list[str] = []

    user_docs = _query_collection(settings.QDRANT_COLLECTION_USER_DOCS, user_id, topic, limit=5)
    if user_docs:
        sections.append("User Documents:\n" + "\n".join(user_docs))

    session_mem = _query_collection(settings.QDRANT_COLLECTION_SESSION_MEMORY, user_id, topic, limit=3)
    if session_mem:
        sections.append("Session Memory:\n" + "\n".join(session_mem))

    profile = _query_collection(settings.QDRANT_COLLECTION_USER_PROFILE, user_id, topic, limit=3)
    if profile:
        sections.append("User Profile:\n" + "\n".join(profile))

    return "\n\n".join(sections).strip()
