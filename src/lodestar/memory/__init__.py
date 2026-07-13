"""Durable memory stores.

These persist across runs as **committed** files under `state/` — not a
gitignored database. In a fresh-checkout CI runner, git is the only thing that
survives between days, which is exactly the design's "git is the durable store."
Plain text / JSON keeps them diffable and auditable.
"""
