# Publicar en PyPI (`decision-resilience-engine`)

El workflow [Publish to PyPI](../.github/workflows/publish-pypi.yml) sube **wheel + sdist** usando **OIDC Trusted Publisher** (sin contraseña en GitHub).

## 1. Crear el proyecto en PyPI

1. Entrá en [PyPI](https://pypi.org/) → tu cuenta → **Publishing**.
2. **Add a new pending publisher** (Trusted Publisher).
3. **PyPI Project name:** `decision-resilience-engine` (debe coincidir con `name` en `pyproject.toml`).
4. **Owner:** `emilianob-ux`
5. **Repository name:** `decision-resilience-engine`
6. **Workflow name:** `publish-pypi.yml`
7. **Environment name:** `pypi`

Guardá. PyPI mostrará el proyecto pendiente hasta la **primera publicación exitosa**.

## 2. Environment `pypi` en GitHub

En el repo: **Settings → Environments → New environment → name:** `pypi`.

Recomendado: proteger el environment (solo vos como revisor) si querés confirmación manual antes de cada deploy.

## 3. Disparar la publicación

- **Opción A:** Publicá un [GitHub Release](https://github.com/emilianob-ux/decision-resilience-engine/releases) asociado al tag (por ejemplo `v0.3.0`). El evento `release: published` ejecuta el workflow.
- **Opción B:** **Actions → Publish to PyPI → Run workflow**, elegí ref `main` o tag `v0.3.0`.

## 4. Migración desde `sistema-optimizacion-mat`

El proyecto **sigue visible en PyPI** como [`sistema-optimizacion-mat`](https://pypi.org/project/sistema-optimizacion-mat/). PyPI **no renombra** un proyecto existente: por eso el badge que apunta a [`decision-resilience-engine`](https://pypi.org/project/decision-resilience-engine/) falla hasta la **primera publicación** bajo el nombre nuevo.

Este repo ya usa `name = "decision-resilience-engine"` en `pyproject.toml`. Podés dejar el proyecto viejo como archivo o publicar una última versión con README que redirija al nuevo nombre.

## Referencias

- [Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
