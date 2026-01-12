import os
import json
import sqlite3
import binascii

DATA_FILE = "./data/ktck_news.json"
DB_PATH = "../db/ktck.db"


def ensure_tables(conn: sqlite3.Connection):
    """
    Tạo bảng articles và categories nếu chưa tồn tại
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            href TEXT NOT NULL,
            category TEXT NOT NULL,
            publish_date TEXT NOT NULL,
            title_latin TEXT NOT NULL,
            href_hash BLOB NOT NULL,
            publish_ts INTEGER NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    conn.commit()


def hex_to_blob(hex_str: str) -> bytes:
    """
    MD5 hex -> BLOB (16 bytes)
    """
    return binascii.unhexlify(hex_str)


def main():
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"Missing data file: {DATA_FILE}")

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    ensure_tables(conn)

    insert_article_sql = """
        INSERT INTO articles (
            title,
            href,
            category,
            publish_date,
            title_latin,
            href_hash,
            publish_ts
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    insert_category_sql = """
        INSERT OR IGNORE INTO categories (name)
        VALUES (?)
    """

    article_count = 0
    category_count = 0

    for r in records:
        # insert category (dedup)
        conn.execute(insert_category_sql, (r["category"],))
        category_count += 1

        # insert article (no dedup)
        conn.execute(
            insert_article_sql,
            (
                r["title"],
                r["href"],
                r["category"],
                r["publish_date"],
                r["title_latin"],
                hex_to_blob(r["href_hash"]),
                int(r["publish_ts"])
            )
        )
        article_count += 1

    conn.commit()
    conn.close()

    print(f"Inserted {article_count} articles into table 'articles'")
    print(f"Processed {category_count} category references (deduped in 'categories')")


if __name__ == "__main__":
    main()
