# Despliegue en AWS

Dos stacks independientes:

- **Frontend** — sitio estatico en S3 privado + CloudFront. Desplegado con la skill
  `deploy-spa-aws`. Es el resto de este documento hasta la seccion "Backend".
- **Backend** — API Gateway, Lambdas, DynamoDB, S3 y SQS, con AWS CDK. Ver la
  seccion "Backend (fase 1)" al final.

## Arquitectura del hosting

```
Navegador -> CloudFront (HTTPS, cache, CloudFront Function) -> S3 privado (OAC)
```

- El bucket S3 es **100% privado**. No tiene website hosting ni politica publica.
- CloudFront lo lee mediante un **Origin Access Control (OAC)**; la policy del bucket
  solo autoriza a esa distribucion.
- Una **CloudFront Function** en `viewer-request` resuelve las rutas del export
  (`/dashboard` -> `/dashboard/index.html`). Ver `infra/cloudfront/append-index.js`.
- `CustomErrorResponses` manda 403/404 a `/index.html` con 200 como red de seguridad.

## Por que hubo que tocar el codigo

`output: "export"` no admite nada que corra en servidor. El frontend tenia tres cosas
incompatibles:

| Que habia | Por que rompia | Que se hizo |
|---|---|---|
| `apps/web/proxy.ts` con `clerkMiddleware` | El export no genera middleware/proxy | Eliminado. La proteccion de `/dashboard` es ahora client-side |
| `app/dashboard/page.tsx` con `currentUser()` | `@clerk/nextjs/server` requiere servidor | Componente cliente con `useUser()` + redireccion a `/sign-in` |
| `@clerk/nextjs` (build de App Router) | Registra React Server Actions, que `output: "export"` rechaza | Reemplazado por `@clerk/react` en `components/AppShell.tsx` |
| Rutas catch-all `[[...sign-in]]` / `[[...sign-up]]` | El export no puede prerenderizar los pasos anidados del flujo | Paginas planas con `<SignIn routing="hash" />` |

**Consecuencia de seguridad, explicita:** ya no hay ninguna verificacion de sesion en
el servidor del frontend. La proteccion de rutas es cosmetica: evita que un usuario
sin sesion vea la UI, no impide que alguien pida el HTML. El limite real de
autorizacion es el **Lambda authorizer de API Gateway**, que valida el JWT de Clerk en
cada peticion y filtra por `userId` (CLAUDE.md, seccion 8). Esto no cambia el modelo de
amenazas: ya era asi, porque el HTML y el JS siempre fueron publicos.

## Variables de entorno

Se hornean en el bundle **en tiempo de build**. Cambiar una exige reconstruir y
volver a desplegar. Copiar `apps/web/.env.local.example` a `apps/web/.env.local` y
rellenar. `CLERK_SECRET_KEY` ya no se usa en el frontend.

## Desplegar

Configuracion en `deploy.config.yml` (entorno `prod`, perfil AWS `po-agent`).
Consumida por la skill `deploy-spa-aws`.

```bash
# diagnostico de la maquina
python <ruta-skill>/deploy.py --check --profile po-agent

# primer despliegue: crea bucket + OAC + distribucion + policy
python <ruta-skill>/deploy.py --env prod

# despliegues siguientes: re-sync + invalidacion
python <ruta-skill>/deploy.py --env prod --update

# volver atras
python <ruta-skill>/deploy.py --env prod --list-versions
python <ruta-skill>/deploy.py --env prod --rollback <snapshot-id>
```

Tras el **primer** despliegue, asociar la CloudFront Function una sola vez:

```powershell
./infra/cloudfront/attach-function.ps1 -DistributionId <ID-de-la-distribucion>
```

## Costo

El sitio compilado pesa ~1,2 MB. Con trafico de proyecto academico, el consumo queda
holgadamente dentro de la capa gratuita de CloudFront y S3. Aun asi, crear un
presupuesto de gasto cero en AWS Billing antes del primer despliegue: es la unica
proteccion real contra una sorpresa.

## Pendiente

- `NEXT_PUBLIC_API_BASE_URL` apunta a localhost hasta que exista la API. El sitio
  desplegado renderiza la landing y el login; el dashboard fallara al llamar la API.
- Si se usa una instancia **de produccion** de Clerk (`pk_live_`), hay que registrar el
  dominio de CloudFront en Clerk. Con `pk_test_` funciona en cualquier dominio.
- CORS en API Gateway debera permitir el origen de CloudFront.


---

# Backend (fase 1)

## Que hay desplegado

```
Navegador -> API Gateway (HTTP API) -> Lambda api      -> DynamoDB
                                                        -> S3 (transcripciones)
                                                        -> SQS
                                       SQS -> Lambda worker -> run_pipeline -> Gemini
                                                             -> DynamoDB
```

`POST /jobs` guarda la transcripcion en S3, crea el job en DynamoDB, encola y
responde 202. El worker toma el mensaje y corre el pipeline completo. El frontend
hace polling sobre `GET /jobs/{id}` hasta que el estado sea terminal.

**Lo que esta fase todavia no hace:** el pipeline corre como una sola Lambda, no
como siete etapas en Step Functions. El techo de 15 minutos de Lambda es el limite
conocido de esta forma, y es exactamente la razon por la que existe la fase 2
(CLAUDE.md §3.1a). Nada de lo desplegado aqui cambia cuando llegue: la cola, la
tabla, el bucket y la API se reutilizan tal cual.

## Una sola app FastAPI, dos runtimes

`services/api/app.py` es la API, y corre igual en local (uvicorn, store en memoria,
pipeline como background task) que en Lambda (Mangum, DynamoDB + S3, pipeline via
SQS). Que camino se toma lo deciden las variables de entorno; no hay una segunda
implementacion que mantener sincronizada (§10).

| Variable | Efecto si esta presente |
|---|---|
| `DDB_TABLE_NAME` + `S3_BUCKET_TRANSCRIPTS` | Usa DynamoDB + S3 en vez del store en memoria |
| `SQS_QUEUE_URL` | `POST /jobs` encola en vez de correr en background |
| `CORS_ALLOWED_ORIGINS` | Origenes permitidos (nunca `*`: estas peticiones llevan token de Clerk) |
| `CLERK_SECRET_KEY_PARAM` / `LLM_API_KEY_PARAM` | Nombre del parametro SSM del que sacar el secreto en el arranque en frio |

## Modelo de datos

Tabla unica, claves segun CLAUDE.md §6:

| Entidad | PK | SK |
|---|---|---|
| Job | `USER#{userId}` | `JOB#{jobId}` |
| Resultado | `JOB#{jobId}` | `RESULT#v1` |
| Artefacto | `JOB#{jobId}` | `ARTIFACT#{type}#{id}` |
| Indice de artefacto | `ARTIFACT#{id}` | `INDEX` |

Los artefactos son items separados, no un blob unico: un backlog terminado puede
pasar el limite de 400 KB por item, y editar una historia obligaria a reescribir el
resultado entero. `GET /jobs/{id}/result` los recompone con una sola Query.

El estado de cada modelo se guarda como JSON en el atributo `body`. DynamoDB no
tiene tipo float y estos modelos estan llenos (`confidence`, `estimatedHours`);
pasar por Decimal es ruidoso y con perdida.

Las transcripciones crudas van a S3, nunca a DynamoDB: son la unica entrada sin cota.

## Secretos

CloudFormation **no puede crear parametros SecureString**, asi que se escriben una
vez a mano y CDK solo concede permiso de lectura. Se usa Parameter Store en lugar de
Secrets Manager porque es gratis, y §12 prohibe meter componentes con costo fijo sin
discutirlo.

```powershell
aws ssm put-parameter --name /po-agent/clerk-secret-key --type SecureString `
  --value "<sk_test_...>" --overwrite --profile po-agent-cdk

aws ssm put-parameter --name /po-agent/llm-api-key --type SecureString `
  --value "<clave de Gemini>" --overwrite --profile po-agent-cdk
```

## Desplegar

Requiere el perfil `po-agent-cdk` (permisos amplios) y `cdk bootstrap` hecho una vez.

```powershell
cd infra
npm install
npm run build:assets    # copia services/ y compila la capa para linux
npx cdk deploy --profile po-agent-cdk
```

`build-assets.mjs` instala las dependencias con `--platform manylinux2014_x86_64`
en lugar de compilarlas para el equipo local. Es lo que evita el fallo clasico:
`pydantic-core` y `cryptography` son extensiones nativas, y una rueda de Windows
importa bien en tu maquina y revienta dentro de Lambda con un error de ELF. No hace
falta Docker.

El deploy imprime `ApiUrl`. Ese valor va en `apps/web/.env.local` como
`NEXT_PUBLIC_API_BASE_URL`, y despues hay que **redesplegar el frontend**: la URL se
hornea en el bundle en tiempo de build.

## Costo

DynamoDB y SQS bajo demanda, Lambda por invocacion, S3 con expiracion a 90 dias: con
volumen de proyecto academico, centavos. Lo que cuesta de verdad son las llamadas a
Gemini, y por eso el worker **no reintenta**: si el pipeline falla, el error queda
registrado en el job y el mensaje se borra. Cada reintento automatico seria otra
ronda de llamadas pagadas sobre una transcripcion que ya fallo igual. Los mensajes
malformados, que ni llegan al pipeline, si van a la DLQ.
