# Voice Command API en 4Geeks Academy

<!-- hide -->

Por [@ehiber](https://github.com/ehiber) y [otros contribuidores](https://github.com/4GeeksAcademy/voice-command-api/graphs/contributors) en [4Geeks Academy](https://4geeksacademy.com/)

[![build by developers](https://img.shields.io/badge/build_by-Developers-blue)](https://4geeks.com)
[![4Geeks Academy](https://img.shields.io/twitter/follow/4geeksacademy?style=social&logo=x)](https://x.com/4geeksacademy)

_These instructions are also available in [English](./README.md)._

**Antes de empezar**: Lee la guia de [como comenzar un proyecto de programacion](https://4geeks.com/lesson/how-to-start-a-project) antes de escribir codigo.

> ¡Te necesitamos! Estos ejercicios se construyen y mantienen en colaboracion con personas como tu. Si encuentras algun error 🐞 o falta de ortografia, por favor contribuye y/o reportalo.

<!-- endhide -->

---

## 🎯 Tu reto

Este repositorio es el template inicial del proyecto **Voice Command API**.

El frontend ya esta construido. Graba hasta **20 segundos** de audio en el navegador, envia ese audio a tu backend y muestra:

- la transcripcion devuelta por la API
- la respuesta final de tareas devuelta por la API

Tu trabajo es implementar el backend para que todo el flujo de voz a accion funcione de punta a punta.

---

## Como funciona el proyecto

El frontend usa un unico punto de entrada publico:

- `POST /transcribe`

El frontend **no** decide intenciones con Web Speech API. Solo captura audio (hasta 20 segundos), envia el archivo a `POST /transcribe` y muestra la transcripcion devuelta por el backend para depurar mejor.

Ese endpoint debe:

1. recibir el audio grabado desde el frontend
2. transcribirlo a texto
3. reutilizar la misma logica de routing que `POST /instruction`
4. ejecutar la accion correspondiente sobre las tareas en memoria
5. devolver la transcripcion, la instruccion y el resultado final

Tu backend tambien debe exponer:

- `POST /instruction`
- `GET /tasks`
- `POST /tasks`
- `PUT /tasks/{task_id}`
- `PATCH /tasks/{task_id}`
- `DELETE /tasks/{task_id}`

Importante:

- Usa **solo almacenamiento en memoria**. No base de datos ni archivos.
- El frontend ya viene dado y no deberias modificarlo como parte del ejercicio.
- El backend incluido en este repositorio es solo un template. Tu debes completar la logica faltante.

---

## Estructura del repositorio

```text
voice-command-api/
|-- .devcontainer/           # Configuracion para Codespaces
|-- frontend/                # Frontend ya listo
|   |-- public/
|   `-- src/
|-- src/
|   `-- app/
|       |-- api/routes/      # /transcribe, /instruction, /tasks
|       |-- core/            # Configuracion
|       |-- schemas/         # Contratos de request y response
|       |-- services/        # Aqui va tu implementacion
|       `-- utils/
|-- pyproject.toml
|-- README.md
`-- README.es.md
```

---

## 🌱 Como iniciar el proyecto

Puedes abrir este proyecto en [GitHub Codespaces](https://codespaces.new/4GeeksAcademy/voice-command-api) o clonarlo localmente.

Si usas Codespaces, el repositorio ya incluye un `.devcontainer` preparado para Python, Node, FastAPI y Vite.

### Opcion A: GitHub Codespaces

1. Abre el repositorio en Codespaces.
2. Espera a que el dev container termine de instalar dependencias.
3. Crea `.env` a partir de `.env.example`.
4. Crea `frontend/.env` a partir de `frontend/.env.example`.
5. Ejecuta el backend y el frontend desde la terminal.

### Opcion B: Configuracion local

```bash
git clone https://github.com/4GeeksAcademy/voice-command-api
cd voice-command-api
```

Crea tu propio repositorio y actualiza el remoto:

```bash
git remote set-url origin https://github.com/TU_USUARIO/TU_REPOSITORIO
```

### Configuracion del backend

 Crea `.env` en la carpeta raiz del proyecto (junto a `pyproject.toml`) copiando la plantilla:

```bash
cp .env.example .env
```

Abre `.env` y reemplaza `GROQ_API_KEY` por una API key valida de Groq. No compartas ni subas este archivo a GitHub. La clave se usa solamente en el backend; no la pongas en `frontend/.env`.

Variables disponibles:

| Variable | Obligatoria | Uso |
| --- | --- | --- |
| `GROQ_API_KEY` | Si | API key de Groq. Es necesaria tanto para transcribir audio como para interpretar instrucciones. |
| `GROQ_MODEL` | No | Modelo de chat que convierte la transcripcion en una accion. La plantilla incluye un valor predeterminado. |
| `GROQ_TRANSCRIPTION_MODEL` | No | Modelo speech-to-text. El valor predeterminado es `whisper-large-v3-turbo`. |
| `REQUEST_TIMEOUT_SECONDS` | No | Tiempo limite para las solicitudes a Groq (45 segundos por defecto). |
| `ALLOWED_ORIGINS` | No | Origenes permitidos por CORS, separados por comas. Para Vite local, conserva `http://localhost:5173,http://127.0.0.1:5173`. |

No agregues comillas alrededor de los valores del `.env`. Si cambias variables, reinicia el backend.

Instala dependencias y ejecuta la API:

```bash
uv sync
uv run uvicorn src.main:app --reload
```

Deja esta terminal abierta. La API queda disponible en `http://127.0.0.1:8000` y la documentacion interactiva en `http://127.0.0.1:8000/docs`.

### Configuracion del frontend

Crea `frontend/.env` a partir de `frontend/.env.example`.
Crea `frontend/.env` desde la raiz del proyecto:

```bash
cp frontend/.env.example frontend/.env
```

La plantilla configura `VITE_API_BASE_URL=http://127.0.0.1:8000`, que debe apuntar a la URL del backend. Esta variable no es una API key. Si la cambias, reinicia Vite.

Ejecuta el frontend:

```bash
cd frontend
npm install
npm run dev
```

Abre en el navegador la URL que muestre Vite (normalmente `http://localhost:5173`). Permite el acceso al microfono cuando el navegador lo solicite. Mantén las terminales del backend y del frontend en ejecucion al mismo tiempo.

> Requisitos locales: Python 3.11 o superior, `uv`, Node.js y npm. En Windows PowerShell, usa `Copy-Item .env.example .env` y `Copy-Item frontend/.env.example frontend/.env` para copiar las plantillas.

### Probar y diagnosticar la transcripcion

Primero confirma que el backend esta activo abriendo `http://127.0.0.1:8000/` (debe responder `{"status":"ok"}`). Puedes probar la API y ver errores en `http://127.0.0.1:8000/docs`. Para comprobar la transcripcion directamente desde una terminal, usa un archivo de audio real compatible con Groq:

```bash
curl -X POST http://127.0.0.1:8000/transcribe \
  -F "file=@./grabacion.webm;type=audio/webm" \
  -F "language=es"
```

Reemplaza `./grabacion.webm` por la ruta a tu archivo. El campo `language` es opcional; se puede omitir para autodeteccion. El frontend graba hasta 20 segundos y envia el audio al backend para que Groq lo transcriba.

Si aparece `The speech-to-text service failed to transcribe the audio.`, el backend no pudo completar la solicitud de transcripcion a Groq (HTTP 502). Revisa la terminal donde corre Uvicorn: ahora imprime el error original de Groq y su traceback, que permiten distinguir entre una clave invalida, un modelo no disponible, limites/cuota de la cuenta, problemas de red o un formato de audio rechazado. Verifica que:

1. `GROQ_API_KEY` este configurada en el `.env` de la raiz, sin espacios sobrantes, y que la clave siga activa.
2. `GROQ_TRANSCRIPTION_MODEL` sea un modelo de transcripcion disponible para tu cuenta (por defecto `whisper-large-v3-turbo`).
3. El archivo contenga audio y use un formato admitido por Groq, como WebM, WAV, MP3, M4A u OGG; prueba tambien con una grabacion breve y clara.
4. El backend se haya reiniciado despues de editar `.env` y tenga conexion a internet.

La respuesta HTTP 503 con `GROQ_API_KEY is missing` indica que el backend no esta leyendo la variable; confirma que el archivo se llama exactamente `.env`, esta en la raiz del repositorio y arranca Uvicorn desde esa carpeta. Un error distinto durante `/instruction` afecta al modelo de chat/routing, no a la transcripcion de audio.

---

## 💻 Qué debes hacer

- [ ] Crea una lista `tasks` a nivel de modulo con `id`, `title` y `done`, usando IDs unicos e incrementales.
- [ ] Implementa `GET /tasks`, `POST /tasks`, `PUT /tasks/{task_id}`, `PATCH /tasks/{task_id}` y `DELETE /tasks/{task_id}` con almacenamiento en memoria.
- [ ] Implementa `POST /instruction` para recibir `{ "transcription": "..." }`, llamar a Groq y devolver **solo** JSON de routing (sin ejecutar tareas):

```json
{
  "endpoint": "/tasks",
  "method": "POST",
  "params": { "title": "Buy groceries" }
}
```

- [ ] Implementa `POST /transcribe` para aceptar `multipart/form-data`, convertir audio a texto, reutilizar la logica de `/instruction`, ejecutar la accion y devolver `transcription`, `instruction` y `result`.
- [ ] No hardcodees el routing con reglas manuales como `if "add" in text`.

⚠️ **IMPORTANTE:** El frontend no decide intenciones con Web Speech API. Solo captura audio (hasta 20 segundos), envia a `POST /transcribe` y muestra la transcripcion del backend para depurar STT vs. routing.

```json
{
  "transcription": "add buy groceries to my list",
  "instruction": {
    "endpoint": "/tasks",
    "method": "POST",
    "params": {
      "title": "Buy groceries"
    }
  },
  "result": {
    "id": 1,
    "title": "Buy groceries",
    "done": false
  }
}
```

---

## Tip para depurar

Si la transcripcion que se ve en el frontend ya esta mal, el problema esta en la captura de audio o en el speech-to-text.

Si la transcripcion esta bien pero la accion sale mal, el problema esta en `/instruction`.

---

## ✅ Qué vamos a evaluar

- [ ] `POST /transcribe` recibe audio, transcribe y reutiliza la logica de `/instruction`.
- [ ] `POST /instruction` recibe texto plano y devuelve solo JSON de routing (sin ejecutar acciones).
- [ ] `GET /tasks`, `POST /tasks`, `PUT /tasks/{task_id}`, `PATCH /tasks/{task_id}` y `DELETE /tasks/{task_id}` funcionan correctamente con memoria en proceso.
- [ ] El frontend muestra la transcripcion devuelta por el backend para distinguir errores de STT vs. errores de routing.

---

## 📦 Cómo entregar este proyecto

1. Sube tu solucion a tu repositorio de GitHub.
2. Asegurate de incluir backend y frontend configurados para correr localmente.
3. Comparte el enlace del repositorio y un breve video o GIF mostrando:
   - grabacion de audio (20 segundos maximo),
   - transcripcion visible en frontend,
   - ejecucion correcta de acciones sobre tareas.

---

Este y muchos otros proyectos son construidos por estudiantes como parte de los [Coding Bootcamps](https://4geeksacademy.com/) de 4Geeks Academy. Encuentra mas acerca de los cursos de [Full-Stack Software Developer](https://4geeksacademy.com/es/programas-de-carrera/desarrollo-full-stack), [Data Science & Machine Learning](https://4geeksacademy.com/en/career-programs/data-science-ml), [Ciberseguridad](https://4geeksacademy.com/es/programas-de-carrera/ciberseguridad) e [Ingeniería de IA](https://4geeksacademy.com/es/programas-de-carrera/ingenieria-ia).
