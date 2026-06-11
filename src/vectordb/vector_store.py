from src.ingestion.scraper import F1LiveWebScraper
import os
import re
from typing import List, Tuple


class F1VectorStoreManager:
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "f1_regulations"):
        # Ensure local DB directory exists
        os.makedirs(db_path, exist_ok=True)

        try:
            import chromadb     #type: ignore
            from chromadb.utils import embedding_functions #type: ignore
        except ImportError as exc:
            raise ImportError(
                "The chromadb package is required to use F1VectorStoreManager. "
                "Install it with `pip install chromadb` and ensure your environment is activated."
            ) from exc

        self.chromadb = chromadb
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self.client = self.chromadb.PersistentClient(path=db_path)

        # Get or create our dedicated vector collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text for BM25-style matching."""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'was', 'be', 'are'}
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if w not in stop_words and len(w) > 2]

    def _bm25_score(self, document: str, query_keywords: List[str]) -> float:
        """Calculate simple BM25-style score for keyword matching."""
        doc_keywords = self._extract_keywords(document)
        score = 0
        for keyword in query_keywords:
            if keyword in doc_keywords:
                # Boost score for exact matches
                score += doc_keywords.count(keyword) * 2
        return score

    def _rerank_results(self, results: dict, query: str, top_k: int = 5) -> List[Tuple[str, dict, float]]:
        """Rerank search results by combining semantic and keyword scores."""
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        query_keywords = self._extract_keywords(query)
        ranked = []
        
        for i, (doc, meta, distance) in enumerate(zip(documents, metadatas, distances)):
            # Semantic score (lower distance = better, normalize to 0-1)
            semantic_score = 1 / (1 + distance)
            
            # Keyword score
            keyword_score = self._bm25_score(doc, query_keywords) / (len(doc) / 100 + 1)
            
            # Combined score (weighted)
            combined_score = (0.6 * semantic_score) + (0.4 * keyword_score)
            
            ranked.append((doc, meta, combined_score))
        
        # Sort by combined score and return top-k
        ranked.sort(key=lambda x: x[2], reverse=True)
        return ranked[:top_k]

    def add_documents(self, chunks: list[str], source_name: str):
        """Indexes text chunks into the vector database with unique IDs and metadata."""
        if not chunks:
            return
            
        ids = [f"{source_name}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": source_name, "chunk_idx": i} for i, _ in enumerate(chunks)]
        
        self.collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )
        print(f"✅ Successfully indexed {len(chunks)} chunks from {source_name} into VectorDB.")

    def query_similar_context(self, user_query: str, n_results: int = 5) -> Tuple[str, List[dict]]:
        """
        Searches ChromaDB using hybrid search (semantic + keyword matching).
        Returns combined context and list of metadata for traceability.
        """
        # Perform semantic search
        results = self.collection.query(
            query_texts=[user_query],
            n_results=min(n_results * 2, 20),  # Get more results for reranking
            include=["documents", "metadatas", "distances"]
        )

        # Rerank using hybrid scoring
        ranked_results = self._rerank_results(results, user_query, top_k=n_results)
        
        if not ranked_results:
            return "❌ No relevant context found in database.", []
        
        # Sort by source preference (live URLs > historical)
        ranked_results.sort(key=lambda x: (0 if x[1].get("source_url") else 1, -x[2]))
        
        # Combine context
        combined_context = "\n\n--- Context Block ---\n".join([doc for doc, _, _ in ranked_results])
        metadata_list = [meta for _, meta, _ in ranked_results]
        
        return combined_context, metadata_list
    
    def add_historical_stats(self):
        """Seeds historical circuit data into a clean text segment for RAG retrieval."""
        catalunya_stats = """
        CIRCUIT: Circuit de Barcelona-Catalunya (Spanish Grand Prix)
        LAST 5 YEARS PODIUM FINISHES:
        - 2025: 1st Oscar Piastri, 2nd Lando Norris, 3rd Charles Leclerc
        - 2024: 1st Max Verstappen, 2nd Lando Norris, 3rd Lewis Hamilton
        - 2023: 1st Max Verstappen, 2nd Lewis Hamilton, 3rd George Russell
        - 2022: 1st Max Verstappen, 2nd Sergio Pérez, 3rd George Russell
        - 2021: 1st Lewis Hamilton, 2nd Max Verstappen, 3rd Valtteri Bottas
        
        POLE POSITIONS (LAST 5 YEARS):
        - 2025: Lando Norris (McLaren) | 1:11.546
        - 2024: Lando Norris (McLaren) | 1:11.383
        - 2023: Max Verstappen (Red Bull) | 1:12.272
        - 2022: Charles Leclerc (Ferrari) | 1:18.750
        - 2021: Lewis Hamilton (Mercedes) | 1:16.741

        FASTEST LAP RECORDS (LAST 5 YEARS):
        - 2024: Lando Norris (McLaren) | 1:17.115
        - 2023: Max Verstappen (Red Bull) | 1:16.330 (Current Official Race Lap Record)
        - 2022: Sergio Pérez (Red Bull) | 1:24.108
        - 2021: Max Verstappen (Red Bull) | 1:18.149
        """
        self.collection.upsert(
            documents=[catalunya_stats.strip()],
            ids=["stats_catalunya"],
            metadatas=[{"source": "historical_database"}]
        )
        print("📊 Historical F1 statistics successfully synchronized with ChromaDB.")

    def ingest_live_web_data(self, url: str, source_id: str):
        """
        Dynamically drives the scraper, extracts text metrics, 
        and inserts them straight into the persistent mathematical vector rows.
        """
        from src.chunking.chunker import DocumentChunker
        
        # 1. Trigger the live web scraper tool using the passed URL parameter
        scraper = F1LiveWebScraper()
        raw_web_text = scraper.fetch_and_extract_text(url)
        
        if not raw_web_text:
            print("⚠️ Web ingestion aborted. No text data retrieved.")
            return False
            
        # 2. Slice the scraped data into manageable paragraphs
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
        web_chunks = chunker.chunk_text(raw_web_text)
        
        # 3. Store securely inside our persistent vector database layer
        ids = [f"web_{source_id}_chunk_{i}" for i in range(len(web_chunks))]
        metadatas = [{"source_url": url, "chunk_idx": i} for i, _ in enumerate(web_chunks)]
        
        self.collection.upsert(
            documents=web_chunks,
            ids=ids,
            metadatas=metadatas
        )
        print(f"💾 [DATABASE] Vectorized and stored {len(web_chunks)} live web chunks into ChromaDB.")
        return True