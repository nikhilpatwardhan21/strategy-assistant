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
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'was', 'be', 'are'}
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if w not in stop_words and len(w) > 2]

    def _bm25_score(self, document: str, query_keywords: List[str]) -> float:
        """Calculate simple BM25-style score for keyword matching."""
        doc_keywords = self._extract_keywords(document)
        score = 0
        for keyword in query_keywords:
            if keyword in doc_keywords:
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
        """Searches ChromaDB using hybrid search (semantic + keyword matching)."""
        results = self.collection.query(
            query_texts=[user_query],
            n_results=min(n_results * 2, 20),
            include=["documents", "metadatas", "distances"]
        )

        ranked_results = self._rerank_results(results, user_query, top_k=n_results)
        
        if not ranked_results:
            return "❌ No relevant context found in database.", []
        
        ranked_results.sort(key=lambda x: (0 if x[1].get("source_url") else 1, -x[2]))
        
        combined_context = "\n\n--- Context Block ---\n".join([doc for doc, _, _ in ranked_results])
        metadata_list = [meta for _, meta, _ in ranked_results]
        
        return combined_context, metadata_list

    def add_historical_stats(self):
        """Seeds expansive historical F1 statistics, records, eras, and global circuit logs (1950 - Present)."""
        f1_historical_dump = {
            # === ALL-TIME RECORDS (1950 - PRESENT) ===
            "all_time_driver_championships": """
            ALL-TIME DRIVER WORLD CHAMPIONSHIPS (1950-Present)
            1. Michael Schumacher (7 Titles: 1994, 1995, 2000, 2001, 2002, 2003, 2004)
            2. Lewis Hamilton (7 Titles: 2008, 2014, 2015, 2017, 2018, 2019, 2020)
            3. Juan Manuel Fangio (5 Titles: 1951, 1954, 1955, 1956, 1957)
            4. Max Verstappen (5 Titles: 2021, 2022, 2023, 2024)
            5. Alain Prost (4 Titles: 1985, 1986, 1989, 1993)
            6. Sebastian Vettel (4 Titles: 2010, 2011, 2012, 2013)
            7. Jack Brabham, Jackie Stewart, Niki Lauda, Nelson Piquet, Ayrton Senna (3 Titles each)
            """,
            "all_time_driver_wins": """
            ALL-TIME DRIVER GRAND PRIX WINS (1950-Present)
            1. Lewis Hamilton: 105+ wins
            2. Michael Schumacher: 91 wins
            3. Max Verstappen: 60+ wins
            4. Sebastian Vettel: 53 wins
            5. Alain Prost: 51 wins
            6. Ayrton Senna: 41 wins
            7. Fernando Alonso: 32 wins
            8. Nigel Mansell: 31 wins
            9. Jackie Stewart: 27 wins
            10. Jim Clark / Niki Lauda: 25 wins
            """,
            "all_time_constructor_championships": """
            ALL-TIME CONSTRUCTOR WORLD CHAMPIONSHIPS (1958-Present)
            Note: The Constructors' Championship was introduced in 1958, eight years after the drivers' title.
            1. Scuderia Ferrari: 16 Titles (First: 1961, Last: 2008)
            2. Williams Racing: 9 Titles (First: 1980, Last: 1997)
            3. McLaren Racing: 9 Titles (First: 1974, Last: 2024)
            4. Mercedes-AMG: 8 Titles (Consecutive from 2014 to 2021)
            5. Lotus: 7 Titles (First: 1963, Last: 1978)
            6. Red Bull Racing: 6 Titles (First: 2010, Last: 2023)
            """,

            # === HISTORICAL ERAS & DECADES ===
            "era_1950s": """
            DECADE SUMMARY: The 1950s (The Dawn of F1)
            The Formula One World Championship officially began in 1950 at Silverstone. 
            KEY DRIVERS: Juan Manuel Fangio dominated the era, winning 5 titles with 4 different manufacturers (Alfa Romeo, Maserati, Mercedes, Ferrari). Alberto Ascari won back-to-back titles in 1952-1953. Stirling Moss became known as the greatest driver never to win a championship.
            CAR TECHNOLOGY: Front-engined, incredibly dangerous, drum brakes, and no seatbelts. Alfa Romeo and Maserati were the early dominant forces before Mercedes introduced the legendary W196.
            """,
            "era_1960s": """
            DECADE SUMMARY: The 1960s (The British Invasion & Rear-Engine Revolution)
            KEY DRIVERS: Jim Clark, Graham Hill, Jack Brabham, John Surtees, Jackie Stewart.
            KEY TEAMS: Lotus, BRM, Cooper, Brabham.
            CAR TECHNOLOGY: Cooper revolutionized the sport by placing the engine behind the driver, rendering front-engine cars obsolete. Colin Chapman's Team Lotus introduced the aluminum sheet monocoque chassis (Lotus 25) and commercial sponsorship liveries. Aerodynamic wings appeared in the late 1960s. Jack Brabham became the only man to win a world title in a car of his own construction (1966).
            """,
            "era_1970s": """
            DECADE SUMMARY: The 1970s (Aero, Ground Effect, and Danger)
            KEY DRIVERS: Niki Lauda, Jackie Stewart, Emerson Fittipaldi, James Hunt, Mario Andretti.
            KEY TEAMS: Ferrari, Lotus, Tyrrell, McLaren.
            CAR TECHNOLOGY: The era was defined by the introduction of slicks, massive airboxes, and Colin Chapman's Lotus 78/79 which introduced "Ground Effect" aerodynamics, creating massive underbody downforce. Tyrrell introduced the iconic P34 six-wheeled car. The era was highly dangerous, prompting safety crusades led by Jackie Stewart and culminating in Niki Lauda's horrific survival crash at the Nürburgring in 1976.
            """,
            "era_1980s": """
            DECADE SUMMARY: The 1980s (The Turbo Era & Senna vs. Prost)
            KEY DRIVERS: Ayrton Senna, Alain Prost, Nelson Piquet, Niki Lauda, Nigel Mansell, Gilles Villeneuve.
            KEY TEAMS: McLaren, Williams, Ferrari, Brabham.
            CAR TECHNOLOGY: Ground effect was banned in 1983. Engines shifted from normally aspirated 3.0L V8s to wild 1.5L turbocharged engines pushing over 1,000 horsepower in qualifying trim. Carbon fiber monocoques (pioneered by John Barnard's McLaren MP4/1) revolutionized safety. McLaren dominated the late 80s, winning 15 of 16 races in 1988 with the MP4/4 driven by Senna and Prost.
            """,
            "era_1990s": """
            DECADE SUMMARY: The 1990s (Electronic Aids, Tragedy, and Schumacher's Rise)
            KEY DRIVERS: Michael Schumacher, Ayrton Senna, Mika Häkkinen, Damon Hill, Jacques Villeneuve, Nigel Mansell.
            KEY TEAMS: Williams, McLaren, Benetton, Ferrari.
            CAR TECHNOLOGY: The early 90s saw Williams deploy highly advanced active suspension and traction control (FW14B). After the tragic deaths of Ayrton Senna and Roland Ratzenberger at Imola in 1994, the FIA mandated sweeping safety changes, banning electronic aids and introducing grooved tires and narrower tracks in 1998. Michael Schumacher won his first two titles with Benetton before moving to rebuild Ferrari.
            """,
            "era_2000s": """
            DECADE SUMMARY: The 2000s (The Ferrari Hegemony & V10 Scremers)
            KEY DRIVERS: Michael Schumacher, Fernando Alonso, Kimi Räikkönen, Lewis Hamilton, Jenson Button.
            KEY TEAMS: Ferrari, Renault, McLaren, Brawn GP.
            CAR TECHNOLOGY: The era is remembered for the screaming 3.0L V10 engines (later regulated to 2.4L V8s). Michael Schumacher and Ferrari dominated the first half of the decade, winning 5 consecutive driver and constructor titles (2000-2004). Fernando Alonso and Renault ended the streak in 2005-2006. In 2009, massive aerodynamic regulation changes led to the "Double Diffuser" loophole, allowing Brawn GP to win the championship in their single year of existence.
            """,
            "era_2010s": """
            DECADE SUMMARY: The 2010s (Red Bull Dominance & The V6 Hybrid Era)
            KEY DRIVERS: Sebastian Vettel, Lewis Hamilton, Nico Rosberg, Fernando Alonso, Max Verstappen.
            KEY TEAMS: Red Bull Racing, Mercedes, Ferrari.
            CAR TECHNOLOGY: The decade began with Red Bull Racing and Sebastian Vettel winning four consecutive titles (2010-2013) using blown-diffuser aerodynamics. In 2014, F1 introduced 1.6L V6 Turbo-Hybrid power units. Mercedes mastered this technology, beginning an unprecedented era of dominance, securing every constructor's championship from 2014 to 2019, while Lewis Hamilton secured five titles and Nico Rosberg secured one.
            """,

            # === MODERN SEASON SUMMARIES (2020-2025) ===
            "stats_2025_season": "YEAR: 2025 Season Summary. DRIVER CHAMPION: Max Verstappen (Red Bull Racing) - 5th consecutive World Championship. CONSTRUCTOR CHAMPION: McLaren Racing (Driven by Lando Norris and Oscar Piastri). SEASON BREAKDOWN: A highly contentious fight between McLaren, Ferrari, and Red Bull. Norris mounted a fierce campaign, but Verstappen secured the title.",
            "stats_2024_season": "YEAR: 2024 Season Summary. DRIVER CHAMPION: Max Verstappen (Red Bull Racing). CONSTRUCTOR CHAMPION: McLaren Racing. SEASON BREAKDOWN: Red Bull dominated early, but McLaren closed the gap rapidly. Lando Norris achieved his maiden win in Miami. Lewis Hamilton completed his final year with Mercedes before moving to Ferrari.",
            "stats_2023_season": "YEAR: 2023 Season Summary. DRIVER CHAMPION: Max Verstappen (Red Bull Racing). CONSTRUCTOR CHAMPION: Red Bull Racing (RB19). SEASON BREAKDOWN: Arguably the most dominant solo display in F1 history. Verstappen secured 19 wins out of 22 Grands Prix. Red Bull Racing won 21 out of 22 total races.",
            "stats_2022_season": "YEAR: 2022 Season Summary. DRIVER CHAMPION: Max Verstappen (Red Bull). CONSTRUCTOR CHAMPION: Red Bull Racing. SEASON BREAKDOWN: Ground-effect aero regulations were fully introduced. Ferrari started strongly with Leclerc, but strategic errors allowed Verstappen to pull away. Mercedes struggled with porpoising.",
            "stats_2021_season": "YEAR: 2021 Season Summary. DRIVER CHAMPION: Max Verstappen (Red Bull). CONSTRUCTOR CHAMPION: Mercedes AMG Petronas. SEASON BREAKDOWN: A historic rivalry between Verstappen and Hamilton. The championship was decided on a controversial final-lap restart at Abu Dhabi.",
            "stats_2020_season": "YEAR: 2020 Season Summary. DRIVER CHAMPION: Lewis Hamilton (Mercedes) - Equaled Schumacher's record of 7 Titles. CONSTRUCTOR CHAMPION: Mercedes. SEASON BREAKDOWN: Calendar heavily disrupted by COVID-19. Hamilton broke the all-time race wins record (91).",

            # === GLOBAL CIRCUIT SPECIFIC DUMPS ===
            "circuit_silverstone": "CIRCUIT: Silverstone (British Grand Prix). TYPE: High-Speed Permanent. HISTORIC FACT: Hosted the first ever Formula 1 World Championship race on May 13, 1950. Known for Maggotts, Becketts, Chapel sequence.",
            "circuit_monza": "CIRCUIT: Autodromo Nazionale Monza (Italian Grand Prix). TYPE: Ultra-Low Downforce 'Temple of Speed'. HISTORIC FACT: Has hosted more World Championship Grands Prix than any other circuit. Known for the Parabolica and Lesmo corners.",
            "circuit_monaco": "CIRCUIT: Circuit de Monaco. TYPE: Tight Street Circuit. HISTORIC FACT: Part of the Triple Crown of Motorsport. Ayrton Senna holds the record for most wins here with 6 victories.",
            "circuit_spa": "CIRCUIT: Circuit de Spa-Francorchamps (Belgian Grand Prix). TYPE: High-Speed Ardennes Track. HISTORIC FACT: Longest track on the calendar (7.004 km). Features the iconic Eau Rouge and Raidillon elevation change.",
            "circuit_suzuka": "CIRCUIT: Suzuka International Racing Course (Japanese Grand Prix). TYPE: Technical Figure-8 Layout. HISTORIC FACT: Designed by John Hugenholtz as a Honda test track. Scene of the infamous Senna vs Prost title collisions in 1989 and 1990.",
            "circuit_interlagos": "CIRCUIT: Autódromo José Carlos Pace (Brazilian Grand Prix). TYPE: Anti-Clockwise High-Altitude Track. HISTORIC FACT: Scene of Lewis Hamilton's dramatic final-corner championship win in 2008 against Felipe Massa.",
            "circuit_bahrain": "CIRCUIT: Bahrain International Circuit. TYPE: Desert Track. KEY FACT: Often the modern season opener. High degradation surface.",
            "circuit_abu_dhabi": "CIRCUIT: Yas Marina Circuit. TYPE: Night Twilight Track. KEY FACT: Traditional season finale. Site of the 2021 title decider."
        }

        for record_id, content in f1_historical_dump.items():
            self.collection.upsert(
                documents=[content.strip()],
                ids=[record_id],
                metadatas=[{"source": "historical_database", "span": "1950-Present"}]
            )
        print(f"📊 {len(f1_historical_dump)} expansive historical F1 records (1950-Present) successfully synced to ChromaDB.")

    def ingest_live_web_data(self, url: str, source_id: str):
        """Dynamically drives the scraper, extracts text, and inserts into vector rows."""
        from src.chunking.chunker import DocumentChunker
        
        scraper = F1LiveWebScraper()
        raw_web_text = scraper.fetch_and_extract_text(url)
        
        if not raw_web_text:
            print("⚠️ Web ingestion aborted. No text data retrieved.")
            return False
            
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
        web_chunks = chunker.chunk_text(raw_web_text)
        
        ids = [f"web_{source_id}_chunk_{i}" for i in range(len(web_chunks))]
        metadatas = [{"source_url": url, "chunk_idx": i} for i, _ in enumerate(web_chunks)]
        
        self.collection.upsert(
            documents=web_chunks,
            ids=ids,
            metadatas=metadatas
        )
        print(f"💾 [DATABASE] Vectorized and stored {len(web_chunks)} live web chunks into ChromaDB.")
        return True

