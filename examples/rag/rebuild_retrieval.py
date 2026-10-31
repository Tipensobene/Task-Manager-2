from examples.rag.vector_demo import cosine_similarity

def retrieve(query_vector, candidates, top_k=2, section=None):

    if section is not None:
        filtered_candidates = []
        for candidate in candidates:
            if candidate["section"] == section:
                filtered_candidates.append(candidate)
        final_candidates = filtered_candidates

    else:
        final_candidates = candidates

    scored_candidates = []
    for candidate in final_candidates:
        score = cosine_similarity(query_vector, candidate["vector"])

        scored_candidates.append(
            {
                "candidate": candidate,
                "score": score,
            }
        )

    ranked_candidates=sorted(
        scored_candidates,
        key=lambda x:x["score"],
        reverse=True,
    )

    return ranked_candidates[:top_k]
