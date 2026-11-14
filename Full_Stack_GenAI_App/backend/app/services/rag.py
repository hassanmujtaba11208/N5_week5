"""Local RAG-style retrieval service using TF-IDF cosine similarity."""
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class RAGService:
    def __init__(self, corpus_path: Path):
        self.corpus_path = Path(corpus_path)
        self.sections = self._load_sections()
        if not self.sections:
            raise ValueError(f"No content found in knowledge base: {self.corpus_path}")
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform([body for _, body in self.sections])

    def _load_sections(self):
        text = self.corpus_path.read_text(encoding="utf-8")
        title, lines, output = "General", [], []
        for line in text.splitlines():
            if line.startswith("## "):
                if lines:
                    output.append((title, " ".join(lines).strip()))
                    lines = []
                title = line[3:].strip()
            elif line.startswith("# "):
                continue
            elif line.strip():
                lines.append(line.strip())
        if lines:
            output.append((title, " ".join(lines).strip()))
        return [(title, body) for title, body in output if body]

    def search(self, query: str, top_k: int = 3):
        if not query.strip():
            raise ValueError("Search query cannot be empty.")
        if not 1 <= top_k <= 10:
            raise ValueError("top_k must be between 1 and 10.")
        vector = self.vectorizer.transform([query])
        scores = cosine_similarity(vector, self.matrix).ravel()
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
        results = []
        for index, score in ranked[:top_k]:
            if score <= 0:
                continue
            title, body = self.sections[index]
            results.append({
                "rank": len(results) + 1,
                "section": title,
                "text": body,
                "similarity": round(float(score), 4),
            })
        return results
