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

El paquete anterior en PyPI **no se renombra solo**. Este repo usa el nombre nuevo `decision-resilience-engine`. Podés dejar el proyecto viejo como archivo o publicar una última versión con README que redirija al nuevo nombre.

## Referencias

- [Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
