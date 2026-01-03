import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
import google.generativeai as genai
from typing import List
from langchain.embeddings import Embeddings

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)

class GeminiEmbeddings(Embeddings):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Batch embedding not always supported directly or requires loop for large lists
        embeddings = []
        for text in texts:
            # Model name for embeddings
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

def ingest_data(pdf_path="constitution.pdf"):
    if not os.path.exists(pdf_path):
        print(f"File {pdf_path} not found.")
        return

    print("Loading PDF...")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    print("Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)

    print("Creating embeddings (using Gemini SDK)...")
    embeddings = GeminiEmbeddings()

    print("Building vector store...")
    # Passing the custom embeddings class
    vectorstore = FAISS.from_documents(texts, embeddings)
    
    vectorstore.save_local("faiss_index")
    print("Ingestion complete. Vector store saved to 'faiss_index'.")

if __name__ == "__main__":
    ingest_data("constitution.pdf")
