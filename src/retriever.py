"""[과제 규약 3-1] RAG 파이프라인 — 진입 파일.

실제 코드는 src/knowledge/retriever.py 에 있다(배치 규칙은 CLAUDE.md).
공식 문서 9개를 제목 단위로 자른 청크를 Chroma 벡터(Bedrock Titan v2) + BM25(kiwipiepy) 로 찾고 RRF 로 합친다.
"""
from src.knowledge.retriever import HybridRetriever, get_retriever, load_chunks, warm_up  # noqa: F401
