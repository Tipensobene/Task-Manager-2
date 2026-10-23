
from llm_service import generate_candidate



if __name__ == "__main__":
    candidate = generate_candidate(
        "高优先级学习SQLAlchemy，重点理解Session，标签是Python。"
    )
    print(candidate.title)
    print(candidate.model_dump())

