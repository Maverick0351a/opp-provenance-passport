"""Dagster job example demonstrating OPP @stamp usage.

Prerequisites:
  pip install dagster dagit

Run UI:
  dagster dev -f examples/dagster_job.py
"""
from __future__ import annotations
import os
from opp.decorators import stamp

try:
    from dagster import op, job  # type: ignore
except ImportError:  # pragma: no cover
    if __name__ == "__main__":
        print("Dagster not installed. Install dagster to run this example.")
    raise

TRACE_ID = os.getenv("OPP_TRACE_ID", "dagster-trace")

@op
@stamp("extract.v1", outputs=lambda rv: {"count": len(rv)})
def extract():
    return [1, 2, 3]

@op
@stamp("transform.v1", inputs=lambda a, kw: {"prev": "extract"}, outputs=lambda rv: {"sum": sum(rv)})
def transform(records: list[int]):
    return [r * 2 for r in records]

@op
@stamp("load.v1", inputs=lambda a, kw: {"stage": "transform"})
def load(data: list[int]):
    # pretend to load
    return {"loaded": True, "size": len(data)}

@job
def opp_example_job():
    load(transform(extract()))

if __name__ == "__main__":  # run an ad-hoc execution
    from dagster import execute_job
    result = execute_job(opp_example_job)
    print("Result success:", result.success)
