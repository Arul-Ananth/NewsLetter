import uuid
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

# 1. Initialize Qdrant Client (Persistent Local Mode)
client = QdrantClient(path="./qdrant_db_local")

# 2. Initialize Embedding Model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

COLLECTION_NAME = "user_profile"

# 3. Ensure Collection Exists
if not client.collection_exists(COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=384,
            distance=models.Distance.COSINE
        )
    )


def get_user_context(user_id: int, topic: str) -> str:
    """
    Retrieves relevant context for a specific user based on the topic.
    """
    try:
        query_vector = embedder.encode(topic).tolist()

        # FIXED: Changed 'filter' to 'query_filter'
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=str(user_id))
                    )
                ]
            ),
            limit=3
        ).points

        if results:
            documents = [hit.payload["document"] for hit in results if "document" in hit.payload]
            return "\n".join(documents)

        return "No specific preferences found."

    except Exception as e:
        print(f"Vector DB Error: {e}")
        return "No context available."


def save_feedback(user_id: int, topic: str, feedback: str, sentiment: str):
    """
    Saves user feedback as a vector embedding.
    """
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
                    "timestamp": datetime.now().isoformat()
                }
            )
        ]
    )


def fetch_memories(user_id: int):
    """
    Fetches all memories for a specific user from Qdrant.
    """
    try:
        # Scroll (paginate) through the collection to get all items for this user
        response = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=str(user_id))
                    )
                ]
            ),
            limit=100
        )

        points, _ = response  # Unpack the tuple (points, offset)

        # Format for Frontend
        return [
            {
                "id": point.id,
                "document": point.payload.get("document", ""),
                "metadata": point.payload
            }
            for point in points
        ]
    except Exception as e:
        print(f"Error fetching memories: {e}")
        return []