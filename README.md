# Bank News ETL & Viewer

## 📌 Tổng quan dự án

Dự án **Bank News ETL & Viewer** là hệ thống thu thập, xử lý và hiển thị tin tức ngân hàng/tài chính từ nhiều nguồn, bao gồm cả luồng tự động ETL qua Airflow và GUI Web chạy Streamlit.
Hệ thống đã được phát triển đầy đủ, vận hành bằng 3 script `.sh` chính, không cần thao tác trực tiếp các file bên trong.

### Mục tiêu

* Thu thập tin tức từ các nguồn: nqs, ktck, vne, vst, tbkt, vnfi.
* Chỉ lấy các thông tin quan trọng: `Title`, `Link`, `Datetime`, `Category`.
* Lưu trữ riêng rẽ các DB nguồn (`nqs.db`, `ktck.db`, ...) và tổng hợp `total_news.db`.
* Hiển thị dữ liệu qua GUI Streamlit, filter theo Category, Read/Favorite, Keyword, Load more.
* Quản lý ETL tự động qua Airflow DAG `update_all`.

---

## ⚙️ Tech Stack

* Python 3.x
* Streamlit (GUI)
* SQLite3 (DB)
* Pandas (xử lý dữ liệu)
* Bash (script vận hành)
* Airflow (quản lý DAG ETL)

---

## 🗂️ Cấu trúc thư mục

```
.
├── airflow                  # Airflow DAG & configs
│   ├── dags
│   │   └── update_all.py
│   └── airflow.db
├── db                       # DB nguồn & tổng hợp
├── etl                      # Script ETL & data json
├── gui                      # Streamlit app
├── run_app.sh               # Chạy GUI
├── setup.sh                 # Cài đặt môi trường
└── update_all.sh            # Chạy toàn bộ DAG + GUI
```

* **airflow/**: chứa DAG `update_all` và môi trường Airflow.
* **db/**: các SQLite DB nguồn và tổng hợp.
* **etl/**: script extract/transform/load, dữ liệu json.
* **gui/**: Streamlit app hiển thị tin.
* **.sh scripts**: vận hành setup, GUI, ETL/Airflow.

---

## ⚡ Quy trình vận hành

### 1️⃣ Cài đặt môi trường

Chạy:

```bash
./setup.sh
```

* Cài virtualenv cho Airflow, ETL, GUI.
* Cài các requirements tương ứng.

### 2️⃣ Chạy Airflow & ETL tự động

```bash
./update_all.sh
```

* Dừng mọi tiến trình Airflow cũ.
* Khởi tạo Airflow DB nếu chưa có.
* Start Airflow Webserver + Scheduler.
* Mở trình duyệt Airflow UI. (**user: admin, pass: admin**)
* Trigger DAG `update_all` để chạy toàn bộ pipeline ETL.

### 3️⃣ Chạy GUI Streamlit

```bash
./run_app.sh
```

* Mở GUI Streamlit tại `http://localhost:8501`.

---

## 📝 Quy trình dữ liệu (ETL)

```
[Source JSON] -> extract.py/sh -> transform.py/sh -> load.py/sh -> DB nguồn
DB nguồn -> _total_load.py -> total_news.db
```

* Mỗi nguồn: nqs, ktck, vne, vst, tbkt, vnfi.
* Pipeline Airflow DAG `update_all` chạy song song tất cả nguồn và gom vào node join, sau đó tổng hợp.
* GUI đọc từ `total_news.db`.

---

## 🖼️ GUI Streamlit

* Hiển thị tin mới nhất trước.
* Filter: Category (từ bảng `channels`), keyword, Read/Favorite.
* Load more: 100 tin một lần, append liền dưới.
* Checkbox Read/Favorite lưu trạng thái vào DB.
* Link Title mở tab mới.

---

## 🧰 Lưu ý

* Vận hành toàn bộ chỉ cần 3 script ngoài: `setup.sh`, `run_app.sh`, `update_all.sh`.
* Không cần thao tác trực tiếp file trong `etl/`, `airflow/`, `gui/`.
* Có thể mở rộng multi-user bằng thêm `user_id` trong bảng trạng thái.
* Hệ thống modular, dễ thêm nguồn tin mới.

---

## 📦 Yêu cầu

* Python >=3.10
* streamlit, pandas, airflow, sqlite3 (builtin)
* Hệ thống Linux/macOS hoặc WSL cho script Bash
