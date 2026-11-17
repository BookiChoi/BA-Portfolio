"""Tiny helper so every stage writes its printed output to outputs/logs/<stage>.log.

Why: the plan requires, for every number, the script path plus the log that printed it.
"""
import contextlib
import sys

from . import config as C


class _Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)
        return len(s)

    def flush(self):
        for st in self.streams:
            st.flush()


@contextlib.contextmanager
def tee_log(stage: str):
    C.LOGS.mkdir(parents=True, exist_ok=True)
    with open(C.LOGS / f"{stage}.log", "w") as f:
        old = sys.stdout
        sys.stdout = _Tee(old, f)
        try:
            yield
        finally:
            sys.stdout = old
