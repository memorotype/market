from rapidfuzz import fuzz, process

def normalize(s: str) -> str:
    return s.strip().lower()

def fuzzy_best_match(query: str, candidates: list[str], threshold=80):
    q = normalize(query)
    results = process.extract(q, candidates, scorer=fuzz.WRatio, limit=5)
    if not results:
        return None
    best, score = results[0]
    return (best, score) if score >= threshold else None
