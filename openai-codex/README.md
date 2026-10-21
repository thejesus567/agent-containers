# Codex

Desde la raíz del repositorio, con Docker o Podman en ejecución:

```bash
make codex
```

El lanzador construye la imagen si no existe y abre Codex sin montar carpetas
ni pasar claves del equipo. Selecciona **Sign in with Device Code** en la
pantalla de autenticación. La sesión usa credenciales en memoria y se elimina
al salir; no se reutiliza el inicio de sesión del Codex instalado en tu equipo.

Para consultar código local sin permitir cambios:

```bash
./codex.sh --project /ruta/a/proyecto
```

Todos los archivos de esa carpeta quedan visibles, incluidos archivos ocultos
y secretos ignorados por Git. Comparte únicamente una carpeta sin credenciales.

Para construir sin abrir Codex:

```bash
make openai-codex
```

Para comprobar la versión instalada:

```bash
docker run --rm openai-codex --version
```

La imagen usa `/home/node` y configuración actual de Codex; no utiliza
`--approval-mode auto-edit`, `config.yaml` ni `/home/codeuser`.
No montes tu configuración local de Codex: puede contener tokens de acceso.

Consulta el [README principal](../README.md) para requisitos, actualización,
autenticación y límites del aislamiento.

Referencias oficiales: [autenticación](https://developers.openai.com/codex/auth)
y [CLI](https://developers.openai.com/codex/cli/reference).
