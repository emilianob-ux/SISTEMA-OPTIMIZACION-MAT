#!/usr/bin/env python3
"""Servidor HTTP de desarrollo para la API DRE."""

from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from dre.api.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Decision Resilience Engine — API dev")
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/dre_governance.sqlite"),
        help="Ruta SQLite governance (append-only MVP)",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    args.db.parent.mkdir(parents=True, exist_ok=True)
    app = create_app(governance_db_path=args.db)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
