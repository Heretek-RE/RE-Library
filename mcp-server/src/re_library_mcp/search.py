"""Tiny in-memory search over RE-Library entries.

This is intentionally small — ~50 entries today, maybe a few hundred at
maturity. The corpus fits in memory many times over; we don't need
whoosh, tantivy, or a server. The whole index is rebuilt on load and
served from a dict.

The scoring is plain TF-IDF with title and tag boosts. Snippets are
~200 chars centred on the first match, with the matched terms marked
(``\\<match\\>``).

The API is synchronous and pure — ``SearchIndex.build()`` returns a
``SearchIndex`` and ``SearchIndex.search()`` returns a list of
``SearchHit``. Nothing here does I/O; the loader is the only place
that talks to disk or the network.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from re_library_mcp.schema import Entry

# Match a "word": a run of letters, digits, underscores, or hyphens.
# Length-bounded to keep the index reasonable.
_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{1,40}")

# Stop words that are too common to be useful as signal.
_STOP_WORDS: frozenset[str] = frozenset(
    """
    a an and are as at be by for from has have he her his i in is it its
    of on or our she that the their them then there these they this to
    was we were what when where which who why will with would you your
    """.split()
)


def tokenize(text: str) -> list[str]:
    """Lowercase, drop stop words, return a list of tokens."""
    tokens: list[str] = []
    for m in _TOKEN_RE.finditer(text.lower()):
        tok = m.group(0)
        if tok in _STOP_WORDS or len(tok) < 2:
            continue
        tokens.append(tok)
    return tokens


@dataclass(frozen=True)
class SearchHit:
    """A single search result."""

    entry_id: str
    title: str
    category: str
    snippet: str
    score: float

    def to_dict(self) -> dict:
        return {
            "slug": self.entry_id,
            "title": self.title,
            "category": self.category,
            "snippet": self.snippet,
            "score": round(self.score, 4),
        }


class SearchIndex:
    """An in-memory inverted index over a set of entries.

    Build once with ``SearchIndex.build(entries)``, then call
    ``.search(query, ...)`` any number of times.
    """

    # How many characters of context to show on each side of the match.
    SNIPPET_PAD = 100

    def __init__(
        self,
        entries: list[Entry],
        *,
        postings: dict[str, list[tuple[str, int]]],
        doc_lens: dict[str, int],
        title_index: Counter[str],
        tag_index: Counter[str],
    ) -> None:
        self._entries = entries
        self._by_id: dict[str, Entry] = {e.id: e for e in entries}
        # postings: token -> list of (entry_id, term_frequency_in_doc)
        self._postings = postings
        # doc_lens: entry_id -> number of tokens in body
        self._doc_lens = doc_lens
        # Per-doc counters for title and tag tokens (boosted scoring)
        self._title_index = title_index
        self._tag_index = tag_index
        # Document count
        self._n = len(entries)
        # Average document length (for length-normalised scoring)
        self._avg_len = (
            sum(doc_lens.values()) / self._n if self._n else 1.0
        )

    @classmethod
    def build(cls, entries: list[Entry]) -> "SearchIndex":
        postings: dict[str, list[tuple[str, int]]] = {}
        doc_lens: dict[str, int] = {}
        title_counter: Counter[str] = Counter()
        tag_counter: Counter[str] = Counter()

        for entry in entries:
            body_tokens = tokenize(entry.body)
            doc_lens[entry.id] = len(body_tokens) or 1
            counts = Counter(body_tokens)
            for tok, c in counts.items():
                postings.setdefault(tok, []).append((entry.id, c))
            # Title tokens get a 5x boost
            for tok in tokenize(entry.frontmatter.title):
                title_counter[tok] += 5
            # Tag tokens get a 3x boost
            for tag in entry.frontmatter.tags:
                for tok in tokenize(tag):
                    tag_counter[tok] += 3

        return cls(
            entries=entries,
            postings=postings,
            doc_lens=doc_lens,
            title_index=title_counter,
            tag_index=tag_counter,
        )

    @property
    def entries(self) -> list[Entry]:
        return list(self._entries)

    def get(self, entry_id: str) -> Entry | None:
        return self._by_id.get(entry_id)

    def _idf(self, token: str) -> float:
        """Inverse document frequency — log(N / df) with smoothing."""
        df = len(self._postings.get(token, ()))
        if df == 0:
            return 0.0
        return math.log((1 + self._n) / (1 + df)) + 1.0

    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        max_results: int = 5,
    ) -> list[SearchHit]:
        """Return up to ``max_results`` hits for ``query``."""
        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        # Accumulate per-doc scores.
        scores: dict[str, float] = {}
        for tok in q_tokens:
            idf = self._idf(tok)
            # Body postings
            for entry_id, tf in self._postings.get(tok, ()):
                if category and self._by_id[entry_id].category != category:
                    continue
                # BM25-flavoured length normalisation
                b = 0.75
                k1 = 1.5
                dl = self._doc_lens[entry_id]
                norm = (1 - b) + b * (dl / self._avg_len)
                score = idf * ((tf * (k1 + 1)) / (tf + k1 * norm))
                scores[entry_id] = scores.get(entry_id, 0.0) + score
            # Title boost
            for entry_id, count in self._title_index.items():
                if entry_id != tok:
                    continue
                # (Counter stores (token, count); iterate to find matching tokens)
            # Title boost — re-iterate correctly:
            title_boost = self._title_index.get(tok, 0)
            if title_boost:
                # Apply to every doc whose title contains tok — but the
                # counter is per-token, not per-doc, so we don't know
                # *which* docs share the title token. Fall back to a doc-
                # independent title boost applied to docs that mention the
                # token in their title field directly:
                for entry in self._entries:
                    if category and entry.category != category:
                        continue
                    if tok in tokenize(entry.frontmatter.title):
                        scores[entry.id] = scores.get(entry.id, 0.0) + 3.0
            # Tag boost
            tag_boost = self._tag_index.get(tok, 0)
            if tag_boost:
                for entry in self._entries:
                    if category and entry.category != category:
                        continue
                    if any(tok in tokenize(t) for t in entry.frontmatter.tags):
                        scores[entry.id] = scores.get(entry.id, 0.0) + 1.5

        if not scores:
            return []

        ranked = sorted(scores.items(), key=lambda kv: -kv[1])[:max_results]
        hits: list[SearchHit] = []
        for entry_id, score in ranked:
            entry = self._by_id[entry_id]
            hits.append(
                SearchHit(
                    entry_id=entry_id,
                    title=entry.title,
                    category=entry.category,
                    snippet=self._snippet(entry, q_tokens),
                    score=score,
                )
            )
        return hits

    def _snippet(self, entry: Entry, q_tokens: list[str]) -> str:
        """Build a ~200-char snippet around the first match in the body."""
        body = entry.body
        lower = body.lower()
        # Find the earliest match position across all query tokens.
        best_pos = -1
        for tok in q_tokens:
            i = lower.find(tok)
            if i == -1:
                continue
            if best_pos == -1 or i < best_pos:
                best_pos = i
        if best_pos == -1:
            # No match in body — fall back to start of body
            return body[: 2 * self.SNIPPET_PAD].strip()
        start = max(0, best_pos - self.SNIPPET_PAD)
        end = min(len(body), best_pos + self.SNIPPET_PAD)
        snippet = body[start:end].strip()
        # Mark matched terms with <mark>…</mark>
        for tok in sorted(set(q_tokens), key=len, reverse=True):
            snippet = re.sub(
                rf"(?i)\b{re.escape(tok)}\b",
                lambda m: f"<mark>{m.group(0)}</mark>",
                snippet,
            )
        if start > 0:
            snippet = "…" + snippet
        if end < len(body):
            snippet = snippet + "…"
        return snippet
