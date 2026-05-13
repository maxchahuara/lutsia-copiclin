# LUTSIA CopiCLin

LUTSIA CopiCLin es un copiloto clinico local-first para medicos. Su objetivo es grabar entrevistas clinicas autorizadas, transcribirlas localmente con Whisper y organizar la informacion en una nota estructurada revisable por el profesional.

La app no diagnostica, no propone tratamientos y no toma decisiones clinicas. Codex solo ayuda a ordenar informacion explicitamente mencionada en la entrevista para que el medico la revise, corrija y use bajo su criterio.

Estado actual: pre-release funcional local. No es HCE/EHR, no reemplaza el juicio clinico y no debe usarse sin revision medica humana.

## Que hace hoy

- Gestiona pacientes reales en almacenamiento local por usuario.
- Graba entrevistas clinicas desde el navegador local, con consentimiento confirmado antes de iniciar.
- Transcribe audio con `faster-whisper` en la PC del usuario.
- Usa la cuenta ChatGPT/Codex del usuario para organizar la transcripcion en una nota clinica estructurada.
- Muestra estados de proceso con animacion mientras transcribe y mientras organiza la informacion.
- Permite revisar la transcripcion fuente junto a la nota estructurada.
- Organiza notas por paciente y por fecha, de mas reciente a mas antigua.
- Permite copiar el resumen estructurado para uso posterior.
- Mantiene la experiencia enfocada en un flujo simple: pacientes, captura, transcripcion, notas y configuracion.

## Flujo principal

1. Crear o seleccionar un paciente.
2. Confirmar que el paciente autorizo la grabacion.
3. Iniciar grabacion.
4. Finalizar y transcribir.
5. Whisper procesa el audio localmente.
6. Codex organiza la informacion transcrita.
7. El medico revisa la nota estructurada y la transcripcion fuente.
8. La nota queda disponible en `Notas estructuradas`, agrupada por paciente y fecha.

## Lo que la IA no hace

LUTSIA CopiCLin esta disenado como herramienta de apoyo documental, no como sistema de decision clinica.

La IA no debe:

- Diagnosticar.
- Sugerir diagnosticos diferenciales.
- Indicar tratamientos.
- Recomendar medicacion.
- Sustituir la revision del medico.
- Presentar informacion no mencionada como si fuera un hecho.

Cuando faltan datos, la nota debe dejarlo indicado como informacion faltante, pendiente o incierta.

## Arquitectura

La aplicacion corre localmente:

- Frontend: React + Vite.
- Backend: FastAPI.
- Desktop shell: pywebview.
- Transcripcion: `faster-whisper` local.
- Organizacion clinica: Codex CLI con la sesion ChatGPT/Codex del usuario.
- Almacenamiento inicial: JSON local por usuario.
- Frontend embebido: `backend/app/static`.

No hay backend cloud propio de LUTSIA CopiCLin en esta version.

## Privacidad y seguridad

Principios actuales:

- Los datos se guardan localmente en la PC del usuario.
- La grabacion requiere confirmacion de consentimiento en la interfaz.
- La transcripcion se realiza con Whisper local.
- La app no lee tokens crudos, cookies del navegador ni credenciales privadas.
- La cuenta Codex se conecta mediante el flujo oficial del Codex CLI.
- Las notas generadas son borradores revisables.

Ubicacion de datos por defecto:

```text
<directorio de datos del usuario>/LUTSIA/LUTSIA CopiClin/
```

El `CODEX_HOME` usado por la app se mantiene separado:

```text
<directorio de datos del usuario>/LUTSIA/LUTSIA CopiClin/codex
```

## Primer uso

Al iniciar la app, el sistema verifica:

1. Cuenta ChatGPT/Codex conectada.
2. Whisper/faster-whisper disponible localmente.
3. Modelo Whisper seleccionado.
4. Runtime de audio disponible.
5. Uso seguro: revision humana obligatoria.

Si todo esta listo, el usuario puede crear pacientes y comenzar entrevistas autorizadas.

## Modelos Whisper

La app soporta seleccion de modelos Whisper locales segun velocidad y precision:

- `tiny`
- `base`
- `small`
- `medium`
- `large-v3`
- `turbo`

El modelo `small` es el valor recomendado por defecto para uso diario equilibrado.

## Desarrollo local

Requisitos:

- Python 3.11+
- Node.js 22+
- npm
- Git
- Codex CLI oficial (`@openai/codex`) para la integracion con cuenta ChatGPT/Codex

Instalacion:

```bash
make setup
```

Ejecutar backend:

```bash
make dev-backend
```

Ejecutar frontend en otra terminal:

```bash
make dev-frontend
```

URLs locales:

- Backend: <http://127.0.0.1:8765>
- Frontend dev: <http://127.0.0.1:5173>

## Construir frontend embebido

```bash
make frontend-build
```

Ese comando genera `frontend/dist` y copia los archivos estaticos a `backend/app/static`.

Tambien se puede ejecutar manualmente:

```bash
npm --prefix frontend run build
```

Luego copiar `frontend/dist` dentro de `backend/app/static`.

## Ejecutar desde codigo fuente

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
npm --prefix frontend install
make frontend-build
lutsia-copiclin-api
```

Para abrir la ventana desktop:

```bash
lutsia-copiclin-desktop
```

## Endpoints principales

Pacientes:

- `POST /patients`
- `GET /patients`

Consultas:

- `POST /consultations`
- `GET /consultations`
- `GET /consultations/{consultation_id}`
- `POST /consultations/{consultation_id}/audio/upload`
- `POST /consultations/{consultation_id}/transcribe`
- `GET /consultations/{consultation_id}/transcript`
- `POST /consultations/{consultation_id}/generate-note`
- `GET /consultations/{consultation_id}/note`

Configuracion:

- `GET /setup/status`
- `POST /setup/complete`
- `GET /transcription/models`
- `PUT /transcription/model`
- `POST /transcription/models/{model_name}/install`

Cuenta Codex:

- `GET /auth/codex/status`
- `POST /auth/codex/login/start`
- `GET /auth/codex/login/session/{session_id}`
- `DELETE /auth/codex/login/session/{session_id}`

## Verificacion

Comandos usados para validar cambios:

```bash
npm --prefix frontend run build
python -m pytest
python -m ruff check backend apps scripts
python -m compileall -q backend apps scripts
```

## Alcance actual

Incluido:

- Pacientes.
- Captura de audio autorizada.
- Transcripcion local.
- Organizacion de informacion clinica.
- Notas estructuradas por paciente y fecha.
- Configuracion de Codex y Whisper.

No incluido en esta version:

- Telemedicina.
- Facturacion.
- Ask LUTSIA.
- Gestion de equipos.
- Integraciones EMR/EHR.
- Diagnostico o decision clinica automatizada.

## Licencia

MIT. Puedes usar, estudiar, modificar y hacer fork del proyecto libremente, manteniendo el aviso de licencia.
