
from pathlib import Path

file_path = Path("examples/rag/notes.txt")
text = file_path.read_text(encoding="utf-8")
print("从文件读取的正文：")
print(text)

# 将整份文档的真实来源和读取到的正文放在一起，供后续分块使用。
document = {
    "source": str(file_path),
    "text": text,
}
print("文档来源：", document["source"])
print("文档正文：")
print(document["text"])

# 当前示例一行一条知识，先按行拆分；此时列表中的元素仍是字符串。
lines = document["text"].splitlines()
print("按行拆分后的正文：")
for line in lines:
    print(line)

# 先对原始行编号，再跳过空行，确保行号可以定位回原文件。
document_chunks = []
for line_number, line in enumerate(lines, start=1):
    cleaned_text = line.strip()
    if not cleaned_text:
        continue

    document_chunks.append({
        "source": document["source"],
        "line_number": line_number,
        "text": cleaned_text,
    })

print("从真实文档生成的片段：")
for document_chunk in document_chunks:
    print(document_chunk)

# 最小关键词检索：只做区分大小写的文字包含匹配，命中后保留整条记录。
keyword = "commit"
matched_chunks = []
for document_chunk in document_chunks:
    if keyword in document_chunk["text"]:
        matched_chunks.append(document_chunk)

print("检索关键词：", keyword)
print("检索结果：", matched_chunks)

chunks=[
    {
        "chunk_id":"database-001",
        "source":"数据库测试笔记.md",
        "section":"事务提交",
        "text":"flush 将当前待处理的修改发送到数据库，但不提交事务。",
    },
    {
        "chunk_id":"database-002",
        "source":"数据库测试笔记.md",
        "section":"内存数据库连接",
        "text":"StaticPool 可以让连接池复用同一个底层连接。",
    }
]

for chunk in chunks:
    print(chunk["chunk_id"])
    print(chunk["source"])
    print(chunk["text"])

second_chunk=chunks[1]
print(second_chunk["chunk_id"])
print(second_chunk["source"])
print(second_chunk["text"])
print(second_chunk["section"])
