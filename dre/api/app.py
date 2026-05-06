from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError

from dre.governance.errors import RunIdCollisionError
from dre.governance.sqlite_store import SqliteGovernanceStore
from dre.orchestrator.engine import DrePipeline


def create_app(*, governance_db_path: Path) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        gov = SqliteGovernanceStore(governance_db_path)
        app.state.gov = gov
        app.state.pipeline = DrePipeline(gov)
        yield
        gov.close()

    app = FastAPI(
        title="Decision Resilience Engine API",
        version="0.2.0",
        lifespan=lifespan,
    )

    class RunSimulateBody(BaseModel):
        run_id: str = Field(..., pattern=r"^opt_\d{8}_\d{6}_v5\.0$")
        data_hash: str
        rng_seed: int = 42
        variant: str = Field(default="standard", pattern=r"^(standard|intervention)$")

    @app.get("/dre/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "dre"}

    @app.post("/dre/simulate")
    async def simulate(request: Request) -> dict:
        pipe: DrePipeline = app.state.pipeline
        try:
            raw = await request.json()
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=422, detail="invalid_json") from exc
        try:
            body = RunSimulateBody.model_validate(raw)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
        try:
            if body.variant == "standard":
                ctx = pipe.simulate_standard_success(
                    body.run_id,
                    body.data_hash,
                    rng_seed=body.rng_seed,
                )
            else:
                ctx = pipe.simulate_intervention_success(
                    body.run_id,
                    body.data_hash,
                    rng_seed=body.rng_seed,
                )
        except RunIdCollisionError as exc:
            raise HTTPException(status_code=409, detail=exc.as_json()) from exc
        return ctx.model_dump(mode="json")

    return app
