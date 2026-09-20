# Deshacer cambios

Tarde o temprano querrás **volver atrás**: descartar una edición, quitar un
archivo de la preparación, o apartar tu trabajo para atender algo urgente. Git
tiene un comando para cada caso. Esta página cubre los tres que realmente
necesitas —`restore`, `reset` y `stash`— y una guía para elegir el correcto.

!!! warning "Algunos de estos tiran trabajo a la basura"
    Descartar cambios en el directorio de trabajo (`git restore <archivo>`,
    `git reset --hard`) **borra permanentemente** esos cambios: nunca se
    confirmaron, así que Git no puede recuperarlos. Ante la duda, prefiere
    `git stash`, que aparta el trabajo sin destruirlo.

## `git restore` — descartar cambios en el directorio de trabajo

Usa `restore` para tirar ediciones que **no has confirmado** y volver a la última
versión confirmada de un archivo.

```console
$ git status
Changes not staged for commit:
        modified:   README.md

$ git restore README.md
$ git status
On branch main
nothing to commit, working tree clean
```

`restore` también **quita de la preparación** un archivo (lo saca del área de
preparación, pero conserva tus ediciones) con la opción `--staged`:

```console
$ git restore --staged README.md   # quita de preparación, conserva los cambios
```

- `git restore <archivo>` → descarta ediciones sin confirmar de ese archivo.
- `git restore --staged <archivo>` → quita de preparación, pero conserva las
  ediciones.

## `git reset` — mover el puntero de la rama

`reset` opera sobre **commits y preparación**, no sobre ediciones de archivos
individuales. Su uso más común en el día a día es el sentido inverso de `add`:
quitar de la preparación.

```console
$ git add README.md
$ git reset README.md      # quita README.md de preparación (equivale a restore --staged)
```

Usado con un commit, `reset` **mueve el puntero de la rama actual** a un commit
anterior — eliminando en la práctica de la rama los commits posteriores. Lo que
ocurre con los cambios de esos commits depende del modo:

| Modo | Puntero de la rama | Área de preparación | Directorio de trabajo |
| --- | --- | --- | --- |
| `--soft` | retrocede | se conserva | se conserva |
| `--mixed` *(por defecto)* | retrocede | se reinicia | se conserva |
| `--hard` | retrocede | se reinicia | **se descarta** |

- `git reset --soft HEAD~1` — deshace el **último commit** pero conserva sus
  cambios preparados, listos para volver a confirmar (ideal para arreglar un
  mensaje de commit o dividir un commit).
- `git reset --mixed HEAD~1` — deshace el último commit y quita sus cambios de la
  preparación, pero los mantiene en tus archivos.
- `git reset --hard HEAD~1` — deshace el último commit **y tira sus cambios a la
  basura**. Rápido, e irreversible.

Aquí `HEAD~1` significa "un commit antes del actual".

!!! danger "`--hard` e historial compartido"
    Nunca hagas `reset` de commits que ya has **subido y compartido** con otros:
    reescribes un historial que ellos ya tienen, y su próximo `pull` entrará en
    conflicto. En ramas compartidas, deshaz un commit con `git revert` (que
    registra un *nuevo* commit que deshace uno antiguo) en su lugar.

## `git stash` — apartar cambios

A veces estás en mitad de algo y necesitas un directorio de trabajo limpio ahora
mismo — para hacer pull, para cambiar de rama, o para probar un arreglo rápido.
`stash` guarda tus cambios sin confirmar de forma segura y te devuelve un árbol
limpio.

```console
$ git stash
Saved working directory and index state WIP on main: 92c1041 Add project skeleton

$ git status
On branch main
nothing to commit, working tree clean
```

Tus cambios no se pierden — están en una pila. Recupéralos cuando estés listo:

```console
$ git stash pop      # reaplica el stash más reciente y lo quita de la pila
```

- `git stash` → guarda los cambios y limpia el directorio de trabajo.
- `git stash list` → ve qué has guardado en el stash.
- `git stash pop` → reaplica el último stash y lo elimina.
- `git stash drop` → descarta un stash sin aplicarlo.

A diferencia de `reset --hard`, `stash` es **seguro**: no se destruye nada, así
que es el primer reflejo correcto siempre que solo necesites aparcar tu trabajo
un momento.

## ¿Cuál necesito?

| Tu situación | Comando |
| --- | --- |
| Edité un archivo y quiero tirar la edición | `git restore <archivo>` |
| Preparé un archivo por error | `git restore --staged <archivo>` (o `git reset <archivo>`) |
| Quiero rehacer mi último commit (mensaje, o añadir un archivo) | `git reset --soft HEAD~1` |
| Necesito un árbol limpio *ahora mismo* pero quiero recuperar mi trabajo luego | `git stash` → `git stash pop` |
| Quiero deshacer un commit que ya **subí** | `git revert <commit>` |

!!! tip "La regla general de la seguridad primero"
    Si el cambio está **confirmado**, casi siempre puedes recuperarlo, así que
    deshacer es seguro. Si está **sin confirmar**, Git no tiene copia — así que
    haz `stash` antes de hacer nada destructivo.

## Adónde ir después

- [Ejemplo](example.md) — un recorrido completo que junta commits, ramas y
  fusiones.
