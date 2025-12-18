from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import os
from pathlib import Path

class VectorDB:
    def __init__(self):
        app_data = os.environ.get('APPDATA')
        if not app_data:
             app_data = os.path.expanduser("~/.local/share")
        
        self.db_dir = Path(app_data) / "AeroBrief" / "qdrant_data"
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedded Qdrant
        self.client = QdrantClient(path=str(self.db_dir))
        
        self.collection_name = "aerobrief_research"
        self.init_collection()

    def init_collection(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )

    def search(self, vector, limit=5):
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit
        )

    def upsert(self, points):
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
