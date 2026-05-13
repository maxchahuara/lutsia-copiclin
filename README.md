# LUTSIA CopiClin

LUTSIA CopiClin es un copiloto clínico local-first para crear borradores clínicos copiables a partir de audio/transcripciones de consulta.

Estado actual: prototipo técnico pre-release. No es HCE/EHR, no diagnostica y no debe usarse sin revisión médica humana.

## Principios

- Datos locales por usuario.
- Sin backend cloud propio de la app.
- Cada usuario inicia sesión con su propia cuenta ChatGPT/Codex si habilita el proveedor Codex.
- No se usan cookies, automatización de ChatGPT Web, endpoints privados ni credenciales del desarrollador.
- Whisper/faster-whisper local es permitido para transcripción.


## Primer arranque

Al abrir CopiClin por primera vez, la app muestra una configuración inicial obligatoria:

1. Verificar conexión de cuenta ChatGPT/Codex por usuario.
2. Verificar instalación de Whisper/faster-whisper para transcripción local.
3. Verificar runtime de audio/FFmpeg.
4. Confirmar que CopiClin solo genera borradores revisables por el médico.

Si faltan pasos, la app permite continuar únicamente para demo/pruebas locales, pero no marca el sistema como listo para uso real.

## Desarrollo local

Requisitos:

- Python 3.11+
- Node.js 22+
- npm
- Opcional: Codex CLI oficial (`@openai/codex`) para la ruta de cuenta Codex.

```bash
make setup
make check
make dev-backend
```

En otra terminal:

```bash
make dev-frontend
```

Backend local: <http://127.0.0.1:8765>
Frontend dev: <http://127.0.0.1:5173>

## Construir frontend embebido

```bash
make frontend-build
```

Esto genera `frontend/dist` y copia los archivos estáticos a `backend/app/static`, que el backend sirve desde `/`.

## Ejecutar app instalada desde código fuente

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
npm --prefix frontend install
make frontend-build
lutsia-copiclin-api
```

Para la ventana desktop:

```bash
lutsia-copiclin-desktop
```

## Cuenta Codex por usuario

CopiClin usa un `CODEX_HOME` propio por usuario, no `~/.codex`:

```text
<directorio de datos del usuario>/LUTSIA CopiClin/codex
```

La app expone:

- `GET /auth/codex/status`
- `GET /auth/codex/login-instructions`

El login esperado es mediante Codex CLI oficial y device auth, con el `CODEX_HOME` que indique la app.

## Tests

```bash
make check
```

Incluye lint Python, tests backend, compileall y build frontend.

## Licencia

MIT. Puedes usar, estudiar, modificar y hacer fork del proyecto libremente, manteniendo el aviso de licencia.
