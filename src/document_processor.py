"""
Document processing module for the IOT Product Support Chatbot

This module handles:
- PDF document loading and text extraction
- Text chunking and embedding generation
- FAISS vector database creation and management
- Product-specific document organization
"""

import os
import logging
from typing import List, Dict, Tuple, Optional
import tempfile
import shutil

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Local imports
from config.settings import (
    EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, 
    PRODUCT_DOCS_DIR, IOT_PRODUCTS
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Handles document processing and vector database creation for IOT products
    
    This class manages:
    - Loading and processing PDF documents
    - Creating embeddings and FAISS indices
    - Product-specific document organization
    - Vector database persistence and loading
    """
    
    def __init__(self):
        """Initialize the document processor"""
        self.embeddings = None
        self.product_vectorstores = {}  # Store FAISS indices for each product
        self.combined_vectorstore = None  # Combined index for all products
        
        # Initialize embeddings model
        self._initialize_embeddings()
        
        # Create data directories if they don't exist
        self._create_directories()
    
    def _initialize_embeddings(self):
        """
        Initialize the HuggingFace embeddings model
        
        This creates the embedding model that will convert text chunks
        into numerical vectors for similarity search.
        """
        try:
            # Initialize HuggingFace embeddings with the specified model
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                model_kwargs={'device': 'cpu'},  # Use CPU for compatibility
                encode_kwargs={'normalize_embeddings': True}  # Normalize for better similarity
            )
            logger.info(f"Embeddings model '{EMBEDDING_MODEL}' initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing embeddings: {e}")
            raise
    
    def _create_directories(self):
        """Create necessary directories for data storage"""
        try:
            # Create product documents directory
            os.makedirs(PRODUCT_DOCS_DIR, exist_ok=True)
            
            # Create vector database directory
            vector_db_dir = os.path.join("data", "vector_db")
            os.makedirs(vector_db_dir, exist_ok=True)
            
            # Create product-specific vector directories
            for product in IOT_PRODUCTS:
                product_name = product["name"].replace(" ", "_").lower()
                product_vector_dir = os.path.join(vector_db_dir, product_name)
                os.makedirs(product_vector_dir, exist_ok=True)
            
            logger.info("Data directories created successfully")
            
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            raise
    
    def load_pdf_documents(self, pdf_path: str) -> List[str]:
        """
        Load and extract text from PDF documents
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            List[str]: List of extracted text chunks
        """
        try:
            # Load PDF using PyPDFLoader
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # Extract text content from documents
            texts = [doc.page_content for doc in documents]
            
            logger.info(f"Successfully loaded PDF: {pdf_path}")
            return texts
            
        except Exception as e:
            logger.error(f"Error loading PDF {pdf_path}: {e}")
            raise
    
    def split_text_into_chunks(self, texts: List[str]) -> List[str]:
        """
        Split text into smaller chunks for processing
        
        Args:
            texts (List[str]): List of text documents
            
        Returns:
            List[str]: List of text chunks
        """
        try:
            # Create text splitter with specified parameters
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]  # Split on paragraphs, lines, words
            )
            
            # Split all texts into chunks
            chunks = []
            for text in texts:
                text_chunks = text_splitter.split_text(text)
                chunks.extend(text_chunks)
            
            logger.info(f"Split {len(texts)} documents into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error splitting text: {e}")
            raise
    
    def create_product_vectorstore(self, product_name: str, chunks: List[str], 
                                 save_path: Optional[str] = None) -> FAISS:
        """
        Create FAISS vector database for a specific product
        
        Args:
            product_name (str): Name of the IOT product
            chunks (List[str]): Text chunks for the product
            save_path (Optional[str]): Path to save the vector database
            
        Returns:
            FAISS: FAISS vector database instance
        """
        try:
            # Create FAISS vector database from text chunks
            vectorstore = FAISS.from_texts(
                texts=chunks,
                embedding=self.embeddings
            )
            
            # Save vector database if path provided
            if save_path:
                vectorstore.save_local(save_path)
                logger.info(f"Vector database saved to: {save_path}")
            
            logger.info(f"Created vector database for {product_name} with {len(chunks)} chunks")
            return vectorstore
            
        except Exception as e:
            logger.error(f"Error creating vector database for {product_name}: {e}")
            raise
    
    def process_product_documents(self) -> Dict[str, FAISS]:
        """
        Process all IOT product documents and create vector databases
        
        Returns:
            Dict[str, FAISS]: Dictionary mapping product names to their vector databases
        """
        try:
            product_vectorstores = {}
            
            # Process each IOT product
            for product in IOT_PRODUCTS:
                product_name = product["name"]
                product_file = f"{product_name.replace(' ', '_').lower()}.pdf"
                pdf_path = os.path.join(PRODUCT_DOCS_DIR, product_file)
                
                # Check if PDF exists
                if not os.path.exists(pdf_path):
                    logger.warning(f"PDF not found for {product_name}: {pdf_path}")
                    logger.info(f"Please add {product_file} to the {PRODUCT_DOCS_DIR} directory")
                    continue
                
                # Load and process PDF
                texts = self.load_pdf_documents(pdf_path)
                chunks = self.split_text_into_chunks(texts)
                
                # Create vector database path
                vector_db_path = os.path.join("data", "vector_db", 
                                            product_name.replace(" ", "_").lower())
                
                # Create FAISS vector database
                vectorstore = self.create_product_vectorstore(
                    product_name, chunks, vector_db_path
                )
                
                product_vectorstores[product_name] = vectorstore
                logger.info(f"Processed {product_name}: {len(chunks)} chunks")
            
            self.product_vectorstores = product_vectorstores
            return product_vectorstores
            
        except Exception as e:
            logger.error(f"Error processing product documents: {e}")
            raise
    
    def create_combined_vectorstore(self) -> FAISS:
        """
        Create a combined vector database for all products
        
        This allows searching across all IOT products simultaneously
        for general queries or product listing.
        
        Returns:
            FAISS: Combined vector database
        """
        try:
            if not self.product_vectorstores:
                raise ValueError("No product vectorstores available. Process documents first.")
            
            # Combine all vector databases
            combined_vectorstore = None
            
            for product_name, vectorstore in self.product_vectorstores.items():
                if combined_vectorstore is None:
                    combined_vectorstore = vectorstore
                else:
                    # Merge vector databases
                    combined_vectorstore.merge_from(vectorstore)
            
            # Save combined vector database
            combined_path = os.path.join("data", "vector_db", "combined")
            combined_vectorstore.save_local(combined_path)
            
            self.combined_vectorstore = combined_vectorstore
            logger.info("Created combined vector database for all products")
            return combined_vectorstore
            
        except Exception as e:
            logger.error(f"Error creating combined vector database: {e}")
            raise
    
    def load_existing_vectorstores(self) -> Dict[str, FAISS]:
        """
        Load existing vector databases from disk
        
        Returns:
            Dict[str, FAISS]: Dictionary of loaded vector databases
        """
        try:
            product_vectorstores = {}
            vector_db_dir = os.path.join("data", "vector_db")
            
            # Load product-specific vector databases
            for product in IOT_PRODUCTS:
                product_name = product["name"]
                product_vector_path = os.path.join(vector_db_dir, 
                                                product_name.replace(" ", "_").lower())
                
                if os.path.exists(product_vector_path):
                    try:
                        vectorstore = FAISS.load_local(
                            product_vector_path, 
                            self.embeddings,
                            allow_dangerous_deserialization=True
                        )
                        product_vectorstores[product_name] = vectorstore
                        logger.info(f"Loaded vector database for {product_name}")
                    except Exception as e:
                        logger.warning(f"Could not load vector database for {product_name}: {e}")
                else:
                    logger.warning(f"No vector database found for {product_name}")
            
            # Load combined vector database
            combined_path = os.path.join(vector_db_dir, "combined")
            if os.path.exists(combined_path):
                try:
                    self.combined_vectorstore = FAISS.load_local(
                        combined_path, 
                        self.embeddings,
                        allow_dangerous_deserialization=True
                    )
                    logger.info("Loaded combined vector database")
                except Exception as e:
                    logger.warning(f"Could not load combined vector database: {e}")
            
            self.product_vectorstores = product_vectorstores
            return product_vectorstores
            
        except Exception as e:
            logger.error(f"Error loading vector databases: {e}")
            raise
    
    def get_product_retriever(self, product_name: str, k: int = 4) -> Optional[FAISS]:
        """
        Get retriever for a specific product
        
        Args:
            product_name (str): Name of the IOT product
            k (int): Number of chunks to retrieve
            
        Returns:
            Optional[FAISS]: FAISS retriever for the product
        """
        try:
            if product_name in self.product_vectorstores:
                vectorstore = self.product_vectorstores[product_name]
                return vectorstore.as_retriever(search_kwargs={"k": k})
            else:
                logger.warning(f"No vector database found for product: {product_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting retriever for {product_name}: {e}")
            return None
    
    def get_combined_retriever(self, k: int = 4) -> Optional[FAISS]:
        """
        Get retriever for all products combined
        
        Args:
            k (int): Number of chunks to retrieve
            
        Returns:
            Optional[FAISS]: Combined FAISS retriever
        """
        try:
            if self.combined_vectorstore:
                return self.combined_vectorstore.as_retriever(search_kwargs={"k": k})
            else:
                logger.warning("No combined vector database available")
                return None
                
        except Exception as e:
            logger.error(f"Error getting combined retriever: {e}")
            return None
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during processing"""
        try:
            temp_dir = "temp"
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")

# Global document processor instance
document_processor = DocumentProcessor() 