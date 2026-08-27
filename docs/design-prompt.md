Adjunto el contexto funcional completo de una aplicación web ya construida y funcionando
(`design-context.md`): un "Agente PO" que convierte transcripciones de reuniones en un backlog
trazable (épicas, features, historias de usuario), que un Product Owner revisa, edita, aprueba
o descarta.

Necesito que diseñes la identidad visual y la experiencia de esta app — **no un producto nuevo,
ni pantallas nuevas**: el flujo, los botones y los datos que se muestran ya están definidos en
el documento adjunto, respétalos tal cual. Lo que falta es diseño: layout, tipografía, color,
jerarquía visual, y cómo hacer que una vista con tanta información anidada (épica → feature →
historia, cada una con criterios de aceptación, subtareas, estimación y fuente) se sienta clara
y no abrumadora.

**Contexto del usuario:** un Product Owner o líder técnico, revisando su propio trabajo — no un
cliente externo. Necesita confiar en el resultado rápido: ver de un vistazo qué está aprobado,
qué falta revisar, y poder verificar cualquier historia contra la transcripción original sin
fricción.

**Restricciones técnicas (para que el diseño sea implementable tal cual):**
- Se construye con Tailwind CSS (utility classes), sobre Next.js App Router. Nada de librerías
  de componentes pesadas — prefiero HTML semántico + Tailwind puro, o como mucho primitivas
  simples tipo Radix si hace falta accesibilidad (modales, tooltips).
- Tiene que funcionar en modo claro y oscuro.
- Tiene que ser responsive — hoy no lo es en absoluto, así que diseña también cómo se ve en
  mobile, especialmente la vista jerárquica de tarjetas y el layout de dos columnas del
  dashboard.
- Autenticación la maneja Clerk con sus propios componentes (`SignInButton`, `UserButton`,
  etc.) — se pueden tematizar con la prop `appearance`, pero no se rediseñan desde cero.

**Lo que necesito que entregues:**
1. Una dirección de identidad visual (paleta de color, tipografía, tono) — hoy no hay ninguna,
   partes de cero. Algo profesional pero no corporativo-genérico; el usuario confía en que la
   herramienta le ahorra trabajo, no en que se vea como un SaaS enterprise más.
2. Mockups de las pantallas reales descritas en el documento: home pública, y sobre todo el
   dashboard completo — formulario de carga, estado del job por etapas, la jerarquía de tarjetas
   (con sus tres estados: borrador/aprobado/descartado, y el modo edición), el historial de
   reuniones, y los botones de exportación.
3. Cómo resolver visualmente la densidad de información en la tarjeta de historia de usuario
   (título, como/quiero/para, criterios numerados, subtareas, estimación, riesgos, fuente
   colapsable) sin que se sienta un formulario burocrático.
4. Estados de carga/vacío: el job corriendo (con las 7 etapas), la lista de reuniones vacía, un
   job que falló.

No necesito la implementación en código todavía — con el diseño (mockups + guía de estilo) yo
me encargo de traducirlo al código real.
