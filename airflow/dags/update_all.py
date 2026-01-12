from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
import os

# --- Đường dẫn gốc dự án ---
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ETL_DIR = os.path.join(PROJECT_DIR, "etl")

# --- DAG definition ---
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
}

dag = DAG(
    dag_id="update_all",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="*/30 * * * *",  # Chạy thủ công
    catchup=False,
)  

# --- Điểm start chung ---
start = DummyOperator(
    task_id="start",
    dag=dag
)

# --- Task 1 ---
nqs_extract = BashOperator(
    task_id="nqs_extract",
    bash_command=f'bash "{os.path.join(ETL_DIR, "nqs_extract.sh")}"',
    dag=dag
)

# --- Task 2 ---
nqs_transform = BashOperator(
    task_id="nqs_transform",
    bash_command=f'bash "{os.path.join(ETL_DIR, "nqs_transform.sh")}"',
    dag=dag
)

# --- Task 3 ---
nqs_load = BashOperator(
    task_id="nqs_load",
    bash_command=f'bash "{os.path.join(ETL_DIR, "nqs_load.sh")}"',
    dag=dag
)

# --- Task 3 ---
ktck_extract = BashOperator(
    task_id="ktck_extract",
    bash_command=f'bash "{os.path.join(ETL_DIR, "ktck_extract.sh")}"',
    dag=dag
)

# --- Task 4 ---
ktck_transform = BashOperator(
    task_id="ktck_transform",
    bash_command=f'bash "{os.path.join(ETL_DIR, "ktck_transform.sh")}"',
    dag=dag
)

# --- Task 5 ---
ktck_load = BashOperator(
    task_id="ktck_load",
    bash_command=f'bash "{os.path.join(ETL_DIR, "ktck_load.sh")}"',
    dag=dag
)

# --- Task 6 ---
vne_extract = BashOperator(
    task_id="vne_extract",
    bash_command=f'bash "{os.path.join(ETL_DIR, "vne_extract.sh")}"',
    dag=dag
)

# --- Task 7 ---
vne_transform = BashOperator(
    task_id="vne_transform",
    bash_command=f'bash "{os.path.join(ETL_DIR, "vne_transform.sh")}"',
    dag=dag
)

# --- Task 8 ---
vne_load = BashOperator(
    task_id="vne_load",
    bash_command=f'bash "{os.path.join(ETL_DIR, "vne_load.sh")}"',
    dag=dag
)

# --- Task 9 ---
vst_extract = BashOperator(
    task_id="vst_extract",
    bash_command=f'bash "{os.path.join(ETL_DIR, "vst_extract.sh")}"',
    dag=dag
)

# --- Task 10 ---
vst_transform = BashOperator(
    task_id="vst_transform",
    bash_command=f'bash "{os.path.join(ETL_DIR, "vst_transform.sh")}"',
    dag=dag
)

# --- Task 11 ---
vst_load = BashOperator(
    task_id="vst_load",
    bash_command=f'bash "{os.path.join(ETL_DIR, "vst_load.sh")}"',
    dag=dag
)

# --- Task 12 ---
tbkt_extract = BashOperator(
    task_id="tbkt_extract",
    bash_command=f'bash "{os.path.join(ETL_DIR, "tbkt_extract.sh")}"',
    dag=dag
)

# --- Task 13 ---
tbkt_transform = BashOperator(
    task_id="tbkt_transform",
    bash_command=f'bash "{os.path.join(ETL_DIR, "tbkt_transform.sh")}"',
    dag=dag
)

# --- Task 14 ---
tbkt_load = BashOperator(
    task_id="tbkt_load",
    bash_command=f'bash "{os.path.join(ETL_DIR, "tbkt_load.sh")}"',
    dag=dag
)

# --- Task 15 ---
vnfi_extract = BashOperator(
    task_id="vnfi_extract",
    bash_command=f'bash "{os.path.join(ETL_DIR, "vnfi_extract.sh")}"',
    dag=dag
)

# --- Task 16 ---
vnfi_transform = BashOperator(
    task_id="vnfi_transform",
    bash_command=f'bash "{os.path.join(ETL_DIR, "vnfi_transform.sh")}"',
    dag=dag
)

# --- Task 17 ---
vnfi_load = BashOperator(
    task_id="vnfi_load",
    bash_command=f'bash "{os.path.join(ETL_DIR, "vnfi_load.sh")}"',
    dag=dag
)

# Join
join_all = DummyOperator(
    task_id="join_all",
    dag=dag
)

# --- Task 18 ---
_total_load = BashOperator(
    task_id="_total_load",
    bash_command=f'bash "{os.path.join(ETL_DIR, "_total_load.sh")}"',
    dag=dag
)

# --- Thiết lập thứ tự chạy ---
start >> [nqs_extract, ktck_extract, vne_extract, vst_extract, tbkt_extract, vnfi_extract]
nqs_extract >> nqs_transform >> nqs_load
ktck_extract >> ktck_transform >> ktck_load
vne_extract >> vne_transform >> vne_load
vst_extract >> vst_transform >> vst_load
tbkt_extract >> tbkt_transform >> tbkt_load
vnfi_extract >> vnfi_transform >> vnfi_load
[nqs_load, ktck_load, vne_load, vst_load, tbkt_load, vnfi_load] >> join_all >> _total_load
