# Publicar en PyPI (`decision-resilience-engine`)

El workflow [.github/workflows/publish-pypi.yml](../.github/workflows/publish-pypi.yml) sube **wheel + sdist** con **OIDC Trusted Publisher** (sin guardar contraseñas de PyPI en GitHub).

## Checklist — dejar todo listo (orden recomendado)

### 1. PyPI — Trusted Publisher (una sola vez)

1. Entrá en [pypi.org](https://pypi.org/) → tu cuenta → **Publishing**.
2. **Add a new pending publisher**.
3. Completá exactamente:

   | Campo | Valor |
   | --- | --- |
   | **PyPI Project name** | `decision-resilience-engine` (igual que `name` en `pyproject.toml`) |
   | **Owner** | `emilianob-ux` |
   | **Repository name** | `decision-resilience-engine` |
   | **Workflow name** | `publish-pypi.yml` |
   | **Environment name** | `pypi` |

4. Guardá. PyPI mostrará el proyecto **pendiente** hasta la **primera subida exitosa** (es normal que la URL del proyecto dé 404 hasta entonces).

### 2. GitHub — environment `pypi` (una sola vez)

1. En el repo: **Settings → Environments → New environment**.
2. **Name:** `pypi` (debe coincidir con PyPI y con el workflow).
3. Opcional: activá **Required reviewers** o **deployment branches** si querés aprobar cada publicación a mano.

Sin este environment, el job de publicación **no obtiene OIDC** y PyPI rechazará la subida.

### 3. Versión en `pyproject.toml`

La versión que se publica es **`[project].version`** en `pyproject.toml` (hoy **0.3.0**).  
Antes de etiquetar: si cambiás código relevante para usuarios, incrementá versión (semver) y actualizá `CHANGELOG.md`.

### 4. Tag + Release (dispara el workflow)

El workflow comprueba que el **nombre del tag del release** coincida con esa versión:

- Tag **`v0.3.0`** → debe existir `version = "0.3.0"` en `pyproject.toml`.
- Si no coinciden, el job falla con un mensaje explícito.

Pasos:

1. Commits en `main` con la versión deseada en `pyproject.toml`.
2. Creá un tag anotado localmente o desde GitHub: `vX.Y.Z` (con **`v`**).
3. **GitHub → Releases → Draft a new release** → elegí el tag → **Publish release**.

El evento `release: published` ejecuta **Publish to PyPI**.

### 5. Alternativa: ejecución manual

**Actions → Publish to PyPI → Run workflow**

- **git_ref** por defecto: `main` (podés poner un tag existente, ej. `v0.3.0`).
- No corre la verificación tag ↔ `pyproject` (solo aplica a releases).
- Útil para recuperar una publicación fallida si ya tenés tag correcto.

### 6. Tras publicar OK

1. Abrí [pypi.org/project/decision-resilience-engine](https://pypi.org/project/decision-resilience-engine/) y verificá la versión.
2. Local: `pip install decision-resilience-engine==X.Y.Z`.
3. README (opcional): podés sumar el badge de versión estable:

   ```markdown
   [![PyPI version](https://img.shields.io/pypi/v/decision-resilience-engine.svg)](https://pypi.org/project/decision-resilience-engine/)
   ```

   Podés dejar también el badge **legacy** [`sistema-optimizacion-mat`](https://pypi.org/project/sistema-optimizacion-mat/) mientras quieras indicar el nombre anterior.

## Migración desde `sistema-optimizacion-mat`

El proyecto **sigue visible** como [`sistema-optimizacion-mat`](https://pypi.org/project/sistema-optimizacion-mat/). PyPI **no renombra** proyectos: el índice nuevo es **`decision-resilience-engine`**.

Podés archivar el proyecto viejo o subir una última versión con README que redirija al nombre nuevo.

## Verificación local (misma lógica que CI)

```bash
pip install build twine
python -m build
twine check --strict dist/*
```

## Problemas frecuentes

| Síntoma | Qué revisar |
| --- | --- |
| **Permission denied** / OIDC en PyPI | Trusted Publisher: owner/repo/workflow/environment deben coincidir **exactamente** con este repo (`pypi`). |
| **404** al publicar | El proyecto pendiente en PyPI debe llamarse `decision-resilience-engine`. |
| Falla **Coincidencia tag ↔ pyproject** | El release debe usar tag `v` + misma versión que `pyproject.toml` (ej. `v0.3.0` y `0.3.0`). |
| **File already exists** | En PyPI no se puede sobrescribir una versión; subí `X.Y.Z` nueva en `pyproject.toml` + tag nuevo. |

## Referencias

- [Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
