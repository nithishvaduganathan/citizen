import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
import google.generativeai as genai
from typing import List
from langchain.embeddings import Embeddings

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

class GeminiEmbeddings(Embeddings):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document",
            )
            embeddings.append(result['embedding'])
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query",
        )
        return result['embedding']

def get_answer(query: str):
    if not os.path.exists("faiss_index"):
        return "System not initialized. Please run ingestion first."
    
    embeddings = GeminiEmbeddings()
    vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    
    # Retrieve relevant docs
    docs = vectorstore.similarity_search(query, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])
    
    # Generate answer using Gemini
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""You are a helpful Civic Assistant. Use the following context from the Indian Constitution to answer the user's question.
    
Context:
{context}

Question: {query}

Answer:"""
    
    response = model.generate_content(prompt)
    return response.text

def chat_with_rag(query: str):
    try:
        return get_answer(query)
    except Exception as e:
        return f"Error: {str(e)}"
