"""Tag search: exact matches first, similar tags (substring + vector) when a word has no exact match."""
from collections import defaultdict
from dataclasses import dataclass

import numpy as np

import ai
import config
import database as db


@dataclass
class SearchResult:
    score: float
    exact_matches: int
    total_words: int
    image_url: str
    description: str
    author: str
    jump_url: str


async def ensure_vectors(guild_id: int) -> None:
    """Embed any tags that don't have a stored vector yet."""
    missing = db.tags_missing_vectors(guild_id)
    for i in range(0, len(missing), 64):
        batch = missing[i:i + 64]
        db.save_vectors(guild_id, batch, await ai.embed(batch))


async def _similar_tags(guild_id: int, words: list[str], vocab: list[str]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {w: {} for w in words}


    for w in words:
        if len(w) < 3:
            continue
        for tag in vocab:
            if len(tag) >= 3 and (w in tag or tag in w):
                result[w][tag] = 0.9

    try:
        await ensure_vectors(guild_id)
        tags, matrix = db.load_vectors(guild_id)
        if tags:
            query_vecs = await ai.embed(words)
            sims = query_vecs @ matrix.T
            for i, w in enumerate(words):
                for j in np.argsort(sims[i])[::-1][:config.SIMILAR_TAGS_PER_WORD]:
                    s = float(sims[i][j])
                    if s >= config.SIMILARITY_THRESHOLD:
                        result[w][tags[j]] = max(result[w].get(tags[j], 0), s)
    except Exception as e:  
        print(f"Vector search unavailable: {e}")

    return result


async def find_images(guild_id: int, query_words: list[str], limit: int) -> list[SearchResult]:
    vocab = db.all_tags(guild_id)
    vocab_set = set(vocab)

    expansions: dict[str, dict[str, float]] = {}
    unmatched = []
    for w in query_words:
        if w in vocab_set:
            expansions[w] = {w: 1.0}
        else:
            unmatched.append(w)

    if unmatched and vocab:
        expansions.update(await _similar_tags(guild_id, unmatched, vocab))

    wanted_tags = {t for exp in expansions.values() for t in exp}
    image_tags: dict[int, set[str]] = defaultdict(set)
    for image_id, tag in db.images_for_tags(guild_id, list(wanted_tags)):
        image_tags[image_id].add(tag)

    scored = []
    for image_id, tags in image_tags.items():
        score, exact = 0.0, 0
        for exp in expansions.values():
            best = max((wt for t, wt in exp.items() if t in tags), default=0.0)
            score += best
            if best == 1.0:
                exact += 1
        scored.append((score, exact, image_id))
    scored.sort(reverse=True)
    top = scored[:limit]

    rows = db.get_images(guild_id, [i for _, _, i in top])
    return [
        SearchResult(score, exact, len(query_words), *rows[image_id])
        for score, exact, image_id in top
    ]
