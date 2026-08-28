# Despliegue del frontend en AWS

Este documento cubre **solo `apps/web`**: el sitio estatico. El backend (API Gateway,
Lambdas, DynamoDB, SQS, Step Functions) se despliega aparte con CDK y todavia no existe.

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

```bash
python infra/cloudfront/attach_function.py --distribution-id <ID-de-la-distribucion>
```

Crea la funcion, la publica a LIVE, la asocia como `viewer-request` al
comportamiento por defecto e invalida la cache. Es idempotente: correrlo dos
veces no rompe nada.

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
