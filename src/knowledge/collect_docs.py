"""공식 문서 수집기.

Gemini Enterprise 공식 문서(docs.cloud.google.com, CC BY 4.0)를 내려받아
본문만 마크다운에 가깝게 바꿔 data/docs/{doc_id}.md 로 저장한다.
파일 맨 위에 doc_id·제목·URL·최종 업데이트일·라이선스·수집일을 적는다.

실행: python -m src.knowledge.collect_docs
"""
from __future__ import annotations

import datetime as dt
import html
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://docs.cloud.google.com/gemini/enterprise/docs/"
DOCS = {
    "ge-sp-overview": "connectors/ms-sharepoint",
    "ge-sp-config": "connectors/ms-sharepoint/third-party-config",
    "ge-sp-datastore": "connectors/ms-sharepoint/set-up-data-store",
    "ge-sp-filters": "connectors/ms-sharepoint/add-filters-to-sharepoint-data-store",
    "ge-idp": "configure-identity-provider",
    "ge-entra-connector": "connectors/entra-id/connect-entra-id",
    "ge-connectors-intro": "connectors/introduction-to-connectors-and-data-stores",
    "ge-confluence-cloud": "connectors/confluence-cloud/third-party-config",
    "ge-access-control": "access-control",
}
OUT = Path(__file__).resolve().parents[2] / "data" / "docs"   # 저장소 루트의 data/docs

BLOCK = {"p", "li", "tr", "pre", "h1", "h2", "h3", "h4", "h5", "dt", "dd", "table", "div", "section", "aside"}
SKIP = {"script", "style", "nav", "button", "devsite-feedback", "devsite-thumb-rating", "svg"}


class ArticleText(HTMLParser):
    """devsite-article-body 안의 글만 모은다."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0          # article-body 안에서의 div 깊이
        self.skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class") or ""
        if self.depth == 0:
            if tag == "div" and "devsite-article-body" in cls:
                self.depth = 1
            return
        if tag == "div":
            self.depth += 1
        if tag in SKIP:
            self.skip += 1
            return
        if self.skip:
            return
        if tag in ("h1", "h2", "h3", "h4", "h5"):
            self.parts.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag in ("td", "th"):
            self.parts.append(" | ")
        elif tag in BLOCK or tag == "br":
            self.parts.append("\n")
        elif tag == "code":
            self.parts.append("`")

    def handle_endtag(self, tag):
        if self.depth == 0:
            return
        if tag in SKIP and self.skip:
            self.skip -= 1
            return
        if self.skip:
            return
        if tag == "code":
            self.parts.append("`")
        elif tag in BLOCK:
            self.parts.append("\n")
        if tag == "div":
            self.depth -= 1

    def handle_data(self, data):
        if self.depth and not self.skip:
            self.parts.append(data)

    def text(self) -> str:
        t = "".join(self.parts)
        t = re.sub(r"[ \t]+", " ", t)
        t = re.sub(r" *\n *", "\n", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
        return t.strip()


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (doc-collector)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    for doc_id, path in DOCS.items():
        url = BASE + path
        raw = fetch(url + "?hl=en")
        title_m = re.search(r"<title>(.*?)</title>", raw, re.S)
        title = html.unescape(title_m.group(1)).split("|")[0].strip() if title_m else doc_id
        upd_m = re.search(r"Last updated (\d{4}-\d{2}-\d{2}) UTC", raw)
        lic = "CC BY 4.0" if "Creative Commons Attribution 4.0 License" in raw else "확인 필요"
        p = ArticleText()
        p.feed(raw)
        body = p.text()
        header = (
            f"---\ndoc_id: {doc_id}\ntitle: {title}\nurl: {url}\n"
            f"last_updated: {upd_m.group(1) if upd_m else 'unknown'}\n"
            f"license: {lic} (Google Cloud documentation, attribution required)\ncollected_at: {today}\n---\n\n"
        )
        (OUT / f"{doc_id}.md").write_text(header + body + "\n", encoding="utf-8")
        print(f"{doc_id}: {len(body):>6} chars, updated {upd_m.group(1) if upd_m else '?'}, {lic}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
