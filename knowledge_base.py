import os
from pathlib import Path
from typing import List, Optional, Dict
import hashlib

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document


class KnowledgeBase:
    
    def __init__(self, 
                 guides_folder: str = "guides",
                 db_folder: str = "chroma_db",
                 embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.guides_folder = Path(guides_folder)
        self.db_folder = Path(db_folder)
        
        self.guides_folder.mkdir(exist_ok=True)
        self.db_folder.mkdir(exist_ok=True)
        
        print("Loading embedding model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("Embedding model loaded!")
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        self.vectorstore: Optional[Chroma] = None
        self._load_or_create_db()
    
    def _get_guides_hash(self) -> str:
        hash_content = ""
        if self.guides_folder.exists():
            for file in sorted(self.guides_folder.glob("*.txt")):
                stat = file.stat()
                hash_content += f"{file.name}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.md5(hash_content.encode()).hexdigest()
    
    def _load_or_create_db(self):
        hash_file = self.db_folder / "guides_hash.txt"
        current_hash = self._get_guides_hash()
        
        needs_reindex = True
        if hash_file.exists():
            stored_hash = hash_file.read_text().strip()
            if stored_hash == current_hash and (self.db_folder / "chroma.sqlite3").exists():
                needs_reindex = False
        
        if needs_reindex:
            print("Indexing guides...")
            self._index_guides()
            hash_file.write_text(current_hash)
        else:
            print("Loading existing knowledge base...")
            self.vectorstore = Chroma(
                persist_directory=str(self.db_folder),
                embedding_function=self.embeddings
            )
            print(f"Loaded {self.vectorstore._collection.count()} chunks")
    
    def _index_guides(self):
        documents = []
        txt_files = list(self.guides_folder.glob("*.txt"))
        
        if not txt_files:
            print(f"No .txt files found in '{self.guides_folder}'")
            documents = [Document(
                page_content="No guides loaded yet. Add .txt files to the guides/ folder.",
                metadata={"source": "placeholder"}
            )]
        else:
            for txt_file in txt_files:
                print(f"  Processing: {txt_file.name}")
                try:
                    loader = TextLoader(str(txt_file), encoding='utf-8')
                    docs = loader.load()
                    
                    game_name = txt_file.stem
                    for doc in docs:
                        doc.metadata["game"] = game_name
                        doc.metadata["source"] = str(txt_file)
                    
                    documents.extend(docs)
                except Exception as e:
                    print(f"  Error loading {txt_file.name}: {e}")
        
        chunks = self.text_splitter.split_documents(documents)
        print(f"  Total chunks created: {len(chunks)}")
        
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(self.db_folder)
        )
        
        print(f"Knowledge base indexed with {len(chunks)} chunks")
    
    def reindex(self):
        print("Forcing reindex...")
        hash_file = self.db_folder / "guides_hash.txt"
        if hash_file.exists():
            hash_file.unlink()
        self._load_or_create_db()
    
    def search(self, query: str, k: int = 3, 
               game_filter: Optional[str] = None) -> List[Dict]:
        if not self.vectorstore:
            return []
        
        filter_dict = None
        if game_filter:
            filter_dict = {"game": game_filter}
        
        results = self.vectorstore.similarity_search_with_relevance_scores(
            query, k=k, filter=filter_dict
        )
        
        formatted = []
        for doc, score in results:
            formatted.append({
                "content": doc.page_content,
                "game": doc.metadata.get("game", "unknown"),
                "source": doc.metadata.get("source", "unknown"),
                "relevance": score
            })
        
        return formatted
    
    def search_context(self, screen_text: str, k: int = 3) -> str:
        results = self.search(screen_text, k=k)
        
        if not results:
            return ""
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Section {i} - {result['game']}]\n{result['content']}")
        
        return "\n\n".join(context_parts)
    
    def list_games(self) -> List[str]:
        if not self.vectorstore:
            return []
        
        collection = self.vectorstore._collection
        results = collection.get(include=["metadatas"])
        
        games = set()
        for metadata in results.get("metadatas", []):
            if metadata and "game" in metadata:
                games.add(metadata["game"])
        
        return sorted(list(games))
    
    def get_stats(self) -> Dict:
        if not self.vectorstore:
            return {"status": "not_initialized"}
        
        collection = self.vectorstore._collection
        count = collection.count()
        games = self.list_games()
        
        return {
            "total_chunks": count,
            "total_games": len(games),
            "games": games,
            "db_path": str(self.db_folder)
        }


def create_sample_guide():
    guides_folder = Path("guides")
    guides_folder.mkdir(exist_ok=True)
    
    sample_guide = """
=== RESIDENT EVIL 2 - COMPLETE WALKTHROUGH ===

== SCENARIO A - LEON ==

--- POLICE STATION - ENTRANCE ---
When entering the police station, pick up the AMMO on the reception counter.
Go to the door on the left side to find the STATION MAP.

--- POLICE STATION - EAST CORRIDOR ---
Watch out for zombies in this area! There are 3 zombies in the corridor.
Pick up the HEART KEY on the office desk.
Use the Heart Key on the door to the right.

--- POLICE STATION - CHIEF'S OFFICE ---
Examine the chief's desk to find the CHIEF'S LETTER.
The safe in this room requires the combination: LEFT 2, RIGHT 11, LEFT 14.
Inside the safe is the MEDALLION PIECE.

--- POLICE STATION - ARCHIVE ROOM ---
Examine the files to discover the laboratory location.
Pick up the WOODPECKER KEY in the locked drawer (use the crowbar).

--- LABORATORY - ENTRANCE ---
Use the SPECIAL KEY to open the main door.
Watch out for Lickers! Walk slowly to avoid attracting attention.

--- LABORATORY - GENERATOR ROOM ---
To restore power:
1. First activate the blue panel
2. Then activate the red panel  
3. Finally the green panel
Power will be restored and you can proceed.

--- FINAL BOSS - G1 ---
Shoot the exposed area (the eye on the shoulder).
Use grenades when he's stunned.
Approximately 15-20 magnum shots will defeat G1.

=== END OF SCENARIO A ===
"""
    
    sample_file = guides_folder / "resident_evil_2.txt"
    sample_file.write_text(sample_guide, encoding='utf-8')
    print(f"Sample guide created: {sample_file}")
    return sample_file


def main():
    print("=" * 50)
    print("Xayk Noob's Journal - Knowledge Base Test")
    print("=" * 50)
    
    guides_folder = Path("guides")
    if not guides_folder.exists() or not list(guides_folder.glob("*.txt")):
        print("\nCreating sample guide for testing...")
        create_sample_guide()
    
    print("\nInitializing knowledge base...")
    kb = KnowledgeBase()
    
    stats = kb.get_stats()
    print(f"\nStatistics:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Indexed games: {stats['games']}")
    
    test_queries = [
        "Generator Room restore power",
        "Heart Key",
        "safe combination",
        "defeat boss G1"
    ]
    
    print("\nTesting searches:")
    print("-" * 40)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = kb.search(query, k=2)
        
        for i, result in enumerate(results, 1):
            content_preview = result['content'][:150].replace('\n', ' ')
            print(f"   [{i}] (relevance: {result['relevance']:.2f})")
            print(f"       {content_preview}...")
    
    print("\n" + "=" * 50)
    print("Test completed!")


if __name__ == "__main__":
    main()
