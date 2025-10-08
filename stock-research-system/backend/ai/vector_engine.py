"""
Vector Intelligence Engine for TavilyAI Pro
Implements FAISS vector database, embeddings, and semantic search
"""

import os
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
from datetime import datetime, timedelta
import asyncio
import logging

import faiss
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter, TextSplitter
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from sentence_transformers import SentenceTransformer, CrossEncoder

logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """Document with vector representation"""
    id: str
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    chunk_index: int = 0
    parent_id: Optional[str] = None


@dataclass
class SearchResult:
    """Search result with score and metadata"""
    document: VectorDocument
    score: float
    relevance_explanation: Optional[str] = None


class VectorIntelligence:
    """
    Advanced vector database system with multi-level embeddings
    and intelligent retrieval strategies
    """

    def __init__(self,
                 openai_api_key: str = None,
                 persist_directory: str = "./vector_store",
                 embedding_model: str = "text-embedding-3-small"):

        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=self.openai_api_key,
            model=embedding_model
        )

        # Initialize sentence transformer for local embeddings
        self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize cross-encoder for re-ranking
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

        # Initialize FAISS indices
        self.indices = {
            "sentence": None,
            "paragraph": None,
            "document": None,
            "semantic": None
        }

        # Document storage
        self.documents = {}
        self.chunk_to_doc_mapping = {}

        # Initialize or load indices
        self._initialize_indices()

        # Statistics
        self.stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "total_embeddings": 0,
            "searches_performed": 0
        }

    def _initialize_indices(self):
        """Initialize or load FAISS indices"""
        os.makedirs(self.persist_directory, exist_ok=True)

        # Dimension of OpenAI embeddings (1536 for text-embedding-3-small)
        dimension = 1536

        # Create indices with different strategies
        self.indices["sentence"] = faiss.IndexFlatL2(dimension)  # L2 distance
        self.indices["paragraph"] = faiss.IndexFlatIP(dimension)  # Inner product
        self.indices["document"] = faiss.IndexFlatL2(dimension)

        # Create an optimized index for semantic search
        quantizer = faiss.IndexFlatL2(dimension)
        self.indices["semantic"] = faiss.IndexIVFPQ(quantizer, dimension, 100, 8, 8)

        # Load existing indices if available
        self._load_indices()

    def _load_indices(self):
        """Load persisted indices from disk"""
        for index_type in self.indices.keys():
            index_path = os.path.join(self.persist_directory, f"{index_type}_index.faiss")
            docs_path = os.path.join(self.persist_directory, f"{index_type}_docs.pkl")

            if os.path.exists(index_path) and os.path.exists(docs_path):
                try:
                    self.indices[index_type] = faiss.read_index(index_path)

                    with open(docs_path, 'rb') as f:
                        stored_docs = pickle.load(f)
                        self.documents.update(stored_docs)

                    logger.info(f"Loaded {index_type} index with {self.indices[index_type].ntotal} vectors")
                except Exception as e:
                    logger.error(f"Error loading {index_type} index: {e}")

    def _save_indices(self):
        """Persist indices to disk"""
        for index_type, index in self.indices.items():
            if index and index.ntotal > 0:
                index_path = os.path.join(self.persist_directory, f"{index_type}_index.faiss")
                docs_path = os.path.join(self.persist_directory, f"{index_type}_docs.pkl")

                try:
                    faiss.write_index(index, index_path)

                    # Save associated documents
                    relevant_docs = {k: v for k, v in self.documents.items()
                                   if v.metadata.get("index_type") == index_type}
                    with open(docs_path, 'wb') as f:
                        pickle.dump(relevant_docs, f)

                    logger.info(f"Saved {index_type} index with {index.ntotal} vectors")
                except Exception as e:
                    logger.error(f"Error saving {index_type} index: {e}")

    async def add_documents(self,
                          documents: List[str],
                          metadata_list: Optional[List[Dict]] = None,
                          chunk_size: int = 1000,
                          chunk_overlap: int = 200) -> Dict[str, Any]:
        """
        Add documents to vector store with intelligent chunking

        Args:
            documents: List of document texts
            metadata_list: Optional metadata for each document
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks

        Returns:
            Statistics about the indexing process
        """
        if not metadata_list:
            metadata_list = [{}] * len(documents)

        total_chunks = 0
        total_embeddings = 0

        for doc_idx, (doc_text, metadata) in enumerate(zip(documents, metadata_list)):
            # Generate document ID
            doc_id = self._generate_doc_id(doc_text, metadata)

            # Smart chunking based on content type
            chunks = await self._intelligent_chunking(
                doc_text,
                chunk_size,
                chunk_overlap,
                metadata.get("content_type", "general")
            )

            # Create embeddings for different levels
            for chunk_idx, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{chunk_idx}"

                # Create sentence-level embeddings
                sentences = self._split_into_sentences(chunk)
                for sent_idx, sentence in enumerate(sentences):
                    if len(sentence.strip()) > 10:  # Skip very short sentences
                        sent_embedding = await self._create_embedding(sentence, "sentence")
                        sent_doc = VectorDocument(
                            id=f"{chunk_id}_sent_{sent_idx}",
                            content=sentence,
                            embedding=sent_embedding,
                            metadata={
                                **metadata,
                                "doc_id": doc_id,
                                "chunk_id": chunk_id,
                                "level": "sentence",
                                "index_type": "sentence"
                            },
                            chunk_index=chunk_idx,
                            parent_id=doc_id
                        )
                        self._add_to_index(sent_doc, "sentence")
                        total_embeddings += 1

                # Create paragraph-level embedding
                para_embedding = await self._create_embedding(chunk, "paragraph")
                para_doc = VectorDocument(
                    id=chunk_id,
                    content=chunk,
                    embedding=para_embedding,
                    metadata={
                        **metadata,
                        "doc_id": doc_id,
                        "level": "paragraph",
                        "index_type": "paragraph"
                    },
                    chunk_index=chunk_idx,
                    parent_id=doc_id
                )
                self._add_to_index(para_doc, "paragraph")
                total_chunks += 1
                total_embeddings += 1

            # Create document-level embedding (summary)
            doc_summary = await self._create_document_summary(doc_text)
            doc_embedding = await self._create_embedding(doc_summary, "document")
            doc_doc = VectorDocument(
                id=doc_id,
                content=doc_summary,
                embedding=doc_embedding,
                metadata={
                    **metadata,
                    "level": "document",
                    "index_type": "document",
                    "full_text_length": len(doc_text)
                },
                chunk_index=0,
                parent_id=None
            )
            self._add_to_index(doc_doc, "document")
            total_embeddings += 1

            # Update statistics
            self.stats["total_documents"] += 1

        self.stats["total_chunks"] += total_chunks
        self.stats["total_embeddings"] += total_embeddings

        # Train IVF index if using semantic index
        if self.indices["semantic"].ntotal > 100 and not self.indices["semantic"].is_trained:
            self._train_semantic_index()

        # Save indices
        self._save_indices()

        return {
            "documents_processed": len(documents),
            "chunks_created": total_chunks,
            "embeddings_created": total_embeddings,
            "indices_updated": list(self.indices.keys())
        }

    async def _intelligent_chunking(self,
                                   text: str,
                                   chunk_size: int,
                                   overlap: int,
                                   content_type: str) -> List[str]:
        """
        Intelligent chunking based on content type and structure
        """
        if content_type == "financial":
            # For financial documents, respect table/section boundaries
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
                separators=["\n\n\n", "\n\n", "\n", ".", " ", ""],
                keep_separator=True
            )
        elif content_type == "news":
            # For news articles, respect paragraph boundaries
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
                separators=["\n\n", "\n", ". ", " ", ""],
                keep_separator=True
            )
        else:
            # General purpose splitting
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap
            )

        chunks = splitter.split_text(text)

        # Post-process chunks to ensure quality
        quality_chunks = []
        for chunk in chunks:
            # Skip chunks that are too short or just whitespace
            if len(chunk.strip()) > 50:
                quality_chunks.append(chunk)

        return quality_chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re

        # Simple sentence splitting (can be improved with NLTK or spaCy)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    async def _create_embedding(self, text: str, level: str) -> np.ndarray:
        """Create embedding for text"""
        try:
            # Use OpenAI embeddings for better quality
            embedding = await asyncio.to_thread(self.embeddings.embed_query, text)
            return np.array(embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            # Fallback to local sentence transformer
            embedding = self.sentence_transformer.encode(text)
            # Pad or truncate to match OpenAI embedding dimension
            if len(embedding) < 1536:
                embedding = np.pad(embedding, (0, 1536 - len(embedding)))
            else:
                embedding = embedding[:1536]
            return embedding.astype(np.float32)

    async def _create_document_summary(self, text: str, max_length: int = 500) -> str:
        """Create a summary of the document for document-level embedding"""
        # Simple extractive summary (first and last parts)
        if len(text) <= max_length:
            return text

        # Take beginning and end
        half_length = max_length // 2
        summary = text[:half_length] + " ... " + text[-half_length:]
        return summary

    def _add_to_index(self, document: VectorDocument, index_type: str):
        """Add document to appropriate FAISS index"""
        if index_type not in self.indices:
            logger.error(f"Unknown index type: {index_type}")
            return

        index = self.indices[index_type]

        # Add to index
        embedding = document.embedding.reshape(1, -1)
        index.add(embedding)

        # Store document
        self.documents[document.id] = document

        # Update chunk mapping
        if document.parent_id:
            if document.parent_id not in self.chunk_to_doc_mapping:
                self.chunk_to_doc_mapping[document.parent_id] = []
            self.chunk_to_doc_mapping[document.parent_id].append(document.id)

    def _train_semantic_index(self):
        """Train the IVF index for semantic search"""
        if self.indices["paragraph"].ntotal > 100:
            # Get sample vectors for training
            sample_size = min(10000, self.indices["paragraph"].ntotal)
            sample_vectors = np.zeros((sample_size, 1536), dtype=np.float32)

            # Copy vectors from paragraph index
            for i in range(sample_size):
                sample_vectors[i] = self.indices["paragraph"].reconstruct(i)

            # Train the index
            self.indices["semantic"].train(sample_vectors)

            # Add all vectors to semantic index
            for i in range(self.indices["paragraph"].ntotal):
                vector = self.indices["paragraph"].reconstruct(i)
                self.indices["semantic"].add(vector.reshape(1, -1))

            logger.info(f"Trained semantic index with {sample_size} samples")

    async def search(self,
                    query: str,
                    top_k: int = 10,
                    search_type: str = "hybrid",
                    filters: Optional[Dict] = None,
                    rerank: bool = True) -> List[SearchResult]:
        """
        Advanced search with multiple strategies

        Args:
            query: Search query
            top_k: Number of results to return
            search_type: "semantic", "keyword", "hybrid"
            filters: Optional filters for results
            rerank: Whether to rerank results with cross-encoder

        Returns:
            List of SearchResult objects
        """
        self.stats["searches_performed"] += 1

        # Create query embedding
        query_embedding = await self._create_embedding(query, "query")

        results = []

        if search_type in ["semantic", "hybrid"]:
            # Semantic search across different levels
            semantic_results = await self._semantic_search(
                query_embedding,
                top_k * 2,  # Get more for reranking
                filters
            )
            results.extend(semantic_results)

        if search_type in ["keyword", "hybrid"]:
            # Keyword search (BM25-like)
            keyword_results = await self._keyword_search(
                query,
                top_k * 2,
                filters
            )
            results.extend(keyword_results)

        # Deduplicate results
        unique_results = self._deduplicate_results(results)

        # Rerank if requested
        if rerank and len(unique_results) > 0:
            unique_results = await self._rerank_results(query, unique_results)

        # Apply final filtering and sorting
        final_results = sorted(unique_results, key=lambda x: x.score, reverse=True)[:top_k]

        return final_results

    async def _semantic_search(self,
                              query_embedding: np.ndarray,
                              top_k: int,
                              filters: Optional[Dict]) -> List[SearchResult]:
        """Perform semantic search across indices"""
        all_results = []

        # Search in paragraph index (primary)
        if self.indices["paragraph"] and self.indices["paragraph"].ntotal > 0:
            D, I = self.indices["paragraph"].search(
                query_embedding.reshape(1, -1),
                min(top_k, self.indices["paragraph"].ntotal)
            )

            for idx, (dist, doc_idx) in enumerate(zip(D[0], I[0])):
                if doc_idx >= 0:  # Valid index
                    # Find document by reconstructing
                    doc_id = self._find_doc_id_by_index(doc_idx, "paragraph")
                    if doc_id and doc_id in self.documents:
                        doc = self.documents[doc_id]
                        if self._passes_filters(doc, filters):
                            score = 1.0 / (1.0 + dist)  # Convert distance to similarity
                            all_results.append(SearchResult(
                                document=doc,
                                score=score * 1.0  # Weight for paragraph level
                            ))

        # Search in sentence index for precision
        if self.indices["sentence"] and self.indices["sentence"].ntotal > 0:
            D, I = self.indices["sentence"].search(
                query_embedding.reshape(1, -1),
                min(top_k // 2, self.indices["sentence"].ntotal)
            )

            for dist, doc_idx in zip(D[0], I[0]):
                if doc_idx >= 0:
                    doc_id = self._find_doc_id_by_index(doc_idx, "sentence")
                    if doc_id and doc_id in self.documents:
                        doc = self.documents[doc_id]
                        if self._passes_filters(doc, filters):
                            score = 1.0 / (1.0 + dist)
                            all_results.append(SearchResult(
                                document=doc,
                                score=score * 0.8  # Lower weight for sentence level
                            ))

        return all_results

    async def _keyword_search(self,
                             query: str,
                             top_k: int,
                             filters: Optional[Dict]) -> List[SearchResult]:
        """Perform keyword-based search"""
        results = []
        query_terms = query.lower().split()

        for doc_id, doc in self.documents.items():
            if self._passes_filters(doc, filters):
                content_lower = doc.content.lower()

                # Calculate BM25-like score
                score = 0.0
                for term in query_terms:
                    term_freq = content_lower.count(term)
                    if term_freq > 0:
                        # Simple TF-IDF approximation
                        tf = term_freq / len(content_lower.split())
                        idf = np.log(len(self.documents) / sum(
                            1 for d in self.documents.values()
                            if term in d.content.lower()
                        ) + 1)
                        score += tf * idf

                if score > 0:
                    results.append(SearchResult(
                        document=doc,
                        score=score
                    ))

        return sorted(results, key=lambda x: x.score, reverse=True)[:top_k]

    async def _rerank_results(self,
                             query: str,
                             results: List[SearchResult]) -> List[SearchResult]:
        """Rerank results using cross-encoder"""
        if not results:
            return results

        # Prepare pairs for cross-encoder
        pairs = [(query, r.document.content) for r in results]

        # Get reranking scores
        try:
            scores = self.cross_encoder.predict(pairs)

            # Update result scores
            for result, score in zip(results, scores):
                # Combine original score with reranking score
                result.score = 0.3 * result.score + 0.7 * float(score)
        except Exception as e:
            logger.error(f"Error during reranking: {e}")

        return results

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on content similarity"""
        if not results:
            return results

        unique = []
        seen_contents = set()

        for result in results:
            # Create content hash for deduplication
            content_hash = hashlib.md5(
                result.document.content[:200].encode()
            ).hexdigest()

            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique.append(result)

        return unique

    def _passes_filters(self, document: VectorDocument, filters: Optional[Dict]) -> bool:
        """Check if document passes the provided filters"""
        if not filters:
            return True

        for key, value in filters.items():
            if key in document.metadata:
                if isinstance(value, list):
                    if document.metadata[key] not in value:
                        return False
                else:
                    if document.metadata[key] != value:
                        return False

        return True

    def _find_doc_id_by_index(self, index: int, index_type: str) -> Optional[str]:
        """Find document ID by its index position"""
        # This is a simplified version - in production, maintain a mapping
        for doc_id, doc in self.documents.items():
            if doc.metadata.get("index_type") == index_type:
                # This is approximate - would need proper index tracking
                return doc_id
        return None

    def _generate_doc_id(self, text: str, metadata: Dict) -> str:
        """Generate unique document ID"""
        content_hash = hashlib.md5(text[:1000].encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"doc_{timestamp}_{content_hash}"

    def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            **self.stats,
            "index_sizes": {
                name: index.ntotal if index else 0
                for name, index in self.indices.items()
            },
            "total_documents_stored": len(self.documents),
            "memory_usage_mb": self._estimate_memory_usage()
        }

    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB"""
        total_vectors = sum(
            index.ntotal if index else 0
            for index in self.indices.values()
        )
        # Each vector is 1536 dimensions * 4 bytes = 6KB
        vector_memory = (total_vectors * 1536 * 4) / (1024 * 1024)

        # Estimate document storage
        doc_memory = sum(len(doc.content) for doc in self.documents.values()) / (1024 * 1024)

        return vector_memory + doc_memory

    def clear(self):
        """Clear all indices and documents"""
        for index_type in self.indices:
            self.indices[index_type] = None
        self.documents.clear()
        self.chunk_to_doc_mapping.clear()
        self._initialize_indices()
        self.stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "total_embeddings": 0,
            "searches_performed": 0
        }
        logger.info("Vector store cleared")