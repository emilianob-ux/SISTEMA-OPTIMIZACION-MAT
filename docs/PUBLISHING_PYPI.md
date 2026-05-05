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

Podés configurar **OpenID Connect** entre GitHub y PyPI para que un workflow en Actions publique al crear un Release. Requiere:

- Crear el proyecto en PyPI (nombre disponible).
- En PyPI: **Manage → Publishing** → añadir “trusted publisher” con este repositorio y el workflow que uses.

Documentación oficial: [Publishing via Trusted Publishers](https://docs.pypi.org/trusted-publishers/).

No incluimos aquí un workflow fijo porque fallaría hasta que completes ese registro en PyPI; cuando lo tengas, podés copiar el ejemplo de [`pypa/gh-action-pypi-publish`](https://github.com/pypa/gh-action-pypi-publish).
