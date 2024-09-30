import chromadb
from chromadb import PersistentClient

vector_client = PersistentClient()
central_model = vector_client.get_or_create_collection('central')
# Use the central_model for everything