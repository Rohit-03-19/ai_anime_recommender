# --- REFINED DECOUPLED IMPORTS ---
from langchain_community.retrievers import BM25Retriever
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from src.prompt_template import get_anime_prompt

class AnimeRecommender:
    def __init__(self, chroma_retriever, all_documents, api_key: str, model_name: str):
        # 1. Initialize the LLM (Production standard)
        self.llm = ChatGroq(
            api_key=api_key,
            model=model_name,
            temperature=0
        )
        
        # 2. Setup Retrievers independently
        self.dense_retriever = chroma_retriever
        self.sparse_retriever = BM25Retriever.from_documents(all_documents)
        self.sparse_retriever.k = 5
        
        self.prompt = get_anime_prompt()

        # 3. Construct a simplified Chain that expects a pre-processed context
        self.chain = (
            {
                "context": RunnablePassthrough(),
                "question": RunnablePassthrough()
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def get_recommendation(self, query: str):
        """Manual Hybrid Search: Merges results before LLM processing"""
        # A. Fetch from both sources
        dense_docs = self.dense_retriever.invoke(query)
        sparse_docs = self.sparse_retriever.invoke(query)
        
        # B. Merge and remove duplicates (Standard RAG practice)
        all_docs = dense_docs + sparse_docs
        unique_docs = list({doc.page_content: doc for doc in all_docs}.values())
        
        # C. Format as a single block of context
        context_text = "\n\n".join([doc.page_content for doc in unique_docs])
        
        # D. Invoke chain with prepared context
        return self.chain.invoke({"context": context_text, "question": query})