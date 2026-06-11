from src.ingestion.scraper import F1LiveWebScraper
import os

class F1VectorStoreManager:
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "f1_regulations"):
        # Ensure local DB directory exists
        os.makedirs(db_path, exist_ok=True)

        try:
            import chromadb
            from chromadb.utils import embedding_functions
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

    def add_documents(self, chunks: list[str], source_name: str):
        """Indexes text chunks into the vector database with unique IDs and metadata."""
        if not chunks:
            return
            
        ids = [f"{source_name}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": source_name} for _ in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )
        print(f"Successfully indexed {len(chunks)} chunks from {source_name} into VectorDB.")

    def query_similar_context(self, user_query: str, n_results: int = 3) -> str:
        """Searches ChromaDB for the most contextually relevant text chunks."""
        results = self.collection.query(
            query_texts=[user_query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        retrieved_texts = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        combined = list(zip(retrieved_texts, metadatas))
        combined.sort(key=lambda item: 0 if item[1].get("source_url") else 1)

        ordered_texts = [item[0] for item in combined]
        return "\n\n--- Context Block ---\n".join(ordered_texts)
    
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
        # Keeps your manually seeded text clean
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
        chunker = DocumentChunker(chunk_size=800, chunk_overlap=150)
        web_chunks = chunker.chunk_text(raw_web_text)
        
        # 3. Store securely inside our persistent vector database layer
        ids = [f"web_{source_id}_chunk_{i}" for i in range(len(web_chunks))]
        metadatas = [{"source_url": url} for _ in range(len(web_chunks))]
        
        self.collection.upsert(
            documents=web_chunks,
            ids=ids,
            metadatas=metadatas
        )
        print(f"💾 [DATABASE] Vectorized and stored {len(web_chunks)} live web chunks into ChromaDB.")
        return True