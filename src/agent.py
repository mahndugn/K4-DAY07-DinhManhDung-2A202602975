from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở tri thức."

        context_blocks = []
        for i, r in enumerate(results, 1):
            source = r.get("metadata", {}).get("doc_id") or r.get("id", "tài liệu")
            context_blocks.append(f"[{i}] (Nguồn: {source})\n{r['content']}")
        context = "\n\n".join(context_blocks)

        prompt = (
            f"Dưới đây là các đoạn văn bản liên quan được trích xuất từ cơ sở tri thức:\n\n"
            f"{context}\n\n"
            f"Dựa vào thông tin trên, hãy trả lời câu hỏi sau một cách chính xác và trích dẫn nguồn [1], [2] nếu có. "
            f"Nếu ngữ cảnh không chứa thông tin để trả lời, hãy nói rõ là không tìm thấy.\n"
            f"Câu hỏi: {question}\nTrả lời:"
        )
        return self.llm_fn(prompt)
