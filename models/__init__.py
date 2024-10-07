import chromadb
from chromadb import PersistentClient
from .migrations.image_transformer import VGGFeatureExtractor

extractor = VGGFeatureExtractor()

vector_client = PersistentClient('chromadbvector')
central_model = vector_client.get_or_create_collection('central')
title_model = vector_client.get_or_create_collection('title')
# Use the central_model for everything