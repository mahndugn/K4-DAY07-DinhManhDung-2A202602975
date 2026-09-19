"""
Benchmark tool for Lab 07 - Data Foundations.
Evaluates retrieval quality across chunking strategies on the UTSC Library dataset.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import _mock_embed
from src.models import Document
from src.store import EmbeddingStore


class HeadingChunker:
    """
    Heading-based chunker for structured policy / regulation markdown documents.
    Splits by Markdown headings (#, ##, ###), keeping the heading hierarchy in each chunk.
    """

    def __init__(self, max_chunk_size: int = 500) -> None:
        self.max_chunk_size = max_chunk_size
        self._fallback_chunker = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Split on markdown headings
        sections = re.split(r"(?=(?:^|\n)#{1,3}\s+)", text.strip())
        chunks: list[str] = []
        for section in sections:
            section = section.strip()
            if not section:
                continue
            if len(section) <= self.max_chunk_size:
                chunks.append(section)
            else:
                first_line = section.split("\n", 1)[0]
                sub_chunks = self._fallback_chunker.chunk(section)
                for sc in sub_chunks:
                    if sc.startswith("#"):
                        chunks.append(sc)
                    else:
                        chunks.append(f"{first_line}\n\n{sc}")
        return chunks


BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "What are the UTSC Library’s regular opening hours from Monday to Friday between September 8 and December 22, 2026?",
        "gold_answer": "The library’s regular weekday hours are 8:00 AM to 10:00 PM. It is closed on October 12, 2026.",
        "target_doc": "utsc-library-hours",
        "evidence_keywords": ["8:00 AM to 10:00 PM", "8:00 AM - 10:00 PM", "October 12", "Friday"],
        "filter": None,
        "notes": "Tra cứu thời gian và nhận biết ngoại lệ.",
    },
    {
        "id": 2,
        "query": "As an undergraduate student, how long can I borrow regular library items, and what is my item limit?",
        "gold_answer": "Undergraduate students have a regular loan period of 14 days and an item limit of 50.",
        "target_doc": "utsc-borrowing-policy",
        "evidence_keywords": ["Undergraduate students", "14 days", "50"],
        "filter": None,
        "notes": "Phân biệt quy định dành cho sinh viên đại học với các nhóm khác.",
    },
    {
        "id": 3,
        "query": "Where should a user return a borrowed laptop from the Technology Loans collection?",
        "gold_answer": "A borrowed laptop should be returned directly to the Info Desk.",
        "target_doc": "utsc-technology-loans",
        "evidence_keywords": ["Info Desk", "return"],
        "filter": None,
        "notes": "Tra cứu địa điểm và quy trình trả thiết bị.",
    },
    {
        "id": 4,
        "query": "A student needs to find a physical course reading placed on reserve. Where is it located?",
        "gold_answer": "Physical course reserves are located 20 steps to the left of the InfoDesk at the UTSC Library.",
        "target_doc": "utsc-course-reserves",
        "evidence_keywords": ["20 steps to the left of the InfoDesk", "InfoDesk"],
        "filter": {"audience": "student"},
        "ab_test": True,
        "notes": "A/B test: không lọc so với metadata_filter={'audience': 'student'}.",
    },
    {
        "id": 5,
        "query": "Which service provides a free and secure University of Toronto repository for disseminating and preserving faculty and graduate-student research?",
        "gold_answer": "TSpace – University of Toronto Research Repository.",
        "target_doc": "utsc-research-publishing",
        "evidence_keywords": ["TSpace", "Research Repository"],
        "filter": None,
        "notes": "Định danh dịch vụ theo chức năng.",
    },
]


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Extract YAML frontmatter and body from markdown file."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    fm_raw = parts[1].strip()
    body = parts[2].strip()

    metadata: dict[str, str] = {}
    for line in fm_raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            metadata[key] = val

    return metadata, body


def load_corpus(data_dir: Path, chunker) -> list[Document]:
    """Load, clean and chunk all .md files in the corpus directory."""
    documents: list[Document] = []
    md_files = sorted(data_dir.glob("*.md"))

    for p in md_files:
        content = p.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(content)
        doc_id = metadata.get("doc_id", p.stem)
        metadata["doc_id"] = doc_id

        chunks = chunker.chunk(body)
        for i, chunk_text in enumerate(chunks):
            chunk_doc = Document(
                id=f"{doc_id}#{i}",
                content=chunk_text,
                metadata=dict(metadata),
            )
            documents.append(chunk_doc)

    return documents


def get_chunker(strategy: str, chunk_size: int = 400):
    if strategy == "fixed_size":
        return FixedSizeChunker(chunk_size=chunk_size, overlap=50)
    elif strategy == "by_sentences":
        return SentenceChunker(max_sentences_per_chunk=3)
    elif strategy == "heading":
        return HeadingChunker(max_chunk_size=chunk_size)
    else:  # default: recursive
        return RecursiveChunker(chunk_size=chunk_size)


def run_benchmark(
    data_dir: str = "data/utsc-library-services",
    strategy: str = "recursive",
    chunk_size: int = 400,
    output_file: str | None = "ket_qua_benchmark.txt",
) -> None:
    path = Path(data_dir)
    if not path.exists():
        print(f"Error: Directory '{data_dir}' not found.")
        sys.exit(1)

    chunker = get_chunker(strategy, chunk_size=chunk_size)
    docs = load_corpus(path, chunker)

    store = EmbeddingStore(collection_name="benchmark_store", embedding_fn=_mock_embed)
    store.add_documents(docs)

    def simple_mock_llm(prompt: str) -> str:
        return "[LLM Summary] Answer generated from retrieved context."

    agent = KnowledgeBaseAgent(store=store, llm_fn=simple_mock_llm)

    output_lines: list[str] = []

    def out(text: str = "") -> None:
        print(text)
        output_lines.append(text)

    out("================================================================================")
    out("                  BENCHMARK RETRIEVAL QUALITY REPORT — K4-L3A                  ")
    out("================================================================================")
    out(f"Corpus directory : {data_dir}")
    out(f"Strategy         : {strategy}")
    out(f"Chunk size       : {chunk_size}")
    out(f"Total chunks     : {len(docs)}")
    out(f"Store size       : {store.get_collection_size()} records")
    out("================================================================================\n")

    total_score = 0
    num_queries = len(BENCHMARK_QUERIES)

    for item in BENCHMARK_QUERIES:
        qid = item["id"]
        qtext = item["query"]
        gold = item["gold_answer"]
        target = item["target_doc"]
        meta_filter = item.get("filter")
        keywords = item.get("evidence_keywords", [])

        out(f"--------------------------------------------------------------------------------")
        out(f"QUERY {qid}: {qtext}")
        out(f"Gold Answer : {gold}")
        out(f"Target Doc  : {target}")
        out(f"Filter      : {meta_filter}")
        out(f"--------------------------------------------------------------------------------")

        results = store.search_with_filter(qtext, top_k=3, metadata_filter=meta_filter)

        found_target = False
        target_rank = -1
        evidence_found = False

        for rank, r in enumerate(results, 1):
            r_doc_id = r["metadata"].get("doc_id", "")
            r_score = r["score"]
            r_content = r["content"].replace("\n", " ")
            preview = r_content[:140] + "..." if len(r_content) > 140 else r_content

            is_target = (r_doc_id == target)
            has_kw = any(kw.lower() in r_content.lower() for kw in keywords)

            if is_target and not found_target:
                found_target = True
                target_rank = rank
            if has_kw:
                evidence_found = True

            mark = "[TARGET]" if is_target else "        "
            out(f"  Top-{rank} (score={r_score:+.4f}) {mark} id={r['id']}")
            out(f"         source={r_doc_id} | preview: {preview}")

        # Scoring logic according to docs/SCORING.md:
        # 2 points: Top-3 contains relevant chunk + agent answer accurate
        # 1 point : Top-3 has relevant chunk but not top-1 or missing details
        # 0 points: Relevant chunk absent from top-3
        q_score = 0
        if found_target and evidence_found:
            q_score = 2 if target_rank == 1 else 1
        elif found_target:
            q_score = 1
        else:
            q_score = 0

        total_score += q_score
        out(f"  -> Evaluation : Score={q_score}/2 (Target in top-3: {found_target}, Rank: {target_rank}, Evidence: {evidence_found})")

        # Agent answer
        agent_ans = agent.answer(qtext, top_k=3)
        out(f"  -> Agent Output: {agent_ans}")
        out()

        # A/B test for queries marked with ab_test
        if item.get("ab_test"):
            out("  --- [A/B Test Comparison] ---")
            out("  Running WITHOUT filter:")
            results_no_filter = store.search_with_filter(qtext, top_k=3, metadata_filter=None)
            for rk, r in enumerate(results_no_filter, 1):
                out(f"    No-Filter Top-{rk}: id={r['id']} (score={r['score']:+.4f}, doc={r['metadata'].get('doc_id')})")
            out("  -----------------------------\n")

    out("================================================================================")
    out(f"FINAL RESULT: Total Retrieval Score = {total_score} / {num_queries * 2} points")
    out("================================================================================")

    if output_file:
        Path(output_file).write_text("\n".join(output_lines), encoding="utf-8")
        print(f"\n[Saved benchmark output to {output_file}]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAG benchmark on UTSC Library dataset.")
    parser.add_argument("--data-dir", default="data/utsc-library-services", help="Path to corpus directory")
    parser.add_argument("--strategy", default="recursive", choices=["recursive", "fixed_size", "by_sentences", "heading"], help="Chunking strategy")
    parser.add_argument("--chunk-size", type=int, default=400, help="Chunk size for chunkers")
    parser.add_argument("--output", default="ket_qua_benchmark.txt", help="File to write results")
    args = parser.parse_args()

    run_benchmark(
        data_dir=args.data_dir,
        strategy=args.strategy,
        chunk_size=args.chunk_size,
        output_file=args.output,
    )


if __name__ == "__main__":
    main()
