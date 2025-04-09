from typing import Dict, List, Any, Optional
import os
from haystack import Pipeline
from haystack.utils import Secret
from haystack.components.builders import PromptBuilder
from haystack.components.generators.openai import OpenAIGenerator
from ..search.vectorstore import DenseVectorSearch
from ..models.note import Note
from ..config import logger, OPENAI_API_KEY


class RAGPipeline:
    """Handles the full RAG pipeline: retrieval and generation"""
    
    def __init__(self, vector_search: DenseVectorSearch, api_key: Optional[str] = None):
        """
        Initialize the RAG pipeline.
        
        Args:
            vector_search: Vector search component
            api_key: OpenAI API key (uses env variable if not provided)
        """
        self.vector_search = vector_search

        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            logger.warning("No OpenAI API key provided. LLM generation will fail.")
        
        self.llm = OpenAIGenerator(
            api_key=Secret.from_token(self.api_key),
            model="gpt-4o-mini",
            generation_kwargs={"temperature": 0.1, "max_tokens": 500}
        )

        self.prompt_template = """
        Answer the following question based on the provided notes and your knowledge.
        
        QUESTION: {{query}}
        
        RELEVANT NOTES:
        {% for doc in documents %}
        NOTE {{loop.index}}:
        {{doc.content}}
        Tags: {{doc.meta.tags | join(', ')}}
        {% endfor %}
        
        Please provide a comprehensive answer to the question based on the information in the notes.
        """
        
        self.prompt_builder = PromptBuilder(template=self.prompt_template)
        
        self.rag_pipeline = Pipeline()
        self.rag_pipeline.add_component("prompt_builder", self.prompt_builder)
        self.rag_pipeline.add_component("llm", self.llm)
        
        self.rag_pipeline.connect("prompt_builder.prompt", "llm.prompt")
        
        logger.info("Initialized RAG pipeline with LLM")
    
    async def answer_question(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Process a query through the full RAG pipeline
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            
        Returns:
            Dictionary containing the answer and retrieved documents
        """
        if not self.api_key:
            return {
                "answer": "Unable to generate answer - OpenAI API key not configured.",
                "documents": []
            }
            
        logger.info(f"Retrieving documents for: '{query}'")
        documents = self.vector_search.search(query, top_k)
        
        if not documents:
            logger.warning("No relevant documents found")
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "documents": []
            }
        
        try:
            haystack_docs = [note.to_haystack_document() for note in documents]

            logger.info(f"Passing {len(haystack_docs)} documents to LLM")
            
            result = self.rag_pipeline.run({
                "prompt_builder": {
                    "query": query,
                    "documents": haystack_docs
                }
            })
            
            answer = result["llm"]["replies"][0]
            logger.info(f"Generated answer of length {len(answer)}")
            
            return {
                "answer": answer,
                "documents": documents
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}", exc_info=True)
            return {
                "answer": f"An error occurred while generating the answer: {str(e)}",
                "documents": documents
            }