import os
import glob
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "chroma_db"
EMBEDDING_MODEL_NAME = "google/gemma-4-e4b"

def ingest_documents():
    print(f"Checking for documents in {DATA_DIR}...")
    pdf_files = glob.glob(str(DATA_DIR / "*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in the data directory.")
        return

    print(f"Found {len(pdf_files)} PDF files.")
    
    documents = []
    for pdf_path in pdf_files:
        print(f"Loading {pdf_path}...")
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        # Add metadata for filtration if needed later
        for doc in docs:
            doc.metadata["source"] = os.path.basename(pdf_path)
        documents.extend(docs)
    
    print(f"Loaded {len(documents)} pages from PDFs.")

    # Split text
    print("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")

    # Create Embeddings
    print(f"Initializing embedding model ({EMBEDDING_MODEL_NAME}) on CPU...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'}
    )

    # Create & Persist Vector Store
    print(f"Creating Chroma vector store in {DB_DIR}...")
    if DB_DIR.exists():
        print("Existing DB directory found. It will be updated.")
    
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(DB_DIR)
    )
    
    print("Ingestion complete. Vector store created.")

if __name__ == "__main__":
    if not DATA_DIR.exists():
        print(f"Error: Data directory not found at {DATA_DIR}")
        exit(1)
             
    ingest_documents()
