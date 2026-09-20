# Preguntas frecuentes

Preguntas habituales sobre construir, instalar y probar la librería de Python.
Cada respuesta enlaza a la página donde el tema se trata en detalle.

??? question "¿Cuál es la diferencia entre un módulo, un paquete y una librería?"
    Un **módulo** es un único archivo `.py`; un **paquete** es una carpeta de
    módulos importada como una unidad, normalmente marcada por un `__init__.py`;
    una **librería** es un paquete pensado para ser reutilizado por otro código.
    Una **distribución** es el paquete instalable que
    `pip` descarga. Véase
    [Qué es una librería](library.md#modulo-paquete-libreria-distribucion).

??? question "¿Necesito `setup.py`? ¿Qué es `pyproject.toml`?"
    No — `pyproject.toml` es el reemplazo moderno y estandarizado de `setup.py`.
    Contiene los metadatos del proyecto, las dependencias y la configuración de
    construcción en un solo archivo. Véase
    [Organización § pyproject.toml](organization.md#pyprojecttoml).

??? question "¿Por qué el código está bajo `src/` en lugar de en la raíz del repositorio?"
    Para que el paquete no sea importable *por accidente* desde la raíz del
    proyecto. La estructura `src/` te obliga a instalar el paquete antes de
    importarlo, de modo que tus pruebas se ejecutan contra la librería instalada
    exactamente como la obtendría un usuario. Véase
    [Organización § src](organization.md#the-src-layout).

??? question "¿Cuál es la diferencia entre `requirements.txt` y `pyproject.toml`?"
    `pyproject.toml` declara lo que la *librería* necesita como parte de su
    identidad — la fuente de verdad cuando alguien la instala. `requirements.txt`
    es una lista de conveniencia para fijar un *entorno* reproducible. Esta
    librería está basada en reglas, así que no tiene dependencias de ejecución y
    `requirements.txt` está esencialmente vacío. Véase
    [Organización § requirements.txt](organization.md#requirementstxt).

??? question "¿Qué hace `__init__.py`?"
    Marca un directorio como **paquete regular** y define qué expone el paquete al
    importarse. (Desde Python 3.3 una carpeta sin él sigue siendo importable, como
    *paquete de espacio de nombres*, pero una librería debe ser explícita.) Aquí
    declara la versión y, a medida que la librería crezca, es donde se reexportan
    las clases públicas. Véase
    [Organización § __init__.py](organization.md#__init__py).

??? question "¿Cómo instalo la librería en un notebook de Google Colab?"
    Instálala directamente desde GitHub en una celda, luego impórtala:

    ```python
    !pip install git+https://github.com/jparisu/nim-arena.git
    import nimarena
    ```

    Véase [Instalación y uso](installation-and-usage.md#usarlo-en-un-notebook).

??? question "¿Qué significa `pip install -e \".[dev]\"`?"
    `-e` instala el paquete en modo **editable** (un enlace a tu código fuente, de
    modo que las ediciones surten efecto de inmediato), y `.[dev]` instala además
    el extra `dev` (`pytest`, `ruff`, `mypy`). Es la configuración estándar para
    *desarrollar* la
    librería. Véase
    [Instalación y uso § Instalar en local](installation-and-usage.md#instalar-en-local).

??? question "Instalé una nueva versión en un notebook pero nada cambió. ¿Por qué?"
    Python cachea los módulos importados durante la sesión. Tras instalar una nueva
    versión, **reinicia el entorno de ejecución** (Runtime → Restart) para que se
    cargue el código nuevo. Véase
    [Instalación y uso](installation-and-usage.md#usarlo-en-un-notebook).

??? question "¿Para qué sirve `__all__`?"
    Nombra los objetos **públicos** de un módulo: documenta la API prevista y
    controla qué trae `from nimarena import *`. Los nombres fuera de ella (y los
    que empiezan por `_`) se tratan como privados. Véase
    [API § Qué es aquí una API](api.md#que-es-aqui-una-api).

??? question "¿Por qué la interfaz de jugador es una clase base abstracta?"
    Porque `@abstractmethod` hace que Python se niegue a instanciar una
    implementación incompleta, con el nombre del método que falta en el error. El
    fallo se caza en la construcción y no en mitad de un torneo. Véase
    [API § Diseñar una API que otros implementan](api.md#disenar-una-api-que-otros-implementan).

??? question "¿Por qué hay un archivo de manifiesto en vez de escanear la carpeta de jugadores?"
    Porque escanear ejecutaría el código de nivel superior de un desconocido solo
    para descubrirlo, y ocultaría qué se está admitiendo. Un manifiesto pone el
    archivo nuevo y la única línea que lo admite en el mismo diff, de modo que la
    decisión de confianza es visible en la revisión. Véase
    [API § Diseñar una API que otros implementan](api.md#disenar-una-api-que-otros-implementan).

??? question "¿Cómo ejecuto las pruebas?"
    Instala el extra `dev` y ejecuta pytest:

    ```bash
    pip install -e ".[dev]"
    pytest
    ```

    pytest descubre automáticamente los archivos llamados `test_*.py` y las
    funciones llamadas `test_*`. Véase
    [Pruebas](testing.md#escribir-y-ejecutar-pruebas-con-pytest).

??? question "¿Se ejecutan las pruebas automáticamente?"
    Sí. El workflow `tests.yml` de GitHub Actions ejecuta `ruff`, `mypy` y
    `pytest` en tres versiones de Python en cada push y
    pull request, y la protección de ramas puede hacer que pasar las pruebas sea
    **obligatorio** antes de una fusión. Véase
    [Pruebas § Pruebas en integración continua](testing.md#pruebas-en-integracion-continua).

??? question "¿Qué es `py.typed`?"
    Un archivo marcador vacío junto a `__init__.py`. Sin él, los comprobadores de
    tipos ignoran tus anotaciones cuando otra persona importa tu paquete. Véase
    [Organización § py.typed](organization.md#pytyped).
