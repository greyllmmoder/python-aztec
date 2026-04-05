#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backward-compatible import shim for the legacy module path."""

from aztec_py.core import *  # noqa: F401,F403
from aztec_py.core import main


if __name__ == '__main__':
    import sys

    main(sys.argv)
