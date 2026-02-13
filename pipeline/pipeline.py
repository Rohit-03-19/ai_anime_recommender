from src.vector_store import VectorStoreBuilder
from src.recommender import AnimeRecommender
from config.config import GROQ_API_KEY, MODEL_NAME
from utils.logger import get_logger
from utils.custom_exception import CustomException
from langchain_core.documents import Document #

logger = get_logger(__name__)

class AnimeRecommendationPipeline:
    def __init__(self, persist_dir="chroma_db"):
        try:
            logger.info("Initializing Hybrid Recommendation Pipeline")

            # 1. Load the Vector Store Builder
            vector_builder = VectorStoreBuilder(csv_path="", persist_dir=persist_dir)
            vector_store = vector_builder.load_vector_store()
            
            # 2. Extract ALL documents for BM25 (Keyword search)
            logger.info("Extracting documents from vector store for BM25 indexing...")
            raw_data = vector_store.get(include=["documents", "metadatas"])
            
            # Reconstruct LangChain Document objects using the core class
            all_documents = [
                Document(page_content=doc, metadata=meta) 
                for doc, meta in zip(raw_data["documents"], raw_data["metadatas"])
            ]

            # 3. Initialize the Hybrid Recommender
            retriever = vector_store.as_retriever(search_kwargs={"k": 5})

            self.recommender = AnimeRecommender(
                chroma_retriever=retriever,
                all_documents=all_documents,
                api_key=GROQ_API_KEY,
                model_name=MODEL_NAME
            )

            logger.info("Pipeline initialized successfully with Hybrid Search.")

        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {str(e)}")
            # This captures the version conflict or missing package errors
            raise CustomException("Error during hybrid pipeline initialization", e)
        
    def recommend(self, query: str) -> str:
        try:
            logger.info(f"Received query: {query}")
            recommendation = self.recommender.get_recommendation(query)
            logger.info("Recommendation generated successfully.")
            return recommendation
        except Exception as e:
            logger.error(f"Failed to get recommendation: {str(e)}")
            raise CustomException("Error during recommendation generation", e)