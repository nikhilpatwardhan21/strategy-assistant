from src.chunking.chunker import DocumentChunker
from src.vectordb.vector_store import F1VectorStoreManager

# 1. Simulate a page from the FIA Sporting Regulations handbook
sample_fia_document = """
ARTICLE 40.1: The pit lane speed limit shall be 80km/h during the entire event. 
However, this may be amended by the Race Director due to safety constraints. 
ARTICLE 40.2: Under Safety Car conditions, teams are permitted to make tire changes. 
However, double-stacking cars in the pitlane is heavily restricted if it blocks 
the path of oncoming vehicles in the fast lane.
"""

print("--- Starting Vector Pipeline Test ---")

# 2. Break it into chunks
chunker = DocumentChunker(chunk_size=150, chunk_overlap=30)
text_chunks = chunker.chunk_text(sample_fia_document)

# 3. Initialize DB and add data
vdb_manager = F1VectorStoreManager()
vdb_manager.add_documents(text_chunks, source_name="fia_sporting_regs_2026")

# 4. Try querying it like your strategist engine would
query = "What happens if we pit or change tires while the safety car is active?"
retrieved_context = vdb_manager.query_similar_context(query, n_results=1)

print("\n--- Similarity Search Results ---")
print(retrieved_context)