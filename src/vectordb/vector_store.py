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
        """Seeds expansive historical F1 statistics and global circuit logs (2020 - 2025)."""
        f1_historical_dump = {
            # === SEASON SUMMARY DUMPS ===
            "stats_2025_season": """
            YEAR: 2025 Season Summary
            DRIVER CHAMPION: Max Verstappen (Red Bull Racing) - Secures his 5th consecutive World Championship.
            CONSTRUCTOR CHAMPION: McLaren Racing (Driven by Lando Norris and Oscar Piastri).
            SEASON BREAKDOWN: A highly contentious fight between McLaren, Ferrari, and Red Bull. Oscar Piastri won major historical rounds including the Dutch GP, and teammate Lando Norris mounted a fierce campaign securing wins in Monza, Zandvoort, and Interlagos. Ferrari pushed hard via Charles Leclerc and Carlos Sainz Jr. Mercedes showcased strong structural performances from George Russell and rookie Andrea Kimi Antonelli.
            """,
            "stats_2024_season": """
            YEAR: 2024 Season Summary
            DRIVER CHAMPION: Max Verstappen (Red Bull Racing) - Won his 4th World Championship title.
            CONSTRUCTOR CHAMPION: McLaren Racing.
            SEASON BREAKDOWN: Red Bull dominated early on, but McLaren, Ferrari, and Mercedes closed the performance margin rapidly by mid-season. Lando Norris achieved his maiden win in Miami, starting a massive resurgence that pushed McLaren ahead of Red Bull in the Constructors' Championship standings. Lewis Hamilton completed his historic final year with Mercedes, securing emotional final home wins at Silverstone and Spa before his transfer to Scuderia Ferrari.
            """,
            "stats_2023_season": """
            YEAR: 2023 Season Summary
            DRIVER CHAMPION: Max Verstappen (Red Bull Racing) - Historic 3rd consecutive title.
            CONSTRUCTOR CHAMPION: Red Bull Racing (RB19).
            SEASON BREAKDOWN: Arguably the most dominant solo display in Formula 1 history. Max Verstappen secured 19 wins out of 22 Grands Prix. Red Bull Racing broke records by winning 21 out of 22 total races. Carlos Sainz Jr. in the Ferrari was the only non-Red Bull driver to win a race, taking the top spot at the Singapore Grand Prix.
            """,
            "stats_2022_season": """
            YEAR: 2022 Season Summary
            DRIVER CHAMPION: Max Verstappen (Red Bull Racing) - 2nd World Championship title.
            CONSTRUCTOR CHAMPION: Red Bull Racing.
            SEASON BREAKDOWN: Ground-effect aero regulations were fully introduced, fundamentally shifting team competitive balances. Ferrari started strongly with Charles Leclerc winning early rounds, but reliability flaws and strategic errors allowed Max Verstappen and Red Bull to pull away comfortably to close out both title campaigns. Mercedes struggled deeply with structural "porpoising" aerodynamic complications, ending their consecutive constructor streak.
            """,
            "stats_2021_season": """
            YEAR: 2021 Season Summary
            DRIVER CHAMPION: Max Verstappen (Red Bull Racing) - Maiden World Championship title.
            CONSTRUCTOR CHAMPION: Mercedes AMG Petronas (8th consecutive team title).
            SEASON BREAKDOWN: A historic, intense season-long rivalry between Max Verstappen and Lewis Hamilton. The two drivers entered the final race at Abu Dhabi tied exactly on points. The championship was decided on a controversial final-lap restart under a safety car order managed by Race Director Michael Masi, allowing Verstappen to overtake Hamilton to seal his first title.
            """,
            "stats_2020_season": """
            YEAR: 2020 Season Summary
            DRIVER CHAMPION: Lewis Hamilton (Mercedes) - Equaled Michael Schumacher's all-time record of 7 World Titles.
            CONSTRUCTOR CHAMPION: Mercedes AMG Petronas.
            SEASON BREAKDOWN: The season layout was heavily disrupted and altered due to the global COVID-19 pandemic, leading to a shortened 17-race calendar with doubleheaders at venues like Spielberg and Silverstone. Mercedes dominated completely with the dual-axis steering (DAS) equipped W11 car. Lewis Hamilton broke the all-time race wins record, surpassing Schumacher's 91 victories.
            """,

            # === GLOBAL CIRCUIT SPECIFIC DUMPS ===
            "circuit_bahrain": """
            CIRCUIT: Bahrain International Circuit (Sakhir)
            TYPE: Permanent Race Track (Desert)
            KEY CHARACTERISTICS: Highly abrasive asphalt, heavy traction zones, and major braking stability requirements.
            WINNERS (2020-2025):
            - 2025: Max Verstappen (Red Bull)
            - 2024: Max Verstappen (Red Bull)
            - 2023: Max Verstappen (Red Bull)
            - 2022: Charles Leclerc (Ferrari)
            - 2021: Lewis Hamilton (Mercedes)
            - 2020: Lewis Hamilton (Mercedes) [Note: Sergio Pérez won the 2020 Sakhir GP held on the Outer Circuit layout].
            """,
            "circuit_monaco": """
            CIRCUIT: Circuit de Monaco (Monte Carlo)
            TYPE: Tight Street Circuit
            KEY CHARACTERISTICS: Narrow barrier-lined track, extremely low overtaking index, qualifying is crucial.
            WINNERS (2021-2025) [Note: 2020 cancelled]:
            - 2025: Charles Leclerc (Ferrari)
            - 2024: Charles Leclerc (Ferrari) - Historic emotional home victory.
            - 2023: Max Verstappen (Red Bull)
            - 2022: Sergio Pérez (Red Bull)
            - 2021: Max Verstappen (Red Bull)
            """,
            "circuit_catalunya": """
            CIRCUIT: Circuit de Barcelona-Catalunya (Spanish Grand Prix)
            TYPE: Permanent Grand Prix Circuit
            KEY CHARACTERISTICS: High-speed aerodynamic testing layout, prominent long main straight. Chicana removed in 2023 to restore high-speed final sector.
            WINNERS (2020-2025):
            - 2025: Oscar Piastri (McLaren)
            - 2024: Max Verstappen (Red Bull)
            - 2023: Max Verstappen (Red Bull)
            - 2022: Max Verstappen (Red Bull)
            - 2021: Lewis Hamilton (Mercedes)
            - 2020: Lewis Hamilton (Mercedes)
            """,
            "circuit_silverstone": """
            CIRCUIT: Silverstone Circuit (British Grand Prix)
            TYPE: High-Speed Permanent Track
            KEY CHARACTERISTICS: Iconic ultra-fast sequence (Maggotts, Becketts, Chapel). Incredible aerodynamic load demands.
            WINNERS (2020-2025):
            - 2025: Lando Norris (McLaren)
            - 2024: Lewis Hamilton (Mercedes) - Broke win drought with iconic 9th home victory.
            - 2023: Max Verstappen (Red Bull)
            - 2022: Carlos Sainz Jr. (Ferrari) - Maiden career F1 victory.
            - 2021: Lewis Hamilton (Mercedes) [Controversial opening lap crash with Verstappen].
            - 2020: Lewis Hamilton (Mercedes) [Won on 3 wheels due to tyre puncture] / Max Verstappen (Red Bull) [70th Anniversary GP].
            """,
            "circuit_spa": """
            CIRCUIT: Circuit de Spa-Francorchamps (Belgian Grand Prix)
            TYPE: High-Speed Ardennes Track
            KEY CHARACTERISTICS: Longest track layout on calendar. Features 'Eau Rouge/Raidillon'. Highly unpredictable microclimates and heavy rain risks.
            WINNERS (2020-2025):
            - 2025: Max Verstappen (Red Bull)
            - 2024: Lewis Hamilton (Mercedes) [Promoted after teammate George Russell was disqualified for underweight car].
            - 2023: Max Verstappen (Red Bull)
            - 2022: Max Verstappen (Red Bull)
            - 2021: Max Verstappen (Red Bull) [Infamous 2-lap non-race under safety car due to extreme torrential storm].
            - 2020: Lewis Hamilton (Mercedes)
            """,
            "circuit_monza": """
            CIRCUIT: Autodromo Nazionale Monza (Italian Grand Prix)
            TYPE: Ultra-Low Downforce 'Temple of Speed'
            KEY CHARACTERISTICS: Massive straight-line speeds, low aerodynamic drag trim setups, heavy curb-striking chicanes.
            WINNERS (2020-2025):
            - 2025: Lando Norris (McLaren)
            - 2024: Charles Leclerc (Ferrari) - Masterclass 1-stop strategy in front of Tifosi.
            - 2023: Max Verstappen (Red Bull) - Broke record with 10th consecutive solo win.
            - 2022: Max Verstappen (Red Bull)
            - 2021: Daniel Ricciardo (McLaren) - Historic McLaren 1-2 finish.
            - 2020: Pierre Gasly (AlphaTauri) - Shock maiden victory following Hamilton penalty.
            """,
            "circuit_suzuka": """
            CIRCUIT: Suzuka International Racing Course (Japanese Grand Prix)
            TYPE: Technical Figure-8 Layout
            KEY CHARACTERISTICS: Highly technical first-sector 'S' curves, demanding extreme driver precision and front-end mechanical grip.
            WINNERS (2022-2025) [Note: 2020-2021 cancelled]:
            - 2025: Max Verstappen (Red Bull)
            - 2024: Max Verstappen (Red Bull) - Rescheduled to a Spring race slot.
            - 2023: Max Verstappen (Red Bull)
            - 2022: Max Verstappen (Red Bull) - Sealed his 2nd World Championship in rainy shortened round.
            """,
            "circuit_interlagos": """
            CIRCUIT: Autódromo José Carlos Pace (São Paulo / Brazilian Grand Prix)
            TYPE: Anti-Clockwise High-Altitude Track
            KEY CHARACTERISTICS: Short lap time, undulating topography, heavy weather transitions, famous 'Senna S' complex.
            WINNERS (2021-2025) [Note: 2020 cancelled]:
            - 2025: Lando Norris (McLaren)
            - 2024: Max Verstappen (Red Bull) - Stellar drive from 17th on grid in severe wet weather.
            - 2023: Max Verstappen (Red Bull)
            - 2022: George Russell (Mercedes) - Maiden career F1 sprint and grand prix victory.
            - 2021: Lewis Hamilton (Mercedes) - Legendary weekend fightback from back of the grid.
            """,
            "circuit_abu_dhabi": """
            CIRCUIT: Yas Marina Circuit (Season Finale)
            TYPE: Night Twilight Track Layout
            KEY CHARACTERISTICS: Redesigned in 2021 to improve overtaking flowing sectors, heavy braking at end of back straights.
            WINNERS (2020-2025):
            - 2025: Max Verstappen (Red Bull)
            - 2024: Max Verstappen (Red Bull)
            - 2023: Max Verstappen (Red Bull)
            - 2022: Max Verstappen (Red Bull)
            - 2021: Max Verstappen (Red Bull) - Highly controversial title deciding final lap pass.
            - 2020: Max Verstappen (Red Bull)
            """
        }

        for record_id, content in f1_historical_dump.items():
            self.collection.upsert(
                documents=[content.strip()],
                ids=[record_id],
                metadatas=[{"source": "historical_database", "season_span": "2020-2025"}]
            )
        print(f"📊 {len(f1_historical_dump)} multi-year season and circuit files successfully synced to ChromaDB.")

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