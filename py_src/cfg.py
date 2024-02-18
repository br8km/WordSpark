#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Config."""

from pathlib import Path


class Config:
    """Config."""

    time_zone = "America/New_York"

    # dir_src = Project_root/py_src/
    dir_src = Path(__file__).parent
    dir_root = dir_src.parent.parent

    dir_data = dir_root / "data"
    dir_docs = dir_root / "docs"
    dir_dummy = dir_root / "dummy"

    dir_cache = dir_dummy / "cache"
    dir_debug = dir_dummy / "debug"
    dir_log = dir_dummy / "log"
    dir_test = dir_dummy / "test"
