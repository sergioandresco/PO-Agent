# Agente PO — Contexto para diseño

> Documento de referencia funcional del frontend actual (Next.js + Tailwind), para pasarlo
> a una herramienta de diseño. Describe cada pantalla, componente, botón, estado y dato que
> se muestra hoy. El objetivo del diseño es dar identidad visual y mejorar la experiencia —
> **no cambiar el flujo funcional**, que ya está construido y probado de punta a punta.

---

## 1. Qué hace la app (una frase)

Un Product Owner pega o sube la transcripción de una reunión, el sistema genera un backlog
completo (épicas → features → historias de usuario, con criterios de aceptación, subtareas,
estimación y trazabilidad exacta a la transcripción), y el PO lo revisa, edita, aprueba o
descarta antes de exportarlo.

## 2. Quién lo usa

Un Product Owner o líder técnico, no necesariamente alguien técnico a nivel de código, pero sí
familiarizado con el vocabulario ágil (épica, historia de usuario, criterio de aceptación, story
points). Trabaja solo (no hay vistas de equipo/colaboración en tiempo real todavía).

## 3. Stack visual actual (línea base, sin identidad propia)

- Next.js App Router + TypeScript, Tailwind CSS v4.
- Sin librería de componentes (todo hecho a mano con clases utilitarias).
- Paleta actual: blanco/negro por defecto (`bg-foreground`/`bg-background`, variables de Tailwind),
  con acentos puntuales: azul para features (`border-blue-400`), amarillo/verde/rojo para los
  badges de estado, sin logo ni tipografía propia más allá de la fuente Geist por defecto de
  Next.js.
- Soporte de modo oscuro parcial vía clases `dark:` de Tailwind en varios componentes, no
  sistemático en todos.
- Responsive: prácticamente no trabajado (es un layout de una sola columna, o dos columnas fijas
  en desktop para el dashboard). Todo el diseño mobile queda abierto.
- Autenticación con Clerk: sus propios modales de sign-in/sign-up (componentes prediseñados de
  Clerk, `<SignInButton>`, `<SignUpButton>`, `<UserButton>`) — esos no se rediseñan a mano, Clerk
  permite tematizarlos por separado si hace falta más adelante.

---

## 4. Inventario de pantallas

### 4.1 Home pública (`/`)

Ruta pública, sin sesión requerida.

- Título: "Agente PO"
- Un párrafo describiendo el producto: *"Convierte la transcripción de una reunión en un backlog
  trazable: épicas, historias de usuario y criterios de aceptación, cada uno respaldado por el
  fragmento exacto de la transcripción que lo origina."*
- Botón/link: **"Ir al dashboard"** → navega a `/dashboard` (si no hay sesión, Clerk redirige a
  sign-in automáticamente).
- Header global (presente en todas las páginas): a la derecha, si no hay sesión, botones
  **"Sign in"** / **"Sign up"** (componentes de Clerk); si hay sesión, el avatar/menú de usuario
  de Clerk (**`UserButton`**, incluye cerrar sesión).

### 4.2 Sign in / Sign up (`/sign-in`, `/sign-up`)

Generadas por Clerk (`clerk init`), con su propio formulario: email + password, más botones de
OAuth (Google, GitHub, Microsoft). No se han personalizado visualmente. Diseñarlas es opcional —
Clerk permite aplicar un tema (`appearance` prop) sin tocar la lógica.

### 4.3 Dashboard (`/dashboard`) — la pantalla principal

Ruta protegida (redirige a sign-in si no hay sesión). Muestra: *"Sesión activa: {email del
usuario}"* arriba, y debajo el layout principal, dividido en dos columnas en desktop:

**Columna izquierda (contenido principal, la más ancha):**
1. Formulario para generar un nuevo backlog
2. Estado del job en curso (si hay uno)
3. Botones de exportación (cuando el job está completo)
4. La vista del backlog generado (jerarquía de tarjetas)

**Columna derecha (barra lateral, angosta, ~18rem):**
5. "Mis reuniones" — historial de jobs pasados

Debajo del formulario:

---

#### 4.3.1 Formulario "generar backlog"

- Campo de texto: **"Meeting ID"** — identificador corto de la reunión (input simple).
- Campo de archivo: **"Subir archivo de transcripción (.txt)"** — selector de archivo nativo,
  acepta `.txt`. Al elegir un archivo: se lee en el navegador (nunca se sube a ningún servidor
  de almacenamiento) y su contenido llena automáticamente el campo de texto de abajo; el nombre
  del archivo (sin extensión) también rellena el Meeting ID si el usuario no lo ha tocado.
  - Texto de ayuda debajo: *"El archivo se lee en tu navegador, nunca se sube a ningún lado —
    solo se envía el texto al iniciar el job."*
- Campo de texto grande (textarea, ~10 filas): **"Transcripción"** — el usuario puede pegar el
  texto directamente en vez de (o además de) subir un archivo. Placeholder de ejemplo:
  `[00:00:03] Ana (Product Manager): ...`
- Botón primario: **"Generar backlog"** (texto cambia a "Enviando…" mientras se envía). Deshabilitado
  si la transcripción está vacía o mientras se envía.

Formatos de transcripción que el sistema ya reconoce automáticamente (info de contexto, no se
muestra al usuario en pantalla, pero puede ser útil para el copy/ayuda del diseño):
- `[HH:MM:SS] Hablante: texto`
- `Hablante: texto` (sin timestamp)
- Formato con marcadores `[Inicio de la transcripción]` / `[Fin de la transcripción]` que acota
  el diálogo real (ignora encabezados tipo "Asunto:", "Participantes:", y pies como "Acuerdos y
  definiciones")
- Un formato tipo Google Meet/Teams (hablante + hora corta en una línea, texto en la siguiente) —
  soportado como respaldo, aún sin verificar contra un export real.

#### 4.3.2 Estado del job

Mientras/después de correr, debajo del formulario aparece una línea:

> Job {jobId} — estado: {queued | running | completed | failed} ({etapa actual, si aplica})

Las 7 etapas posibles que puede mostrar como "etapa actual" mientras `running`: `normalize`,
`segment`, `classify`, `extract_entities`, `generate_backlog`, `estimate`, `validate`. El
frontend hace polling cada 2 segundos hasta que el estado sea terminal (`completed` o `failed`).
Si falla, se muestra el mensaje de error debajo en rojo.

Cuando el estado es `completed`, en la misma línea (a la derecha) aparecen los **botones de
exportación** (ver 4.3.4).

#### 4.3.3 Vista del backlog (jerarquía de tarjetas) — el corazón de la pantalla

Estructura: **Épicas** (colapsables, expandidas por defecto) → **Features** (tarjetas anidadas,
con un borde de acento azul a la izquierda) → **Historias de usuario** (tarjetas anidadas dentro
de cada feature).

**Cada nivel (épica/feature/historia) tiene, en su encabezado, un badge de estado:**
- 🟡 **Borrador** (`draft`)
- 🟢 **Aprobado** (`approved`)
- 🔴 **Descartado** (`discarded`, con texto tachado)

**Cada nivel tiene los mismos tres botones de acción, siempre visibles:**
- **"Editar"** → cambia el bloque a modo edición (inputs en vez de texto), y el botón se
  convierte en **"Guardar"** + **"Cancelar"**.
- **"Aprobar"** → cambia el estado a `approved` (deshabilitado si ya está aprobado).
- **"Descartar"** → cambia el estado a `discarded` (deshabilitado si ya está descartado).

**Épica** (`<details>` colapsable, abierta por defecto):
- Encabezado (siempre visible, clickeable para colapsar): título + badge de estado.
- Cuerpo (colapsable): **"Título:"** + **"Descripción:"** (editables), botones de acción, y
  dentro, la lista de sus features.

**Feature** (tarjeta con acento azul):
- **"Título:"** + **"Descripción:"** (editables), badge de estado, botones de acción.
- Dentro, la lista de sus historias de usuario.

**Historia de usuario** (la tarjeta más rica en contenido):
- **Título de la tarea** (editable, campo de texto corto, encabezado de la tarjeta).
- Tres líneas etiquetadas (formato historia de usuario clásico), cada una editable:
  - **"Como:"** {rol/persona}
  - **"Quiero:"** {la funcionalidad}
  - **"Para:"** {el beneficio/razón}
- **"Criterios de aceptación"** — lista numerada (1, 2, 3…), cada ítem es "Dado {condición},
  cuando {acción}, entonces {resultado}". En modo edición: cada criterio tiene tres campos de
  texto cortos (dado/cuando/entonces) más un botón **"✕"** para eliminarlo, y abajo un link
  **"+ agregar criterio"** para añadir uno nuevo vacío.
- **"Subtareas"** — lista numerada, de solo lectura por ahora: `[disciplina] título`. Disciplinas
  posibles: `frontend`, `backend`, `database`, `infrastructure`, `qa`, `design`.
- **"Estimación:"** — de solo lectura: story points (escala Fibonacci: 1, 2, 3, 5, 8, 13) +
  justificación en una frase.
- **"⚠ Riesgos:"** y **"❓ Preguntas abiertas:"** — de solo lectura, solo aparecen si hay alguno.
- **"Ver fuente (N)"** — colapsable (`<details>`), al expandir muestra la lista de citas
  textuales exactas de la transcripción que respaldan esta historia, cada una con el hablante:
  *`Hablante: "cita textual exacta"`*. Esto es lo que hace único al producto — cada artefacto
  generado se puede verificar contra el texto original.

**Al final de toda la vista del backlog:** un colapsable **"Ver JSON crudo"** con el
`BacklogResult` completo en formato JSON, para quien quiera copiarlo o inspeccionarlo
directamente.

#### 4.3.4 Botones de exportación

Tres botones (aparecen solo cuando el job está `completed`):
- **"Exportar JSON"**
- **"Exportar Markdown"** (documento legible con toda la jerarquía, listo para pegar en Notion/Confluence/etc.)
- **"Exportar CSV"** (una fila por historia de usuario — útil para importar a Jira/Trello/Excel)

Cada uno descarga un archivo (`{meetingId}.json` / `.md` / `.csv`) directamente al hacer clic,
sin pantalla intermedia. Mientras descarga, el botón muestra "Exportando…".

#### 4.3.5 "Mis reuniones" (historial, barra lateral derecha)

Lista de todos los jobs que el usuario ha corrido antes (más reciente primero). Cada ítem es un
botón de ancho completo mostrando:
- El **Meeting ID**
- El **estado** (En cola / Procesando / Completado / Falló) + la **fecha/hora** de creación

Al hacer clic en un ítem: carga ese job en la columna principal (si sigue corriendo, retoma el
polling; si ya está completo, muestra directamente su backlog). Si no hay reuniones todavía,
muestra el texto: *"Todavía no hay reuniones procesadas."*

---

## 5. Flujo de usuario completo (para que el diseño respete la secuencia)

1. Usuario entra a `/`, hace clic en "Ir al dashboard".
2. Si no tiene sesión, Clerk lo manda a `/sign-in` (o `/sign-up`).
3. Ya en el dashboard: pega texto o sube un `.txt`, pone un Meeting ID, clic en "Generar backlog".
4. Ve el estado avanzando por las 7 etapas en tiempo casi real (polling cada 2s, toma entre
   ~30 segundos y unos pocos minutos según el tamaño de la transcripción).
5. Al completar, aparece el backlog jerárquico completo, listo para revisar.
6. Revisa historia por historia: expande "Ver fuente" para verificar contra la transcripción
   original, edita lo que no le convence, aprueba o descarta cada artefacto.
7. Exporta en el formato que necesite (Markdown para compartir, CSV para importar a su
   herramienta de gestión, JSON para uso programático).
8. Más adelante, vuelve al dashboard y puede retomar cualquier reunión anterior desde "Mis
   reuniones" sin tener que volver a correr el pipeline.

---

## 6. Qué NO existe todavía (para no diseñar pantallas que no tienen backend detrás)

- **No hay vista de "todas las historias aprobadas" ni tablero tipo kanban** — solo la vista
  jerárquica por reunión.
- **No hay colaboración multiusuario** — cada usuario solo ve sus propias reuniones (aislamiento
  estricto por `userId`), no hay compartir/invitar a otros.
- **No hay edición de subtareas, refinamiento (riesgos/dependencias/etc.) ni re-estimación
  manual** — esos tres bloques son de solo lectura hoy. Si el diseño quiere hacerlos editables,
  avísame, falta el backend para subtareas y refinamiento (la estimación si se puede re-generar
  pero no editar el número a mano todavía).
- **No hay página de configuración/perfil propia** — lo único de cuenta es el `UserButton` de
  Clerk.
- **Todo el backend es local (`localhost:3001`)** — no hay URLs de producción todavía; esto no
  afecta el diseño de las pantallas, solo es contexto de que estamos en fase de desarrollo.

---

## 7. Idioma y tono

Toda la interfaz está en español (México/Latinoamérica neutro). El tono es directo y funcional,
sin lenguaje corporativo — coherente con que el usuario final es un PO revisando su propio
trabajo, no un cliente externo.
