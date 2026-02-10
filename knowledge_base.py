import os
import re
import math
from pathlib import Path
from typing import List, Optional, Dict
import hashlib
import json


class KnowledgeBase:
    """
    Knowledge base for game guides.
    Uses TF-IDF text search (no PyTorch/ONNX/DLL dependencies).
    Works perfectly in .exe without any heavy ML libraries.
    
    Supports two folder structures:
    1. Flat: guides/*.txt
    2. By game: guides/GameName/*.txt
    """
    
    def __init__(self, 
                 guides_folder: str = "guides",
                 db_folder: str = "chroma_db"):
        self.guides_folder = Path(guides_folder)
        self.db_folder = Path(db_folder)
        
        self.guides_folder.mkdir(exist_ok=True)
        self.db_folder.mkdir(exist_ok=True)
        
        self.chunks: List[Dict] = []
        self.idf: Dict[str, float] = {}
        
        print("Loading embedding model...")
        self._load_or_create_db()
        print("Embedding model loaded!")
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase, split on non-alphanumeric"""
        return re.findall(r'[a-z0-9]+', text.lower())
    
    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Compute term frequency"""
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        total = len(tokens) if tokens else 1
        return {t: c / total for t, c in tf.items()}
    
    def _compute_idf(self):
        """Compute inverse document frequency across all chunks"""
        n_docs = len(self.chunks)
        if n_docs == 0:
            return
        
        doc_freq = {}
        for chunk in self.chunks:
            tokens = set(self._tokenize(chunk["content"]))
            for token in tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1
        
        self.idf = {}
        for token, freq in doc_freq.items():
            self.idf[token] = math.log(n_docs / (1 + freq))
    
    def _tfidf_score(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        """Compute TF-IDF similarity between query and document"""
        if not query_tokens or not doc_tokens:
            return 0.0
        
        doc_tf = self._compute_tf(doc_tokens)
        query_tf = self._compute_tf(query_tokens)
        
        score = 0.0
        for token in query_tokens:
            if token in doc_tf:
                idf = self.idf.get(token, 1.0)
                score += query_tf[token] * doc_tf[token] * idf * idf
        
        return score
    
    def _get_guides_hash(self) -> str:
        """Generate hash of all guide files for change detection"""
        hash_content = ""
        if self.guides_folder.exists():
            for file in sorted(self.guides_folder.glob("*.txt")):
                stat = file.stat()
                hash_content += f"{file.name}:{stat.st_size}:{stat.st_mtime}"
            
            for game_folder in sorted(self.guides_folder.iterdir()):
                if game_folder.is_dir():
                    for file in sorted(game_folder.glob("*.txt")):
                        stat = file.stat()
                        hash_content += f"{game_folder.name}/{file.name}:{stat.st_size}:{stat.st_mtime}"
        
        return hashlib.md5(hash_content.encode()).hexdigest()
    
    def _discover_guides(self) -> List[Dict]:
        """Discover all guide files in the guides folder."""
        guides = []
        
        for txt_file in self.guides_folder.glob("*.txt"):
            game_name = txt_file.stem.replace("_", " ")
            guides.append({"path": txt_file, "game_name": game_name})
        
        for game_folder in self.guides_folder.iterdir():
            if game_folder.is_dir() and not game_folder.name.startswith("."):
                game_name = game_folder.name.replace("_", " ")
                for txt_file in game_folder.glob("*.txt"):
                    guides.append({"path": txt_file, "game_name": game_name})
        
        return guides
    
    def _split_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        # Split by paragraphs first
        paragraphs = text.split("\n\n")
        
        current_chunk = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Keep overlap from end of previous chunk
                words = current_chunk.split()
                overlap_words = words[-min(10, len(words)):]
                current_chunk = " ".join(overlap_words) + "\n\n" + para
            else:
                current_chunk += ("\n\n" if current_chunk else "") + para
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # If no paragraph splits, split by lines
        if not chunks and text.strip():
            lines = text.strip().split("\n")
            current_chunk = ""
            for line in lines:
                if len(current_chunk) + len(line) > chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = line
                else:
                    current_chunk += ("\n" if current_chunk else "") + line
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text.strip()] if text.strip() else []
    
    def _load_or_create_db(self):
        hash_file = self.db_folder / "guides_hash.txt"
        index_file = self.db_folder / "chunks_index.json"
        current_hash = self._get_guides_hash()
        
        needs_reindex = True
        if hash_file.exists() and index_file.exists():
            stored_hash = hash_file.read_text().strip()
            if stored_hash == current_hash:
                needs_reindex = False
        
        if needs_reindex:
            print("Indexing guides...")
            self._index_guides()
            hash_file.write_text(current_hash)
            # Save index to disk
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=1)
        else:
            print("Loading existing knowledge base...")
            with open(index_file, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
            self._compute_idf()
            print(f"Loaded {len(self.chunks)} chunks")
    
    def _index_guides(self):
        """Index all guide files"""
        guides = self._discover_guides()
        self.chunks = []
        
        if not guides:
            print(f"No .txt files found in '{self.guides_folder}'")
            return
        
        games_found = set()
        
        for guide_info in guides:
            txt_file = guide_info["path"]
            game_name = guide_info["game_name"]
            games_found.add(game_name)
            
            print(f"  Processing: {txt_file.name} ({game_name})")
            try:
                content = txt_file.read_text(encoding='utf-8')
                text_chunks = self._split_text(content)
                
                for chunk_text in text_chunks:
                    self.chunks.append({
                        "content": chunk_text,
                        "game": game_name,
                        "source": str(txt_file),
                        "file_name": txt_file.name
                    })
            except Exception as e:
                print(f"  Error loading {txt_file.name}: {e}")
        
        print(f"  Games found: {', '.join(sorted(games_found))}")
        print(f"  Total chunks created: {len(self.chunks)}")
        
        self._compute_idf()
        print(f"Knowledge base indexed with {len(self.chunks)} chunks")
    
    def reindex(self):
        """Force reindex of all guides"""
        print("Forcing reindex...")
        hash_file = self.db_folder / "guides_hash.txt"
        if hash_file.exists():
            hash_file.unlink()
        index_file = self.db_folder / "chunks_index.json"
        if index_file.exists():
            index_file.unlink()
        self._load_or_create_db()
    
    def search(self, query: str, k: int = 3, 
               game_filter: Optional[str] = None) -> List[Dict]:
        """Search for relevant content in the knowledge base."""
        if not self.chunks or not query.strip():
            return []
        
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        scored = []
        for chunk in self.chunks:
            if game_filter and chunk.get("game") != game_filter:
                continue
            
            doc_tokens = self._tokenize(chunk["content"])
            score = self._tfidf_score(query_tokens, doc_tokens)
            
            if score > 0:
                scored.append({
                    "content": chunk["content"],
                    "game": chunk.get("game", "unknown"),
                    "source": chunk.get("source", "unknown"),
                    "relevance": score
                })
        
        # Sort by relevance descending
        scored.sort(key=lambda x: x["relevance"], reverse=True)
        
        # Normalize scores
        if scored:
            max_score = scored[0]["relevance"]
            if max_score > 0:
                for item in scored:
                    item["relevance"] = item["relevance"] / max_score
        
        return scored[:k]
    
    def search_context(self, screen_text: str, k: int = 3, 
                       game_filter: Optional[str] = None) -> str:
        """Search and return formatted context string"""
        results = self.search(screen_text, k=k, game_filter=game_filter)
        
        if not results:
            return ""
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Section {i} - {result['game']}]\n{result['content']}")
        
        return "\n\n".join(context_parts)
    
    def list_games(self) -> List[str]:
        """List all indexed games"""
        games = set()
        for chunk in self.chunks:
            if chunk.get("game"):
                games.add(chunk["game"])
        return sorted(list(games))
    
    def get_stats(self) -> Dict:
        """Get statistics about the knowledge base"""
        games = self.list_games()
        return {
            "total_chunks": len(self.chunks),
            "total_games": len(games),
            "games": games,
            "db_path": str(self.db_folder)
        }


def main():
    print("=" * 50)
    print("Xayk Noob's Journal - Knowledge Base Test")
    print("=" * 50)
    
    print("\nInitializing knowledge base...")
    kb = KnowledgeBase()
    
    stats = kb.get_stats()
    print(f"\nStatistics:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Indexed games: {stats['games']}")
    
    test_queries = [
        "codec",
        "Snake",
        "objectives"
    ]
    
    print("\nTesting searches:")
    print("-" * 40)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = kb.search(query, k=2)
        
        for i, result in enumerate(results, 1):
            content_preview = result['content'][:100].replace('\n', ' ')
            print(f"   [{i}] Game: {result['game']} (relevance: {result['relevance']:.2f})")
            print(f"       {content_preview}...")
    
    print("\n" + "=" * 50)
    print("Test completed!")


if __name__ == "__main__":
    main()
