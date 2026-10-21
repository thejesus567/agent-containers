# Codex

Desde la raíz del repositorio, con Docker o Podman en ejecución:

```bash
make codex
```

El lanzador construye la imagen si no existe y abre Codex sin montar carpetas
ni pasar claves del equipo. Selecciona **Sign in with Device Code** en la
pantalla de autenticación. La autenticación usa credenciales en memoria
que se pierden al salir; las conversaciones sí se conservan. No se reutiliza
el inicio de sesión del Codex instalado en tu equipo.

Para retomar una conversación anterior:

```bash
make codex-resume
```

Vuelve a autenticarte y selecciona la conversación. También puedes usar `/resume`
desde Codex. El historial vive en el volumen `agent-containers-codex-history`;
los archivos de autenticación permanecen en un directorio temporal separado.

Para eliminar permanentemente el historial cuando dejes esta computadora,
primero sal de todas las sesiones y ejecuta:

```bash
make codex-delete-history
```

No pegues credenciales en las conversaciones: su contenido sí es persistente.

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
