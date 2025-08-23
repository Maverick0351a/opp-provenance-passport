"""Airflow DAG example demonstrating OPP @stamp usage.

Prerequisites (not installed automatically):
  pip install apache-airflow

Set a trace id (optional):
  export OPP_TRACE_ID=my-trace   # *nix
  set OPP_TRACE_ID=my-trace      # Windows CMD
  $env:OPP_TRACE_ID='my-trace'   # PowerShell

Initialize Airflow (one-time):
  airflow db init
  airflow users create --username admin --password admin --firstname a --lastname b --role Admin --email a@b.c

Run the scheduler & webserver in separate shells, then place this file in your DAGS_FOLDER or symlink it.
"""
from __future__ import annotations
import os

try:
    from datetime import datetime
    from airflow import DAG  # type: ignore
    from airflow.operators.python import PythonOperator  # type: ignore
except ImportError:  # pragma: no cover
    if __name__ == "__main__":
        print("Airflow not installed. Install apache-airflow to run this example.")
    raise

from opp.decorators import stamp

TRACE_ID = os.getenv("OPP_TRACE_ID", "airflow-trace")

@stamp(
    "extract.v1",
    inputs=lambda a, kw: {"phase": "none"},
    outputs=lambda rv: {"keys": list(rv.keys())},
)
def extract():
    # Simulate extraction
    return {"records": [1, 2, 3]}

@stamp(
    "transform.v1",
    inputs=lambda a, kw: {"upstream": "extract"},
    outputs=lambda rv: {"size": len(rv.get("records", []))},
)
def transform(ti=None):  # Airflow passes TaskInstance via context
    data = ti.xcom_pull(task_ids="extract_task")
    data["sum"] = sum(data["records"])  # simple aggregation
    return data

@stamp("load.v1", inputs=lambda a, kw: {"source": "transform"})
def load(ti=None):
    final = ti.xcom_pull(task_ids="transform_task")
    # Pretend to load somewhere; just return success metadata
    return {"loaded": True, "count": len(final["records"])}

with DAG(
    dag_id="opp_example_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["opp", TRACE_ID],
) as dag:
    t_extract = PythonOperator(task_id="extract_task", python_callable=extract)
    t_transform = PythonOperator(task_id="transform_task", python_callable=transform)
    t_load = PythonOperator(task_id="load_task", python_callable=load)

    t_extract >> t_transform >> t_load
