import asyncio
import json
import argparse
from pathlib import Path


from examples.rag.embedding_demo import get_embedding
from examples.rag.vector_demo import cosine_similarity, get_score
from examples.rag.answer_demo import generate_answer

def split_paragraphs(text: str, source: str) -> list[dict]:

    chunks = []  # 已经完成的段落
    current_lines = []  # 当前正在收集的段落文字
    start_line = None  # 当前段落从哪行开始
    for line_number, line in enumerate(text.splitlines(), start=1):
        cleaned_line = line.strip()

        if cleaned_line:

            if not current_lines:
                start_line=line_number

            current_lines.append(cleaned_line)

        else:
            if current_lines:

                chunk={
                    "text":"\n".join(current_lines),
                    "source":source,
                    "start_line":start_line,
                    "end_line":line_number-1,
                }

                chunks.append(chunk)

                current_lines.clear()
                start_line=None

    if current_lines:
        chunk={
            "text":"\n".join(current_lines),
            "source":source,
            "start_line":start_line,
            "end_line":line_number
        }

        chunks.append(chunk)

    return chunks


def rank_candidates(query_vector, candidates, top_k=2):
    scored_candidates = []
    for candidate in candidates:

        score = cosine_similarity(query_vector, candidate["vector"])
        scored_candidates.append({
            "candidate": candidate,
            "score": score,
        })

    ranked_candidates = sorted(
        scored_candidates,
        key=get_score,
        reverse=True,
    )


    return ranked_candidates[:top_k]

async def main(question: str, top_k: int = 2):

    file_path = Path("examples/rag/notes.txt")
    text = file_path.read_text(
        encoding="utf-8",
    )

    cache_path = Path("examples/rag/notes_vectors.json")
    cache_valid = False

    if cache_path.exists():
        with cache_path.open("r", encoding="utf-8") as file:
            cache_data = json.load(file)

        cache_valid = (
                cache_data["model"] == "text-embedding-v4"
                and cache_data["dimensions"] == 1024
                and cache_data["source"] == str(file_path)
                and cache_data["source_text"] == text
                and cache_data.get("chunking") == "paragraph-v1"
        )

    if cache_valid:
        candidates = cache_data["candidates"]
        print("复用文档向量缓存")
    else:
        print("重新计算文档向量")

        candidates = split_paragraphs(text, str(file_path))

        for candidate in candidates:
            vector = await get_embedding(candidate["text"])
            candidate["vector"] = vector

        # 保存生成向量时的原文与配置，供后续判断缓存是否仍可复用。
        cache_data = {
            "model": "text-embedding-v4",
            "dimensions": 1024,
            "source": str(file_path),
            "source_text": text,
            "candidates": candidates,
            "chunking": "paragraph-v1",
        }
        # w模式会创建或覆盖此文件；缓存只保存资料和向量，不保存密钥。
        with open("examples/rag/notes_vectors.json", "w", encoding="utf-8") as file:
            json.dump(cache_data, file, ensure_ascii=False, indent=2)

    # 从这里开始，保留原来的问题向量、检索及回答代码。


    query_vector = await get_embedding(question)

    top_candidates = rank_candidates(
        query_vector,
        candidates,
        top_k=top_k,
    )

    if not top_candidates:
        print("没有可供回答的参考资料。")
        return

    context_parts=[]
    for number,item in enumerate(top_candidates,start=1):
        candidate = item["candidate"]

        block=(
            f"""
            [资料{number}]
            来源：{candidate["source"]}
            行号：{candidate["start_line"]}-{candidate["end_line"]}
            正文：{candidate["text"]}
            """
        )
        context_parts.append(block)

    context = "\n\n".join(context_parts)

    answer = await generate_answer(question, context)

    print("模型回答：")
    print(answer)

    for item in top_candidates:
        print(
            item["candidate"]["text"],
            item["candidate"]["source"],
            f'{item["candidate"]["start_line"]}-{item["candidate"]["end_line"]}',
            item["score"],
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="根据本地笔记回答问题")
    parser.add_argument("question", help="要查询的问题")
    parser.add_argument(
        "--top-k",
        type=int,
        default=2,
        choices=(1,2,3),
        help="交给回答模型的最大资料条数，默认2",
    )
    args = parser.parse_args()
    asyncio.run(main(args.question, top_k=args.top_k))
