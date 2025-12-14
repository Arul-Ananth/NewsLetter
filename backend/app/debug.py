from qdrant_client import QdrantClient

# Point this to your ACTUAL qdrant folder
client = QdrantClient(path="./qdrant_db_local") 

try:
    info = client.get_collection("user_profile")
    print(f"✅ Collection found! Total items: {info.points_count}")
    
    if info.points_count > 0:
        # Show the first item
        results = client.scroll(collection_name="user_profile", limit=1)
        print("\nSample Data:", results[0])
    else:
        print("⚠️ Collection exists but is EMPTY.")

except Exception as e:
    print(f"❌ Error: {e}")
    print("Did you create the collection name 'user_profile'?")