"""Entry point. Run one stage at a time or all of them in order.

    MPLBACKEND=Agg python main.py [step1|step2|aggregate|q1|q2|q3|q4|all]

Each stage prints to the console and to outputs/logs/<stage>.log (evidence for 05_analysis.md).
"""
import importlib
import sys

from pipeline.logutil import tee_log

STAGES = {"step1": "pipeline.run_step1", "step2": "pipeline.run_step2", "aggregate": "pipeline.run_aggregate",
          "q1": "pipeline.run_q1", "q2": "pipeline.run_q2", "q3": "pipeline.run_q3", "q4": "pipeline.run_q4"}


def run(stage):
    with tee_log(stage):
        importlib.import_module(STAGES[stage]).main()


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    for st in (STAGES if arg == "all" else [arg]):
        run(st)
