# Comandos

Esta página es un recorrido práctico por los comandos que usarás cada día. De
cada uno: qué hace, las dos o tres opciones que realmente vas a usar, y un
pequeño ejemplo con la salida que puedes esperar.

No necesitas memorizarlos: ten esta página a mano como referencia y la memoria
muscular llegará sola. La página de [Ejemplo](example.md) los encadena luego en
un flujo de trabajo completo.

!!! info "Convenciones usadas abajo"
    Las líneas que empiezan por `$` son comandos que escribes; todo lo demás es
    salida. Las rutas y los hashes provienen de un pequeño proyecto de ejemplo.

## Iniciar un repositorio

### `git init`

Convierte la carpeta actual en un repositorio Git. Crea un directorio oculto
`.git/` que contiene todo el historial; tus archivos quedan intactos.

```console
$ git init
Initialized empty Git repository in /home/user/my-project/.git/
```

Esto se ejecuta **una vez**, al principio de un proyecto.

### `git clone`

Copia un repositorio existente —incluido todo su historial— a tu máquina. Así es
como empiezas a trabajar en un proyecto que ya existe (por ejemplo, uno alojado
en GitHub).

```console
$ git clone https://github.com/jparisu/nim-arena.git
Cloning into 'nim-arena'...
remote: Enumerating objects: 120, done.
Receiving objects: 100% (120/120), 45.2 KiB, done.
```

Clonar también configura un remoto llamado **`origin`** que apunta al origen, de
modo que puedes hacer `push` y `pull` sin configuración adicional.

## Registrar cambios

### `git status`

Muestra el estado actual: qué archivos cambiaron, cuáles están preparados para el
próximo commit y cuáles aún no se rastrean. Es el comando que más ejecutas:
siempre que dudes, ejecuta `git status`.

```console
$ git status
On branch main
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
        modified:   README.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        notes.txt

no changes added to commit (use "git add" and/or "git commit -a")
```

### `git add`

Mueve cambios al área de preparación, para que formen parte del próximo commit.

```console
$ git add README.md        # prepara un archivo
$ git add .                # prepara todo lo de la carpeta actual
```

La preparación es lo que te permite hacer commit de *algunos* de tus cambios y
dejar el resto: solo lo que hagas `add` entra en el commit.

### `git commit`

Registra todo lo que está preparado como un nuevo commit, con un mensaje.

```console
$ git commit -m "feat(players): add the greedy bot"
[main 9f3a1c2] feat(players): add the greedy bot
 1 file changed, 42 insertions(+)
```

- `-m "…"` da el mensaje en línea. Sin él, Git abre un editor.
- Escribe los mensajes en **imperativo** y con sentido — véase
  [Organización § Historial](organization.md#historial).

!!! warning "`git commit -a`"
    `git commit -a` prepara **todos los archivos rastreados** y hace el commit en
    un solo paso. Es un atajo cómodo, pero se salta la revisión que da la
    preparación, y nunca incluye archivos nuevos (sin rastrear). Prefiere un
    `git add` explícito mientras aprendes.

## Inspeccionar

### `git log`

Lee el historial, el commit más reciente primero.

```console
$ git log --oneline
772a47a docs: document the leaderboard schema
a1976d8 feat(tournament): add the championship format
92c1041 Add project skeleton, documentation scaffold and CI
5f46a63 docs: add the game rules
7b0978f Add README
```

- `--oneline` condensa cada commit a una línea — la vista más útil del día a día.
- `--graph --oneline --all` dibuja la estructura de ramas como arte ASCII.
- `-p` muestra el diff completo de cada commit.

### `git diff`

Muestra los cambios como un [diff](organization.md#diffs). Sin argumentos,
muestra lo que has cambiado pero **aún no has preparado**:

```console
$ git diff
diff --git a/README.md b/README.md
index 3b1f2a1..a2c4d9e 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # NIM Arena
+A parametrized NIM engine with a player API.
```

- `git diff --staged` muestra lo que está preparado (es decir, lo que registrará
  el próximo commit).
- `git diff main feature` compara dos ramas.

## Ramificar y fusionar

### `git branch`

Lista, crea o borra ramas.

```console
$ git branch                 # lista; la rama actual se marca con *
* main
$ git branch feature         # crea una rama llamada "feature"
$ git branch -d feature      # borra una rama ya fusionada
```

Crear una rama no te cambia a ella — para eso, usa `checkout`.

### `git checkout`

Cambia entre ramas (y, en general, mueve `HEAD`).

```console
$ git checkout feature       # cámbiate a una rama existente
Switched to branch 'feature'
$ git checkout -b feature    # crea Y cámbiate en un solo paso
Switched to a new branch 'feature'
```

!!! note "`git switch` y `git restore`"
    El Git moderno dividió las dos tareas de `checkout` en comandos más claros:
    `git switch` para cambiar de rama y `git restore` para descartar cambios en
    archivos. `checkout` sigue funcionando y es lo que verás más a menudo, así
    que esta guía lo usa; `restore` se cubre en
    [Deshacer cambios](undoing-changes.md).

### `git merge`

Integra otra rama en la actual.

```console
$ git checkout main
$ git merge feature
Updating 92c1041..9f3a1c2
Fast-forward
 docs/git/commands.md | 120 +++++++++++++++++++++++++++
 1 file changed, 120 insertions(+)
```

Si ambas ramas cambiaron las mismas líneas, la fusión se detiene con un
**conflicto** para que lo resuelvas — véase el [Ejemplo](example.md).

## Sincronizar con un remoto

### `git push`

Envía tus commits locales al remoto (p. ej. GitHub).

```console
$ git push origin main
Enumerating objects: 5, done.
To https://github.com/jparisu/nim-arena.git
   92c1041..9f3a1c2  main -> main
```

La primera vez que subes una rama nueva, usa `git push -u origin <rama>`; el `-u`
recuerda el vínculo, así que después basta con escribir `git push`.

### `git pull`

Trae commits del remoto a tu rama actual. En realidad son dos pasos en uno:
**fetch** de los nuevos commits y luego **merge** en tu rama.

```console
$ git pull
Updating 9f3a1c2..b7d0e11
Fast-forward
 README.md | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

Adquiere el hábito de hacer pull **antes** de empezar a trabajar, para construir
sobre los últimos cambios de tus compañeros y no sobre una copia desactualizada.

## Referencia rápida

| Comando | Para qué sirve |
| --- | --- |
| `git init` | Crear un repositorio en la carpeta actual. |
| `git clone <url>` | Copiar un repositorio existente, con todo su historial. |
| `git status` | Ver qué cambió y qué está preparado. |
| `git add <ruta>` | Preparar cambios para el próximo commit. |
| `git commit -m "…"` | Registrar los cambios preparados con un mensaje. |
| `git log --oneline` | Leer el historial. |
| `git diff` | Inspeccionar cambios aún no preparados. |
| `git branch` | Listar, crear o borrar ramas. |
| `git checkout <rama>` | Cambiar de rama (`-b` para crear). |
| `git merge <rama>` | Integrar una rama en la actual. |
| `git push` | Enviar commits al remoto. |
| `git pull` | Traer commits del remoto a la rama actual. |

## Otros comandos útiles

- `git rebase <branch>` — reorganizar commits para hacer el historial más lineal.
- `git fetch` — traer commits del remoto sin fusionarlos.
- `git cherry-pick <hash>` — aplicar un commit concreto de otra rama.

Otros comandos para deshacer cambios se cubren en [Deshacer cambios](undoing-changes.md):
`git restore`, `git reset`, `git stash`.

## El archivo `.gitignore`

No todos los archivos deben estar en el repositorio. Los artefactos compilados,
los entornos virtuales, las cachés y la configuración del editor se generan en
local y, si se confirman, solo ensuciarían el historial (y causarían conflictos).

Un archivo **`.gitignore`**, colocado en la raíz del repositorio, lista patrones
de archivos que Git debe **ignorar**: nunca aparecen en `git status` y no pueden
añadirse por accidente. Cada línea es un patrón; `#` inicia un comentario.

Este es el `.gitignore` que usa este mismo proyecto — un buen punto de partida
para cualquier proyecto Python:

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
build/
dist/
.venv/
venv/
env/

# Testing / tooling
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/

# MkDocs
site/

# Generated web assets (assembled by scripts/build_web.py or the Pages workflow)
web/py/
web/py.zip
web/leaderboard.json

# OS / editor
.DS_Store
.idea/
.vscode/
*.swp
```

!!! tip
    Añade el `.gitignore` **antes** de tu primer commit, para que el ruido no
    entre nunca en el historial. Si un archivo ya está rastreado, añadirlo al
    `.gitignore` no lo elimina — hay que hacer `git rm --cached <archivo>` una vez.

!!! note "Etiquetas y versiones (tags y releases)"
    Etiquetar commits concretos como versiones publicadas es una función real de
    Git, pero se deja fuera de esta guía a propósito: para este proyecto, entender
    `main` y las ramas es suficiente.

## Adónde ir después

- [Deshacer cambios](undoing-changes.md) — cuando un comando salió mal, o
  cambiaste de opinión.
- [Ejemplo](example.md) — estos comandos, aplicados de principio a fin.
