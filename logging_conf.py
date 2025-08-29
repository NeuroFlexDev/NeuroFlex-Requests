import logging
import sys

def setup_logging():
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter(fmt))
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)
    root.addHandler(h)
