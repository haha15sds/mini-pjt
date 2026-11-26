"""RAG 검색기: 공식 문서 하이브리드 검색 (패턴 3).

- 문서: data/docs/*.md (Gemini Enterprise 공식 문서, CC BY 4.0)
- 청크: 마크다운 제목(##, ###) 단위로 자른 뒤 1,200자 안팎으로 나눈다.
  청크 ID는 "{doc_id}#{번호}" 이고, 이 값이 /query 응답 contexts[].doc_id 가 된다.
- 검색: Chroma 벡터(Bedrock Titan v2 임베딩) + BM25(kiwipiepy 형태소) 결과를
  RRF(Reciprocal Rank Fusion)로 합친다. 한국어 질문과 영어 검색어를 둘 다 넣는다(D-5).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from kiwipiepy import Kiwi
from rank_bm25 import BM25Okapi

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "data" / "docs"
CHROMA_DIR = ROOT / "chroma_db"
COLLECTION = "ge_docs_v1"
EMBED_MODEL = "amazon.titan-embed-text-v2:0"
REGION = "us-east-1"
CHUNK_MAX = 1200


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    url: str
    section: str
    text: str


def _parse_doc(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    if raw.startswith("---"):
        head, body = raw[3:].split("\n---", 1)
        for line in head.strip().splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
        return meta, body.strip()
    return meta, raw


def load_chunks() -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        meta, body = _parse_doc(path)
        doc_id = meta.get("doc_id", path.stem)
        # 제목 단위로 자르기
        sections = re.split(r"\n(?=#{2,3} )", "\n" + body)
        n = 0
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue
            heading = sec.splitlines()[0].lstrip("# ").strip() if sec.startswith("#") else meta.get("title", "")
            # 긴 섹션은 문단 경계로 나눈다
            buf = ""
            for para in sec.split("\n\n"):
                if len(buf) + len(para) > CHUNK_MAX and buf:
                    n += 1
                    chunks.append(Chunk(f"{doc_id}#{n:02d}", doc_id, meta.get("title", ""), meta.get("url", ""), heading, buf.strip()))
                    buf = ""
                buf += para + "\n\n"
            if buf.strip():
                n += 1
                chunks.append(Chunk(f"{doc_id}#{n:02d}", doc_id, meta.get("title", ""), meta.get("url", ""), heading, buf.strip()))
    return chunks


_kiwi = Kiwi()
_KEEP = {"NNG", "NNP", "NNB", "NR", "NP", "VV", "VA", "SL", "SN", "SH"}


def tokenize(text: str) -> list[str]:
    """한국어는 형태소, 영어는 소문자 단어로. (수업 hybrid.py 토크나이저 + 영어 소문자화)"""
    return [t.form.lower() for t in _kiwi.tokenize(text) if t.tag in _KEEP]


class HybridRetriever:
    def __init__(self) -> None:
        self.chunks = load_chunks()
        self.by_id = {c.chunk_id: c for c in self.chunks}
        self.bm25 = BM25Okapi([tokenize(f"{c.section}\n{c.text}") for c in self.chunks])
        self._vs = None

    # ---- 벡터 저장소 (처음 한 번 만든다) ----
    def _vectorstore(self):
        if self._vs is None:
            from langchain_aws import BedrockEmbeddings
            from langchain_chroma import Chroma

            emb = BedrockEmbeddings(model_id=EMBED_MODEL, region_name=REGION)
            vs = Chroma(collection_name=COLLECTION, embedding_function=emb, persist_directory=str(CHROMA_DIR))
            if vs._collection.count() != len(self.chunks):
                if vs._collection.count():
                    vs.delete_collection()
                    vs = Chroma(collection_name=COLLECTION, embedding_function=emb, persist_directory=str(CHROMA_DIR))
                vs.add_texts(
                    texts=[f"{c.title} - {c.section}\n{c.text}" for c in self.chunks],
                    metadatas=[{"chunk_id": c.chunk_id, "doc_id": c.doc_id} for c in self.chunks],
                    ids=[c.chunk_id for c in self.chunks],
                )
            self._vs = vs
        return self._vs

    def _bm25_rank(self, query: str, k: int) -> list[str]:
        scores = self.bm25.get_scores(tokenize(query))
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [self.chunks[i].chunk_id for i in order[:k] if scores[i] > 0]

    def _vector_rank(self, query: str, k: int) -> list[str]:
        docs = self._vectorstore().similarity_search(query, k=k)
        return [d.metadata["chunk_id"] for d in docs]

    def search(self, queries: list[str], k: int = 5, per_list: int = 8) -> list[Chunk]:
        """여러 검색어 × (BM25, 벡터) 순위를 RRF로 합쳐 상위 k개 청크를 돌려준다."""
        fused: dict[str, float] = {}
        for q in [q for q in queries if q and q.strip()]:
            for ranking in (self._bm25_rank(q, per_list), self._vector_rank(q, per_list)):
                for rank, cid in enumerate(ranking):
                    fused[cid] = fused.get(cid, 0.0) + 1.0 / (60 + rank + 1)
        top = sorted(fused, key=fused.get, reverse=True)[:k]
        return [self.by_id[c] for c in top]


@lru_cache(maxsize=1)
def get_retriever() -> HybridRetriever:
    return HybridRetriever()


if __name__ == "__main__":
    r = get_retriever()
    print(f"청크 {len(r.chunks)}개")
    for qs in (["관리자 승인이 필요하다는 화면", "Need admin approval admin consent"],
               ["특정 사이트 문서만 검색 안 됨", "Sites.Selected fullcontrol permission"]):
        print("=" * 60, qs)
        for c in r.search(qs, k=4):
            print(f"  {c.chunk_id:28s} {c.section[:50]}")
