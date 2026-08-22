# Agente PO — Contexto de ingeniería

> Documento de contexto para desarrollo. Va en la raíz del repositorio como `CLAUDE.md`.
> Claude Code lo lee automáticamente al iniciar una sesión en este proyecto.

---

## 1. Qué construimos

Un sistema que recibe la **transcripción de una reunión** y devuelve un **backlog estructurado
y trazable**: épicas, features, historias de usuario con criterios de aceptación, subtareas,
refinamiento y estimación sugerida. Cada artefacto generado apunta a los fragmentos exactos de
la transcripción que lo originan.

Es el proyecto final de una materia de Procesamiento de Lenguaje Natural de maestría. Eso
implica dos cosas que condicionan el código:

1. **La trazabilidad no es opcional.** Todo artefacto lleva referencias al texto fuente. Un
   artefacto sin respaldo es un defecto, no un detalle.
2. **El pipeline se mide por etapas.** Cada etapa registra su latencia, sus entradas y sus
   salidas intermedias, porque esos datos alimentan la evaluación experimental del informe.

El sistema **no reemplaza al Product Owner**: produce un borrador que un humano revisa, edita y
aprueba. Todo artefacto nace en estado `draft`.

---

## 2. Stack

| Capa | Tecnología | Nota |
|---|---|---|
| Frontend | Next.js (App Router) + TypeScript | Desplegado como estático en S3 + CloudFront |
| Autenticación | Clerk | Sesión en el frontend; el backend valida el JWT |
| Backend | Python (AWS Lambda) | Todo el pipeline de PLN vive aquí |
| API | Amazon API Gateway | REST, con autorizador que valida Clerk |
| Cola | Amazon SQS | Desacopla la petición del procesamiento |
| Persistencia | Amazon DynamoDB | Jobs, artefactos y estado |
| Objetos | Amazon S3 | Transcripciones crudas y salidas intermedias |
| Vectores | Amazon S3 Vectors | Solo si se implementa RAG (fase posterior) |
| IaC | AWS CDK (TypeScript) | Infraestructura versionada |
| LLM | Solo por API, detrás de una abstracción de proveedor | Ver §7 |

**Todo se despliega en AWS.** No hay componente autoalojado ni inferencia en máquina propia. El
único uso de la máquina del desarrollador es correr el código Python durante el desarrollo,
apuntando a la API remota del LLM (§11, paso 3).

---

## 3. Arquitectura

Flujo, siguiendo el diagrama acordado:

```
Usuario → CloudFront → S3 (frontend estático)
Usuario → API Gateway → POST /jobs           → encola en SQS → responde 202 + jobId
                        SQS → Lambda dispatcher → Step Functions (pipeline por etapas)
                        Step Functions → Lambdas de etapa → API del LLM
                        Lambdas de etapa → DynamoDB (estado y resultados)
Usuario → API Gateway → GET /jobs/{id}       → Lambda de consulta → DynamoDB
```

El frontend hace **polling** sobre `GET /jobs/{id}` hasta que el estado sea terminal.

### 3.1 Decisiones que el diagrama no cubre

Estas cuatro cosas hay que resolverlas antes de escribir código, porque cambian la estructura:

**a) Step Functions en lugar de una sola Lambda procesadora.**
Una Lambda tiene un límite duro de 15 minutos de ejecución. El pipeline hace varias llamadas al
LLM por reunión (una por segmento temático, más las de consolidación), y una transcripción larga
puede superar ese límite. Además, si falla la etapa 5 se perdería todo el trabajo previo.
Solución: una máquina de estados de Step Functions donde **cada etapa del pipeline es su propia
Lambda**, con reintentos y estado persistido entre etapas. Beneficio adicional: el historial de
ejecución de Step Functions da la latencia por etapa gratis, que es justo lo que necesita el
informe.

**b) Carga de transcripciones por URL prefirmada, no por el cuerpo del POST.**
API Gateway limita el payload a 10 MB y las transcripciones largas pueden acercarse. El flujo
correcto es: `POST /uploads` devuelve una URL prefirmada de S3 → el navegador sube el archivo
directo a S3 → `POST /jobs` recibe solo la clave del objeto.

**c) Dónde corre el clasificador afinado.**
El clasificador de enunciados (un encoder tipo BERT) no cabe en un paquete zip de Lambda (límite
de 250 MB descomprimido) junto con sus dependencias. Dos opciones:
- **Fase 1:** hacer la clasificación con el LLM vía prompt. Simple, sin infraestructura extra.
- **Fase 2:** empaquetar el clasificador en una **Lambda con imagen de contenedor** (hasta 10 GB).
  Cargar el modelo fuera del handler para reutilizarlo entre invocaciones tibias.

Empezar por la opción de fase 1. El clasificador propio se integra cuando exista y esté entrenado.

**d) Vectores.**
DynamoDB no hace búsqueda por similitud. Si se implementa RAG, usar **S3 Vectors**, que es
serverless y encaja con el resto de la arquitectura. No introducir una base vectorial
administrada aparte: sería el único componente con costo fijo por hora del proyecto.

### 3.2 Nota sobre el costo

Al no haber nada autoalojado, **el costo del proyecto es enteramente de nube**. Casi todos los
componentes son de pago por uso y con volumen de proyecto académico caen en montos bajos o
dentro de capa gratuita. Lo que sí cuesta de verdad son las **llamadas al LLM**, y en segundo
lugar el almacenamiento vectorial si se implementa RAG.

Antes de la primera prueba, dos cosas no negociables: **límite de gasto en la consola del
proveedor de LLM** y **alerta de presupuesto en AWS Billing**. Durante los experimentos se harán
corridas repetidas sobre el mismo corpus; sin tope, un bucle mal escrito puede costar caro en
minutos. Cachear las respuestas del LLM por hash del prompt durante el desarrollo para no pagar
dos veces la misma llamada.

### 3.3 Consecuencia para la parte académica

La propuesta entregada al docente planteaba como pregunta de investigación qué calidad se
alcanza ejecutando modelos abiertos sobre hardware de consumo sin GPU. **Al eliminar el
despliegue local, esa pregunta ya no aplica** y hay que sustituirla, o la propuesta queda con un
objetivo que el proyecto no va a responder.

Sustitución recomendada, que preserva el experimento comparativo sin necesitar hardware propio:

> **PI-3 (revisada).** ¿Qué diferencia de calidad, latencia y costo hay entre un modelo abierto
> pequeño y un modelo frontera comercial al ejecutar el mismo pipeline, y en qué etapas se
> concentra esa diferencia?

Ambos se ejecutan en la nube, así que el experimento sigue siendo viable. El eje de "costo cero
por API" desaparece de los diferenciadores del proyecto; los que quedan son **español**,
**trazabilidad verificable** y **pipeline modular medible por etapas**. Actualizar la propuesta
en consecuencia antes de la entrega final.

Nota aparte: procesar transcripciones con datos reales de clientes en un proveedor externo
requiere autorización explícita. Sin ella, se trabaja solo con corpus públicos o con
transcripciones anonimizadas.

---

## 4. Estructura del repositorio

```
/
├── CLAUDE.md                  ← este documento
├── apps/
│   └── web/                   Next.js + TypeScript + Clerk
│       ├── app/
│       ├── components/
│       └── lib/api-client.ts  cliente tipado de la API
├── services/
│   ├── api/                   Lambdas de API (crear job, consultar job, URL prefirmada)
│   │   └── handlers/
│   └── pipeline/              Lambdas de etapa del pipeline de PLN
│       ├── stages/
│       │   ├── normalize.py
│       │   ├── segment.py
│       │   ├── classify.py
│       │   ├── extract_entities.py
│       │   ├── generate_backlog.py
│       │   ├── estimate.py
│       │   └── validate.py
│       ├── llm/               abstracción de proveedor (ver §7)
│       └── models/            modelos Pydantic = fuente de verdad de los contratos
├── packages/
│   └── contracts/             tipos TS generados desde los esquemas de Pydantic
├── infra/                     AWS CDK en TypeScript
└── docs/
    ├── contexto-proyecto.md   documento académico del proyecto
    └── propuesta.md           propuesta entregada al docente
```

---

## 5. Contratos de datos

**Fuente de verdad: los modelos Pydantic en `services/pipeline/models/`.** De ahí se exporta
JSON Schema y de ahí se generan los tipos de TypeScript para el frontend. Nunca escribir los
tipos dos veces a mano.

```bash
python -m scripts.export_schemas        # models → docs/schemas/*.json
npx json-schema-to-typescript ...       # schemas → packages/contracts/src/*.ts
```

Tipos principales (representación en TypeScript, que es la que consume el frontend):

```typescript
type ArtifactStatus = "draft" | "approved" | "discarded";
type JobStatus = "queued" | "running" | "completed" | "failed";

type PipelineStage =
  | "normalize"
  | "segment"
  | "classify"
  | "extract_entities"
  | "generate_backlog"
  | "estimate"
  | "validate";

/** Pointer back to the source transcript. Required on every generated artifact. */
interface SourceReference {
  segmentId: string;
  startCharOffset: number;
  endCharOffset: number;
  startTimeMs?: number;
  endTimeMs?: number;
  speaker?: string;
  verbatim: string;
}

interface Job {
  jobId: string;
  userId: string;
  meetingId: string;
  status: JobStatus;
  currentStage: PipelineStage | null;
  stageTimings: Record<PipelineStage, number>;
  error: string | null;
  createdAt: string;
  completedAt: string | null;
}

interface UserStory {
  id: string;
  featureId: string;
  asA: string;
  iWant: string;
  soThat: string;
  acceptanceCriteria: AcceptanceCriterion[];
  subtasks: Subtask[];
  refinement: Refinement;
  estimate: Estimate | null;
  confidence: number;
  status: ArtifactStatus;
  sources: SourceReference[];
}

interface AcceptanceCriterion {
  id: string;
  given: string;
  when: string;
  then: string;
}

interface Subtask {
  id: string;
  title: string;
  description: string;
  discipline: "frontend" | "backend" | "database" | "infrastructure" | "qa" | "design";
  estimatedHours: number | null;
}

interface Refinement {
  assumptions: string[];
  dependencies: string[];
  risks: string[];
  openQuestions: string[];
  definitionOfDone: string[];
}

interface Estimate {
  storyPoints: 1 | 2 | 3 | 5 | 8 | 13;
  rationale: string;
  method: "llm_reasoning" | "similarity_regression" | "hybrid";
  confidence: number;
}

interface BacklogResult {
  meetingId: string;
  epics: Epic[];
  features: Feature[];
  stories: UserStory[];
  generatedAt: string;
  pipelineVersion: string;
}
```

**Regla invariable:** `sources` nunca puede venir vacío en un artefacto generado. La etapa
`validate` rechaza el artefacto y lo marca para revisión si no tiene respaldo en la transcripción.

---

## 6. API

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/uploads` | Devuelve URL prefirmada de S3 y la clave del objeto |
| `POST` | `/jobs` | Crea el job a partir de una clave de S3. Responde `202` con `jobId` |
| `GET` | `/jobs/{jobId}` | Estado del job y etapa actual |
| `GET` | `/jobs/{jobId}/result` | `BacklogResult` cuando el estado es `completed` |
| `PATCH` | `/artifacts/{id}` | Editar o cambiar el estado de un artefacto |
| `GET` | `/jobs/{jobId}/export?format=json\|markdown\|csv` | Exportación |

Todas requieren un `Authorization: Bearer <clerk_jwt>`.

### Modelo DynamoDB (tabla única)

| Entidad | PK | SK |
|---|---|---|
| Job | `USER#{userId}` | `JOB#{jobId}` |
| Resultado | `JOB#{jobId}` | `RESULT#v{n}` |
| Artefacto | `JOB#{jobId}` | `ARTIFACT#{type}#{id}` |
| Segmento | `JOB#{jobId}` | `SEGMENT#{index}` |

Índice secundario global por `status` para listar jobs en curso.

---

## 7. Abstracción del proveedor de LLM

Requisito del proyecto: poder cambiar de modelo y de proveedor **sin tocar el código del
pipeline**, porque comparar modelos entre sí es uno de los experimentos del informe.

```python
class LlmProvider(Protocol):
    name: str
    async def complete(self, request: CompletionRequest) -> CompletionResponse: ...
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
```

Implementaciones previstas: `OpenAiProvider` y `BedrockProvider`. Bedrock importa porque aloja
modelos de pesos abiertos y pequeños, lo que permite la comparación **modelo pequeño abierto vs.
modelo frontera comercial** sin salirse de AWS. Se selecciona con la variable `LLM_PROVIDER`.

La abstracción se mantiene aunque hoy solo se use un proveedor: es lo que hace posible el
experimento comparativo y protege contra el cambio de precios o de disponibilidad de un modelo a
mitad del semestre.

Reglas para las llamadas al LLM:

- Toda salida se pide **como JSON con esquema declarado** y se valida con Pydantic antes de
  persistirla. Si no valida, se reintenta una vez con el error de validación en el prompt; si
  falla otra vez, se marca la etapa como fallida y se registra.
- **Registrar siempre** el identificador exacto del modelo, la fecha, los tokens de entrada y
  salida, y la latencia. Estos datos van al informe.
- Nunca mandar la transcripción completa en un solo prompt. El pipeline trabaja por segmentos.

---

## 8. Autenticación con Clerk

- **Frontend:** el SDK de Clerk para Next.js maneja sesión, login y protección de rutas. El
  cliente de API adjunta el token de sesión en cada petición.
- **Backend:** un **Lambda authorizer** en API Gateway valida el JWT contra el JWKS público de
  Clerk y extrae el `sub` como `userId`. Cachear las claves en memoria; no pedirlas en cada
  invocación.
- **Aislamiento:** todo acceso a datos filtra por `userId`. Un usuario nunca puede leer el job de
  otro. Esto se verifica en el handler, no solo en el frontend.

Consultar la documentación vigente de Clerk para App Router al implementar; su API cambia entre
versiones mayores.

---

## 9. Variables de entorno

```
# Frontend
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
NEXT_PUBLIC_API_BASE_URL=

# Backend
LLM_PROVIDER=openai|bedrock
LLM_API_KEY=
LLM_MODEL=
LLM_CACHE_ENABLED=true   # cachea por hash del prompt en desarrollo
CLERK_JWKS_URL=
DDB_TABLE_NAME=
S3_BUCKET_TRANSCRIPTS=
SQS_QUEUE_URL=
STATE_MACHINE_ARN=
```

Ningún secreto en el repositorio. En AWS van en Secrets Manager o SSM Parameter Store; en local,
en `.env.local`, que está en `.gitignore`.

---

## 10. Convenciones

- **Todo el código en inglés**: nombres de variables, funciones, comentarios, mensajes de commit,
  strings de log. La documentación del proyecto va en español.
- Python: tipado estricto, `ruff` y `mypy`. Frontend: TypeScript en modo `strict`, sin `any`.
- Sin lógica de negocio en los handlers de Lambda: el handler parsea, delega a una función pura y
  serializa. Eso permite probar el pipeline sin AWS.
- Cada etapa del pipeline es una **función pura** `(input, context) -> output`, testeable con una
  transcripción de ejemplo y sin red. Las llamadas al LLM entran por inyección de dependencia.
- Logs estructurados en JSON, siempre con `jobId` y `stage`.
- Un archivo de transcripción de ejemplo versionado en `services/pipeline/fixtures/` para poder
  correr el pipeline completo en local.

---

## 11. Orden de construcción

Construir en este orden. No saltar pasos: cada uno deja algo verificable.

1. **Andamiaje.** Monorepo, linters, CI básico. Next.js con Clerk funcionando y una página
   protegida. Sin backend todavía.
2. **Contratos.** Modelos Pydantic, exportación a JSON Schema, generación de tipos TS.
3. **Pipeline ejecutable sin infraestructura.** Un script que corre en tu máquina, lee la
   transcripción de ejemplo del directorio de fixtures, ejecuta las etapas en secuencia llamando
   a la API del LLM, e imprime el `BacklogResult`. Sin AWS, sin Lambda, sin cola: solo Python y
   una llamada HTTP. **Este es el hito más importante del proyecto**: si el pipeline no produce
   un backlog decente aquí, ninguna infraestructura lo va a arreglar. No pasar al paso 4 hasta
   que la salida de este script sea revisable por un humano sin vergüenza.
4. **Infraestructura con CDK.** DynamoDB, S3, SQS, API Gateway, Lambdas, Step Functions.
   Desplegar con las etapas todavía como stubs.
5. **Integración.** Conectar las etapas reales a la máquina de estados. Verificar el flujo
   completo desde el POST hasta el estado `completed`.
6. **Frontend real.** Carga de archivo, seguimiento del progreso por etapa, vista del backlog con
   el fragmento de transcripción que respalda cada artefacto, edición y aprobación, exportación.
7. **Instrumentación para el informe.** Endpoint o script que vuelca latencias por etapa, tokens
   consumidos, tasa de JSON inválido y proporción de artefactos sin respaldo.

---

## 12. Qué no hacer

- No mandar la transcripción completa al LLM en un solo prompt.
- No hacer el procesamiento síncrono dentro de un request HTTP.
- No generar artefactos sin `SourceReference`.
- No duplicar definiciones de tipos entre Python y TypeScript.
- No poner credenciales en el código ni en el frontend.
- No subir el corpus de transcripciones reales al repositorio, ni siquiera anonimizado, sin
  autorización escrita.
- No introducir componentes con costo fijo por hora sin discutirlo antes.
