"""Lodestar — a daily tech-intelligence digest with a tiered, event-sourced memory.

Phase 0 (this milestone) is a deliberately thin end-to-end slice: one source
(Hacker News) → a minimal digest → written to disk, ready to be committed by a
scheduled GitHub Action. Everything else (the LangGraph pipeline, more sources,
dedup, the verifier/judge loop, the memory subsystem) lands in later phases.
"""

__version__ = "0.0.1"
