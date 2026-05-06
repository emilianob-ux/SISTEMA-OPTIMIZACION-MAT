# Decision Resilience Engine — código de referencia (contratos ICD)

Este paquete contiene **únicamente** los modelos Pydantic descritos en [docs/pdr/02_Interface_Contracts_ICD.md](../docs/pdr/02_Interface_Contracts_ICD.md). Sirven para:

- Verificación automática en CI (`tests/test_dre_contracts.py`).
- Arranque de un futuro servicio FastAPI / orquestador sin acoplarse al runner MAT.

No incluye Redis, FSM completa ni skills (`ProbabilisticForecasting`, etc.): esa implementación sigue la especificación en [docs/DRE_TECHNICAL_ARCHITECTURE.md](../docs/DRE_TECHNICAL_ARCHITECTURE.md).
