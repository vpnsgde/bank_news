import os
import sqlite3

DB_DIR = "../db"
OUTPUT_DB = os.path.join(DB_DIR, "total_news.db")

SOURCE_MAP = {
    "vst": "VietStock",
    "vnfi": "VietNamFinance",
    "vne": "VnEconomy",
    "tbkt": "ThoiBaoKinhTe",
    "nqs": "NguoiQuanSat",
    "ktck": "KinhTeChungKhoan",
}


def get_table_schema(conn, table_name):
    """
    Trả về list tuple: (column_name, column_type)
    """
    cur = conn.execute(f"PRAGMA table_info({table_name})")
    return [(row[1], row[2]) for row in cur.fetchall()]


def main():
    # --- Kết nối DB output ---
    out_conn = sqlite3.connect(OUTPUT_DB)
    out_cur = out_conn.cursor()

    base_schema = None
    insert_sql = None
    col_names = None

    # --- Kiểm tra table articles đã tồn tại chưa ---
    out_cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='articles'"
    )
    exists = out_cur.fetchone() is not None

    # Nếu chưa có table, tạo mới
    if not exists:
        first_db = next(iter(SOURCE_MAP))  # Lấy DB đầu tiên làm schema
        db_path = os.path.join(DB_DIR, f"{first_db}.db")
        in_conn = sqlite3.connect(db_path)
        schema = get_table_schema(in_conn, "articles")
        in_conn.close()

        if not schema:
            raise RuntimeError(f"No articles table found in {first_db}.db")

        base_schema = schema
        col_names = [name for name, _ in base_schema]

        columns_def = [f"{name} {ctype}" for name, ctype in base_schema]
        columns_def.append("source TEXT")

        out_cur.execute(f"""
            CREATE TABLE articles (
                {", ".join(columns_def)}
            )
        """)

        # --- Unique index để dedup (href_hash + source) ---
        out_cur.execute("""
            CREATE UNIQUE INDEX idx_articles_href_source
            ON articles (href_hash, source)
        """)
        out_conn.commit()
    else:
        # Nếu table đã tồn tại, đọc schema
        base_schema = get_table_schema(out_conn, "articles")
        col_names = [name for name, _ in base_schema if name != "source"]

    # --- Prepare insert SQL ---
    placeholders = ",".join(["?"] * (len(col_names) + 1))
    insert_sql = f"""
        INSERT OR IGNORE INTO articles ({",".join(col_names)}, source)
        VALUES ({placeholders})
    """

    # --- Duyệt từng DB nguồn ---
    for short_name, source_name in SOURCE_MAP.items():
        db_path = os.path.join(DB_DIR, f"{short_name}.db")
        if not os.path.exists(db_path):
            print(f"[WARN] Missing DB: {db_path}")
            continue

        print(f"[INFO] Processing {db_path}")
        in_conn = sqlite3.connect(db_path)
        in_cur = in_conn.cursor()

        select_sql = f"SELECT {','.join(col_names)} FROM articles"
        try:
            rows = in_cur.execute(select_sql).fetchall()
        except sqlite3.OperationalError:
            print(f"[WARN] Table 'articles' not found in {db_path}, skipping")
            in_conn.close()
            continue

        data_to_insert = [tuple(row) + (source_name,) for row in rows]

        out_cur.executemany(insert_sql, data_to_insert)
        out_conn.commit()

        print(f"[INFO] Inserted {len(rows)} records from {short_name}")

        in_conn.close()

    # --- Tạo bảng categories nếu chưa tồn tại ---
    out_cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category TEXT PRIMARY KEY
        )
    """)
    out_conn.commit()

    # --- Lấy tất cả category duy nhất từ articles ---
    out_cur.execute("SELECT DISTINCT category FROM articles")
    categories = [row[0] for row in out_cur.fetchall() if row[0]]

    # --- Chèn vào bảng categories ---
    if categories:
        out_cur.executemany(
            "INSERT OR IGNORE INTO categories (category) VALUES (?)",
            [(cat,) for cat in categories]
        )
        out_conn.commit()
        print(f"[INFO] Inserted {len(categories)} unique categories into 'categories' table")

    out_conn.close()
    print("[DONE] Merge completed incrementally with dedup on (href_hash, source) and categories updated")


if __name__ == "__main__":
    main()
