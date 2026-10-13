#!/usr/bin/env python3
"""TITAN PRO V80 entry point.

Usage:
  python run_titan.py              # start HTTP server (default 127.0.0.1:8080)
  python run_titan.py --self-test  # run internal self-tests and exit
"""
from titan.runtime import load

if __name__ == "__main__":
    load(__file__, as_main=True)
