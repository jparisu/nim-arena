# Ejemplo

Esta página une toda la sección **recreando cómo se inició este mismo proyecto,
`nim-arena`** — desde una carpeta vacía hasta un repositorio subido a
GitHub, con una rama y un conflicto de fusión por el camino.

Puedes seguirlo en una carpeta vacía y reproducir cada paso. Los comandos son las
líneas que empiezan por `$`; todo lo demás es salida. Los hashes provienen de una
ejecución concreta — los tuyos serán distintos, porque un hash se calcula a partir
del contenido, el autor y la fecha.

!!! info "Qué necesitas"
    Git instalado (`git --version` debería imprimir una versión) y, para el
    último paso, una cuenta de GitHub. Configura tu identidad una vez, para que
    tus commits se te atribuyan a ti:

    ```console
    $ git config --global user.name "Tu Nombre"
    $ git config --global user.email "tu@ejemplo.com"
    ```

## 1. Crear el repositorio

Empieza en una carpeta vacía y conviértela en un repositorio Git:

```console
$ mkdir nim-arena
$ cd nim-arena
$ git init
Initialized empty Git repository in /home/user/nim-arena/.git/
```

Antes de añadir nada, crea un **`.gitignore`** para que los archivos generados
nunca entren en el historial (véase [Comandos § .gitignore](commands.md#el-archivo-gitignore)):

```console
$ printf '__pycache__/\n.venv/\nsite/\n' > .gitignore
```

## 2. Añadir archivos y hacer el primer commit

Crea un primer archivo — el README del proyecto:

```console
$ printf '# NIM Arena\n' > README.md
```

Comprueba el estado. Git ve dos archivos nuevos que aún no rastrea:

```console
$ git status
On branch main

No commits yet

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        .gitignore
        README.md

nothing added to commit but untracked files present
```

Prepara ambos archivos y registra el primer commit:

```console
$ git add .
$ git commit -m "Initial commit"
[main (root-commit) 29434cf] Initial commit
 2 files changed, 4 insertions(+)
 create mode 100644 .gitignore
 create mode 100644 README.md
```

Añade un poco más al README y haz un segundo commit, para tener algo de
historial:

```console
$ printf '\nA parametrized NIM engine with a player API and a tournament.\n' >> README.md
$ git add README.md
$ git commit -m "Add README"
[main 7b0978f] Add README
 1 file changed, 2 insertions(+)
```

## 3. Inspeccionar el estado

Tres comandos responden a "¿dónde estoy?":

```console
$ git log --oneline
7b0978f Add README
29434cf Initial commit

$ git status
On branch main
nothing to commit, working tree clean

$ git diff
```

`git log` muestra los dos commits, `git status` confirma que no hay nada
pendiente, y `git diff` no imprime nada porque no hay cambios sin confirmar. Este
es el punto de partida limpio para trabajo nuevo.

## 4. Crear una rama y trabajar en ella

El trabajo nuevo va en su propia **rama**, no directamente en `main`. Crea una y
cámbiate a ella:

```console
$ git checkout -b rules-page
Switched to a new branch 'rules-page'
```

Añade el documento de diseño de la documentación y confírmalo:

```console
$ printf '# Rules\n\nRemove sticks from one row. Taking the last stick wins.\n' > RULES.md
$ git add RULES.md
$ git commit -m "docs: add the game rules"
[rules-page 5f46a63] docs: add the game rules
 1 file changed, 3 insertions(+)
```

La rama `rules-page` está ahora un commit por delante de `main`. Nada en `main`
cambió — puedes cambiar de una a otra para comprobarlo:

```console
$ git checkout main
Switched to branch 'main'
$ ls
README.md          # RULES.md no está aquí; vive en la otra rama

$ git checkout rules-page
Switched to branch 'rules-page'
```

## 5. Fusionar la rama de vuelta y resolver un conflicto

Para provocar un conflicto, haremos que ambas ramas cambien **la misma línea**
del README.

En `main`, ajusta la línea de descripción:

```console
$ git checkout main
$ printf '# NIM Arena\n\nA NIM engine with a tournament runner.\n' > README.md
$ git commit -am "docs: reword the README description"
[main a1b2c3d] docs: reword the README description
```

En `rules-page`, cambia *la misma línea* de otra forma:

```console
$ git checkout rules-page
$ printf '# NIM Arena\n\nA parametrized NIM game and a player API.\n' > README.md
$ git commit -am "docs: reword the README description"
[rules-page e4f5a6b] docs: reword the README description
```

Ahora fusiona `rules-page` en `main`. Git no puede decidir qué redacción gana:

```console
$ git checkout main
$ git merge rules-page
Auto-merging README.md
CONFLICT (content): Merge conflict in README.md
Automatic merge failed; fix conflicts and then commit the result.
```

Abre `README.md`. Git ha marcado la región en conflicto:

```text
# NIM Arena

<<<<<<< HEAD
A NIM engine with a tournament runner.
=======
A parametrized NIM game and a player API.
>>>>>>> rules-page
```

- Todo lo que está entre `<<<<<<< HEAD` y `=======` es **tu** versión (`main`).
- Todo lo que está entre `=======` y `>>>>>>> rules-page` es la versión
  **entrante**.

**Resuélvelo** editando el archivo hasta dejar el texto final que quieres y
borrando las tres líneas de marcadores:

```text
# NIM Arena

A parametrized NIM engine, a player API and a tournament runner.
```

Luego prepara el archivo resuelto y completa la fusión:

```console
$ git add README.md
$ git commit -m "Merge rules-page into main"
[main 4d9b2fe] Merge rules-page into main
```

El historial muestra ahora ambas líneas de trabajo unidas por un **commit de
fusión**:

```console
$ git log --oneline --graph
*   4d9b2fe Merge rules-page into main
|\
| * e4f5a6b docs: reword the README description
* | a1b2c3d docs: reword the README description
|/
* 7b0978f Add README
* 29434cf Initial commit
```

La rama `rules-page` ha cumplido su propósito y puede borrarse:

```console
$ git branch -d rules-page
Deleted branch rules-page (was e4f5a6b).
```

## 6. Conectar un remoto y subir (push)

Hasta ahora todo vive en tu máquina. Para compartirlo, crea un repositorio vacío
en GitHub (véase la [sección de GitHub](../github/first-steps.md)), luego
conéctalo como remoto **`origin`** y haz push:

```console
$ git remote add origin https://github.com/jparisu/nim-arena.git
$ git push -u origin main
Enumerating objects: 12, done.
Writing objects: 100% (12/12), 1.24 KiB, done.
To https://github.com/jparisu/nim-arena.git
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
```

La opción `-u` vincula tu `main` local con `origin/main`, así que a partir de
ahora bastan un simple `git push` y `git pull`.

## Resumen

En una sesión corta has usado todas las ideas centrales de esta sección:

- **`init`** para crear un repositorio y **`.gitignore`** para mantenerlo limpio,
- **`add`** y **`commit`** para registrar instantáneas,
- **`status`**, **`log`** y **`diff`** para inspeccionar el estado,
- **`branch`** / **`checkout`** para trabajar de forma aislada,
- **`merge`** —incluido **resolver un conflicto**— para juntar el trabajo,
- **`remote`** y **`push`** para compartirlo con el mundo.

Este es exactamente el ciclo que repetirás, una y otra vez, durante el resto del
proyecto. El siguiente paso es hacerlo *en equipo*, que es de lo que trata la
[sección de GitHub](../github/index.md).
