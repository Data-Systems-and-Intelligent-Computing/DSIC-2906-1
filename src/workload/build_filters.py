"""Represent natural metadata predicates in an auditable form."""
from __future__ import annotations


def equals(field: str, value):
    return lambda row: row.get(field) == value


def all_of(*predicates):
    return lambda row: all(p(row) for p in predicates)
