"""Pure domain: citation extraction and verification.

This package has **no** dependency on the database, FastAPI, or the worker.
It operates on plain dataclasses so it can be unit-tested in isolation and the
verification logic can be reasoned about independently of persistence.
"""
