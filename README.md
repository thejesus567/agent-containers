# agent-containers

Ejecuta asistentes de programación en contenedores Docker o Podman.
El flujo principal permite abrir Codex para hacer preguntas sin compartir
archivos ni credenciales de tu equipo.

## Empezar después de clonar

Necesitas Git, Make y Docker Desktop en ejecución (o Podman con su máquina activa).
No necesitas instalar Node.js ni Codex en tu equipo.

Desde la carpeta del repositorio:

```bash
make codex
```

La primera vez construye las imágenes `agent-base` y `openai-codex`.
Las siguientes veces reutiliza la imagen y abre una sesión nueva.

En la pantalla de autenticación de Codex, selecciona **Sign in with Device Code**,
abre el enlace en tu navegador e introduce el código. Si no aparece disponible,
activa el inicio de sesión por código de dispositivo en la configuración de
seguridad de ChatGPT o consulta al administrador de tu espacio de trabajo.
Necesitas una cuenta con acceso a Codex.

Después puedes preguntar, por ejemplo:

> Explícame las diferencias entre una API REST y GraphQL, con ejemplos en Python.

Sal con `/quit`. Al cerrar se elimina el contenedor. El inicio de sesión se
mantiene únicamente en la memoria del proceso, así que debes autenticarte de
nuevo en cada sesión. Las conversaciones sí se conservan para poder retomarlas.

## Retomar conversaciones

```bash
make codex-resume
```

Inicia sesión por código de dispositivo y selecciona una conversación guardada.
También puedes usar `/resume` desde una sesión abierta. `make codex` inicia una
conversación nueva; `make codex-resume` abre el selector de conversaciones.

El historial se guarda en el volumen `agent-containers-codex-history` de Docker
(o Podman). Incluye conversaciones, su índice y la base de datos para retomarlas.
No se comparte el directorio personal ni la configuración de Codex de tu equipo.
Los archivos de autenticación y la configuración de cada ejecución permanecen
en un directorio temporal separado; las credenciales de OpenAI siguen siendo
en memoria y debes iniciar sesión en cada contenedor nuevo.

Para retomar conversaciones sobre un proyecto, comparte de nuevo esa carpeta:

```bash
./codex.sh --resume --project /ruta/a/mi-proyecto
```

## Antes de dejar la computadora

1. Sal de todas las sesiones con `/quit`. Si cerraste una terminal, comprueba
   con `docker ps` que no quede un contenedor de Codex activo y detenlo si lo hay.
2. Si también quieres eliminar tus conversaciones locales, ejecuta:

   ```bash
   make codex-delete-history
   ```

Este comando elimina permanentemente el volumen de historial. El motor rechaza
el borrado si todavía lo usa un contenedor. `make clean` solo elimina imágenes;
no elimina este historial. Las conversaciones pueden contener información
sensible: no pegues claves ni tokens en ellas.

Para evitar dejar una sesión de navegador en esta computadora, completa el
acceso por código de dispositivo desde tu teléfono u otro equipo. Esta
configuración evita archivos persistentes de autenticación de Codex, pero no
promete borrado forense de memoria, swap o copias de seguridad del sistema.

## Consultar un proyecto local

Compartir archivos es opcional y siempre explícito:

```bash
./codex.sh --project /ruta/a/mi-proyecto
```

La carpeta se monta en `/app` en modo de **solo lectura**. Codex puede explicar
el código, pero no modificar los archivos del equipo. No compartas carpetas
con `.env`, claves privadas o secretos en su historial Git: cualquier archivo
dentro de la carpeta compartida puede leerse. `.gitignore` no restringe el acceso.
Las rutas con espacios funcionan; las rutas con comas no están admitidas.

También puedes consultar las opciones de la CLI:

```bash
./codex.sh -- --help
```

## Credenciales y aislamiento

El lanzador `codex.sh`:

- No monta tu directorio personal, `~/.aws`, `~/.kube`, `~/.ssh` ni `~/.codex`.
- No pasa las variables de entorno de tu equipo, incluyendo claves de API.
- No comparte el socket de Docker ni el agente SSH.
- Ejecuta Codex como usuario sin privilegios, con el sistema de archivos del
  contenedor en solo lectura y la política de aprobación `on-request`.
- Usa almacenamiento temporal en memoria para `/tmp` y `/home/node/.codex`.
- Guarda solo los archivos de conversaciones y su base de datos en un volumen
  separado, fuera de `/home/node/.codex`.
- No crea volúmenes de autenticación; usa `cli_auth_credentials_store="ephemeral"`.

La imagen base no instala AWS CLI, kubectl, Terraform, OpenTofu ni el binario
local `tod`. Incluye herramientas generales de desarrollo y Bun para los otros
asistentes del repositorio.

El aislamiento lo aplica Docker/Podman. El lanzador usa
`--sandbox danger-full-access --ask-for-approval on-request` dentro del contenedor
porque el sandbox interno de Codex (Bubblewrap) requiere namespaces que Docker
bloquea. Esto permite ejecutar comandos dentro del contenedor; los montajes de
solo lectura y las restricciones del motor siguen vigentes. Usa `codex.sh` para
aplicar estas restricciones, en lugar de ejecutar la imagen manualmente.

Codex necesita autenticarse para conectarse a OpenAI. Su propia sesión usa
credenciales en memoria; este diseño no constituye una separación absoluta entre
esas credenciales y los procesos del mismo contenedor. Los archivos del equipo
solo se exponen cuando eliges compartir una carpeta. El contenedor tiene red
para conectarse a OpenAI; no está configurado para bloquear acceso a tu red local.

Documentación oficial: [autenticación](https://developers.openai.com/codex/auth)
y [opciones de Codex CLI](https://developers.openai.com/codex/cli/reference).

## Construir y actualizar

```bash
# Build Codex without starting a session (also the default make target)
make openai-codex

# Explicitly select the container engine when building
make openai-codex CONTAINER_ENGINE=docker
```

Codex está fijado a la versión `0.163.0`, verificada con este lanzador.
La instalación se almacena en la caché de construcción. Para probar explícitamente
la versión publicada más reciente después de construir la base:

```bash
docker build --no-cache --build-arg CODEX_VERSION=latest -t openai-codex -f openai-codex/Dockerfile openai-codex
```

Si usas Podman, sustituye `docker` por `podman`. El Makefile y el lanzador
prefieren Podman si ambos motores están instalados.

## Otros asistentes

Se conservan los objetivos de construcción y las instrucciones específicas:

- [Claude Code](claude-code/README.md): `make claude-code`
- [OpenCode](open-code/README.md): `make open-code`
- [Aider](aider/README.md)

`make all` construye la base, Claude Code y Codex. `make clean` elimina las
imágenes del proyecto; no elimina tus archivos locales. Los otros asistentes
usan sus propios flujos de autenticación; las garantías del lanzador anterior
corresponden a `codex.sh`.

## Validación

```bash
python3 -m unittest discover -s tests -p test_codex_launcher.py
python3 tests/test_codex_history.py
```

La segunda prueba requiere Docker en ejecución y la imagen construida. Usa un
servidor simulado sin red para crear y retomar una conversación en contenedores
distintos, verificar que los archivos temporales de autenticación no se conservan
y eliminar únicamente sus propios contenedores y volumen de prueba. No necesita
credenciales de OpenAI.
