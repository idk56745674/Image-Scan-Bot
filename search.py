
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

    missing = db.tags_missing_vectors(guild_id)
    for i in range(0, len(missing), 64):
        batch = missing[i:i + 64]
        db.save_vectors(guild_id, batch, await ai.embed(batch))


async def _fuzzy_tags(guild_id: int, terms: list[str], vocab: list[str]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {t: {} for t in terms}


    for term in terms:
        if " " in term or len(term) < 3:
            continue
        for tag in vocab:
            if " " not in tag and len(tag) >= 3 and (term in tag or tag in term):
                result[term][tag] = 0.85


    try:
        await ensure_vectors(guild_id)
        tags, matrix = db.load_vectors(guild_id)
        if tags:
            query_vecs = await ai.embed(terms)
            sims = query_vecs @ matrix.T
            for i, term in enumerate(terms):
                for j in np.argsort(sims[i])[::-1][:config.SIMILAR_TAGS_PER_WORD]:
                    s = float(sims[i][j])
                    if s >= config.SIMILARITY_THRESHOLD:
                        result[term][tags[j]] = max(result[term].get(tags[j], 0), s)
    except Exception as e:
        print(f"Vector search unavailable: {e}")

    return result


async def find_images(guild_id: int, terms: list[str], limit: int) -> list[SearchResult]:
    vocab = db.all_tags(guild_id)

    # term -> {tag: weight}
    expansions: dict[str, dict[str, float]] = {}
    unmatched = []
    for term in terms:
        exp: dict[str, float] = {}
        padded = f" {term} "
        for tag in vocab:
            if tag == term:
                exp[tag] = 1.0
            elif padded in f" {tag} ":  # whole-word containment, never partial words
                exp[tag] = 0.9
        expansions[term] = exp
        if not exp:
            unmatched.append(term)

    if unmatched and vocab:
        expansions.update(await _fuzzy_tags(guild_id, unmatched, vocab))

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
        SearchResult(score, exact, len(terms), *rows[image_id])
        for score, exact, image_id in top
    ]
