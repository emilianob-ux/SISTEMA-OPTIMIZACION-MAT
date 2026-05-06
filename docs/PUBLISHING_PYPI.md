# Publicar en PyPI (opcional)

El paquete se llama **`sistema-optimizacion-mat`** según `pyproject.toml`. Publicarlo en [PyPI](https://pypi.org) ayuda a que otros lo encuentren con `pip install`, pero **no es obligatorio** para usar el repo desde GitHub.

## Antes de publicar

1. Cuenta en [pypi.org](https://pypi.org) (y en [test.pypi.org](https://test.pypi.org) para una prueba seca).
2. Confirmá que `README.md`, licencia y versión en `pyproject.toml` reflejan lo que querés mostrar.
3. No subas secretos ni bases de datos grandes (`.gitignore` ya protege lo habitual).

## Prueba en TestPyPI

Desde la raíz del repo, con Python 3.11+:

```bash
python -m pip install --upgrade build twine
python -m build
twine upload --repository testpypi dist/*
```

Instalación de prueba:

```bash
pip install --index-url https://test.pypi.org/simple/ sistema-optimizacion-mat
```

## Publicación en PyPI (producción)

```bash
twine upload dist/*
```

Usá tokens de API en lugar de contraseña ([crear token](https://pypi.org/manage/account/token/)).

## Trusted publishing (GitHub → PyPI, sin token en el repo)

El repo incluye el workflow [`.github/workflows/publish-pypi.yml`](https://github.com/emilianob-ux/SISTEMA-OPTIMIZACION-MAT/blob/main/.github/workflows/publish-pypi.yml): se ejecuta cuando publicás un **Release** en GitHub y sube el artefacto construido con `python -m build`. También podés lanzarlo a mano: **Actions → Publish to PyPI → Run workflow** (parámetro `git_ref`, por defecto `main`; para un tag existente usá `v0.1.3`, etc.).

**Límite de PyPI:** registrar el *trusted publisher* solo se puede desde la **cuenta web de PyPI** (no hay API pública para eso). Copiá los valores tal cual abajo.

### Pasos en PyPI

1. Abrí [**Publishing settings en tu cuenta PyPI**](https://pypi.org/manage/account/publishing/) e iniciá sesión.
2. **Add a new pending publisher** y completá:
   - **PyPI Project Name:** `sistema-optimizacion-mat`
   - **Owner:** `emilianob-ux`
   - **Repository name:** `SISTEMA-OPTIMIZACION-MAT`
   - **Workflow name:** `publish-pypi.yml`
   - **Environment name:** `pypi` (debe coincidir con el `environment:` del YAML).

### Pasos en GitHub

1. **Settings → Environments**: debe existir el entorno **`pypi`** (sin reglas de aprobación alcanza para empezar). Si no está, crealo ahí o actualizalo con la API:  
   `gh api -X PUT repos/emilianob-ux/SISTEMA-OPTIMIZACION-MAT/environments/pypi --input "{\"wait_timer\":0}"`  
   (en PowerShell conviene usar un archivo JSON sin BOM como `--input path\to\body.json`).
2. Publicá un **Release** en GitHub **o** ejecutá el workflow manualmente con el **`git_ref`** deseado; el job usa [`pypa/gh-action-pypi-publish`](https://github.com/pypa/gh-action-pypi-publish).

Documentación oficial: [Publishing via Trusted Publishers](https://docs.pypi.org/trusted-publishers/).

Hasta que el publisher no esté registrado en PyPI, el job fallará en el paso de publicación (es esperado).
