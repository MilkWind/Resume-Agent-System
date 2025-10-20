"""
简历数据一致性检查脚本（SQLite 与 ChromaDB）

大白话：
- 检查 SQLite 中的简历数量
- 检查 ChromaDB 中的向量数量
- 取最近一条简历核对其向量是否存在

运行方式：
    python backend/test_db_check.py
"""

from typing import Optional

from app.database.base import SessionLocal, Base, engine
from app.database.models import Resume
from app.database.crud import get_all_resumes
from app.utils.config import VECTOR_DB_PATH

import chromadb


def check_sqlite() -> int:
    """返回 SQLite 中的简历总数，并打印最近一条信息"""
    # 确保表存在（幂等）
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        total = db.query(Resume).count()
        print(f"[SQLite] 简历总数：{total}")
        if total > 0:
            latest = get_all_resumes(db, skip=0, limit=1)
            row: Optional[Resume] = latest[0] if latest else None
            if row:
                print(
                    f"[SQLite] 最近一条：id={row.id}, filename={row.filename}, vector_id={row.vector_id}"
                )
        return total
    finally:
        db.close()


def check_chroma(expected_latest_id: Optional[int]) -> int:
    """返回 ChromaDB 中向量总数，并检查指定ID是否存在"""
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    col = client.get_or_create_collection(
        name="resumes", metadata={"hnsw:space": "cosine"}
    )
    try:
        total = col.count()  # 向量条目数量
        print(f"[Chroma] 向量总数：{total}")

        if expected_latest_id is not None:
            doc_id = f"resume_{expected_latest_id}"
            got = col.get(ids=[doc_id])
            found = bool(got and got.get("ids") and len(got["ids"]) > 0)
            print(
                f"[Chroma] 最近一条向量存在性（{doc_id}）：{'✅ 存在' if found else '❌ 不存在'}"
            )
        return total
    finally:
        # Chroma 无需显式关闭
        pass


def main() -> None:
    print("=== 开始检查 SQLite 与 ChromaDB 数据一致性 ===")
    sqlite_total = check_sqlite()

    # 为对齐检查，尝试读取最近一条的ID
    db = SessionLocal()
    last_id: Optional[int] = None
    try:
        if sqlite_total > 0:
            latest = get_all_resumes(db, skip=0, limit=1)
            if latest:
                last_id = latest[0].id
    finally:
        db.close()

    chroma_total = check_chroma(last_id)

    # 简单一致性提示（数量不一定严格相等，但通常应接近）
    if sqlite_total == 0 and chroma_total == 0:
        print("结论：两个库目前均为空，请先调用 /api/resume/parse 上传简历再试。")
    elif sqlite_total >= 1 and chroma_total >= 1:
        print("结论：两个库均已写入数据，基础检查通过。")
    else:
        print("结论：数量不一致，请检查最近一次写入流程或错误日志。")


if __name__ == "__main__":
    main()


