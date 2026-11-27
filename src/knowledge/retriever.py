"""RAG 검색기: 공식 문서 하이브리드 검색 (패턴 3).

- 문서: data/docs/*.md (Gemini Enterprise 공식 문서, CC BY 4.0)
- 청크: 마크다운 제목(##, ###) 단위로 자른 뒤 1,200자 안팎으로 나눈다.
  청크 ID는 "{doc_id}#{번호}" 이고, 이 값이 /query 응답 contexts[].doc_id 가 된다.
- 검색: Chroma 벡터(Bedrock Titan v2 임베딩) + BM25(kiwipiepy 형태소) 결과를
  RRF(Reciprocal Rank Fusion)로 합친다. 한국어 질문과 영어 검색어를 둘 다 넣는다(D-5).
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from kiwipiepy import Kiwi
from rank_bm25 import BM25Okapi

from src.utils.paths import ROOT

load_dotenv(ROOT / ".env")

DOCS_DIR = ROOT / "data" / "docs"
CHROMA_DIR = ROOT / "chroma_db"
COLLECTION_PREFIX = "ge_docs_"   # 실제 컬렉션 이름은 문서 내용 지문을 붙인다(아래 _fingerprint)
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


log = logging.getLogger(__name__)


def _fingerprint(chunks: list[Chunk]) -> str:
    """[중간평가 반영] 청크 ID·본문으로 만든 지문. 전에는 청크 수만 비교해, 수가 같은 문서 수정에서는 옛 벡터를 그대로 썼다."""
    h = hashlib.sha256()
    for c in chunks:
        h.update("|".join([c.chunk_id, c.title, c.section, c.text]).encode("utf-8"))
    return h.hexdigest()[:12]


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
        self.collection = COLLECTION_PREFIX + _fingerprint(self.chunks)
        self.vector_ok = True   # 벡터 검색이 실패하면 False 로 바꾸고 BM25 만으로 답한다

    # ---- 벡터 저장소 (처음 한 번 만든다) ----
    def _vectorstore(self):
        if self._vs is None:
            from langchain_aws import BedrockEmbeddings
            from langchain_chroma import Chroma

            emb = BedrockEmbeddings(model_id=EMBED_MODEL, region_name=REGION)
            vs = Chroma(collection_name=self.collection, embedding_function=emb, persist_directory=str(CHROMA_DIR))
            if vs._collection.count() != len(self.chunks):
                if vs._collection.count():   # 같은 지문인데 수가 다르면(만들다 끊긴 경우) 지우고 다시 만든다
                    vs.delete_collection()
                    vs = Chroma(collection_name=self.collection, embedding_function=emb, persist_directory=str(CHROMA_DIR))
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
        # [중간평가 반영] 임베딩 호출·색인이 실패해도 검색 전체가 죽지 않게, 이 순위만 비우고 BM25 결과로 답한다
        try:
            docs = self._vectorstore().similarity_search(query, k=k)
        except Exception as e:  # noqa: BLE001 - 어떤 실패든 BM25 로 대체
            if self.vector_ok:
                log.warning("벡터 검색 실패, BM25만 사용: %s", type(e).__name__)
            self.vector_ok = False
            return []
        self.vector_ok = True
        return [d.metadata["chunk_id"] for d in docs]

    def search(self, queries: list[str], k: int = 5, per_list: int = 8) -> list[Chunk]:
        """여러 검색어 × (BM25, 벡터) 순위를 RRF로 합쳐 상위 k개 청크를 돌려준다."""
        fused: dict[str, float] = {}
        for q in [q for q in queries if q and q.strip()]:
            for ranking in (self._bm25_rank(q, per_list), self._vector_rank(q, per_list)):
                for rank, cid in enumerate(ranking):
                    fused[cid] = fused.get(cid, 0.0) + 1.0 / (60 + rank + 1)
        top = sorted(fused, key=fused.get, reverse=True)[:k]
        return [self.by_id[c] for c in top if c in self.by_id]   # 색인에만 남은 옛 ID는 건너뛴다


@lru_cache(maxsize=1)
def get_retriever() -> HybridRetriever:
    return HybridRetriever()


def warm_up() -> int:
    """[추가 구현] 검색 인덱스를 미리 만든다. 깨끗한 clone에서는 chroma_db가 없어 첫 요청 안에서 임베딩 209개를 만들다
    에이전트 시간 상한(60초)을 넘겼다(AC-8 점검에서 발견). 서버·평가 시작 때 한 번 불러 둔다. 청크 수를 돌려준다."""
    r = get_retriever()
    try:
        r._vectorstore()
    except Exception as e:  # noqa: BLE001 - [중간평가 반영] 색인 준비가 실패해도 서버·화면은 뜨고 BM25로 검색한다
        r.vector_ok = False
        log.warning("검색 색인 준비 실패, BM25만 사용: %s", type(e).__name__)
    return len(r.chunks)


if __name__ == "__main__":
    r = get_retriever()
    print(f"청크 {len(r.chunks)}개")
    for qs in (["관리자 승인이 필요하다는 화면", "Need admin approval admin consent"],
               ["특정 사이트 문서만 검색 안 됨", "Sites.Selected fullcontrol permission"]):
        print("=" * 60, qs)
        for c in r.search(qs, k=4):
            print(f"  {c.chunk_id:28s} {c.section[:50]}")
