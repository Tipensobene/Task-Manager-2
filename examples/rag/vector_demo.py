"""二维非零向量的余弦相似度演示，数字为手工构造，不调用模型。"""

import math

def cosine_similarity(
    left: list[float],
    right: list[float],
) -> float:

    dot_product = 0.0
    left_squared_sum = 0.0
    right_squared_sum = 0.0

    for left_value, right_value in zip(left, right, strict=True):
        dot_product += left_value * right_value
        left_squared_sum += left_value ** 2
        right_squared_sum += right_value ** 2

    first_len=math.sqrt(left_squared_sum)
    second_len=math.sqrt(right_squared_sum)

    if first_len == 0 or second_len == 0:
        raise ValueError(
            "向量长度不能为零"
        )

    return dot_product / (first_len * second_len)


def get_score(item):
    return item["score"]


def main():
    query = [1.0, 0.0]
    candidates = [
        {"text": "模拟片段A", "source": "demo-A", "vector": [1.0, 1.0]},
        {"text": "模拟片段B", "source": "demo-B", "vector": [2.0, 0.0]},
        {"text": "模拟片段C", "source": "demo-C", "vector": [0.0, 1.0]},
    ]

    scored_candidates = []

    for candidate in candidates:
        score = cosine_similarity(query, candidate["vector"])

        scored_candidates.append({
            "candidate": candidate,
            "score": score,
        })

    ranked_candidates = sorted(
        scored_candidates,
        key=get_score,
        reverse=True,
    )

    top_k = 2
    top_candidates = ranked_candidates[:top_k]
    print(top_candidates)


if __name__ == '__main__':
    main()
