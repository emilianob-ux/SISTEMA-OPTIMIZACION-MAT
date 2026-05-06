from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

from dre.governance.errors import RunIdCollisionError

WriteRunStatus = Literal["inserted", "already_existed"]


class SqliteGovernanceStore:
    """Ledger append-only MVP (SQLite). Un registro lógico por `run_id` + bitácora de eventos."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self._conn.close()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS dre_run_registry (
              run_id TEXT PRIMARY KEY,
              data_hash TEXT NOT NULL,
              meta_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS dre_audit_log (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id TEXT NOT NULL,
              event_type TEXT NOT NULL,
              state_before TEXT,
              state_after TEXT,
              payload_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS dre_checkpoints (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id TEXT NOT NULL,
              state TEXT NOT NULL,
              context_json TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def write_run(self, run_id: str, data_hash: str, meta: dict[str, Any]) -> WriteRunStatus:
        row = self._conn.execute(
            "SELECT data_hash FROM dre_run_registry WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        now = datetime.now(timezone.utc).isoformat()
        if row is None:
            self._conn.execute(
                "INSERT INTO dre_run_registry (run_id, data_hash, meta_json, created_at) "
                "VALUES (?, ?, ?, ?)",
                (run_id, data_hash, json.dumps(meta, separators=(",", ":"), sort_keys=True), now),
            )
            self._conn.commit()
            return "inserted"
        existing_hash = row["data_hash"]
        if existing_hash != data_hash:
            raise RunIdCollisionError(run_id, existing_hash, data_hash)
        return "already_existed"

    def append_audit(
        self,
        run_id: str,
        event_type: str,
        *,
        state_before: Optional[str] = None,
        state_after: Optional[str] = None,
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO dre_audit_log (run_id, event_type, state_before, state_after, "
            "payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                run_id,
                event_type,
                state_before,
                state_after,
                json.dumps(payload or {}, separators=(",", ":"), sort_keys=True),
                now,
            ),
        )
        self._conn.commit()

    def save_checkpoint(self, run_id: str, state: str, context: dict[str, Any]) -> int:
        now = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            "INSERT INTO dre_checkpoints (run_id, state, context_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (run_id, state, json.dumps(context, separators=(",", ":"), sort_keys=True), now),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def load_latest_checkpoint(self, run_id: str) -> Optional[dict[str, Any]]:
        row = self._conn.execute(
            "SELECT id, state, context_json, created_at FROM dre_checkpoints "
            "WHERE run_id = ? ORDER BY id DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "id": int(row["id"]),
            "state": row["state"],
            "context": json.loads(row["context_json"]),
            "created_at": row["created_at"],
        }

    def audit_event_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS c FROM dre_audit_log").fetchone()
        return int(row["c"])
