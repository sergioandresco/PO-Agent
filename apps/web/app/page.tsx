import Link from "next/link";

export default function Home() {
  return (
    <main className="relative grid flex-1 grid-cols-1 items-start gap-8 px-6 pt-14 pb-16 md:grid-cols-[1fr_380px] md:gap-12 md:px-[68px] md:pt-[104px] md:pb-[112px]">
      <div className="flex flex-col items-start gap-7">
        <span className="font-mono text-[11.5px] tracking-[.06em] text-text-5">
          TRANSCRIPCIÓN → BACKLOG TRAZABLE
        </span>
        <h1 className="m-0 max-w-[20ch] text-[40px] leading-[1.05] tracking-[-.03em] md:text-[60px]">
          Agente PO
        </h1>
        <p className="m-0 max-w-[52ch] text-[17px] leading-[1.6] text-text-2 [text-wrap:pretty]">
          Convierte la transcripción de una reunión en un backlog trazable:
          épicas, historias de usuario y criterios de aceptación, cada uno
          respaldado por el fragmento exacto de la transcripción que lo
          origina.
        </p>
        <Link
          href="/dashboard"
          className="inline-flex h-[42px] items-center gap-2 rounded-lg px-5 text-[14.5px] font-medium text-accent-soft shadow-[inset_0_0_0_1px_var(--color-accent)] transition-colors hover:bg-accent-wash"
        >
          Ir al dashboard <span className="font-mono">→</span>
        </Link>
      </div>
      <div
        className="hidden flex-col gap-2.5 pt-3 font-mono text-[12.5px] leading-[1.7] text-text-6 opacity-85 md:flex"
        style={{ maskImage: "linear-gradient(to bottom, #000 40%, transparent)" }}
      >
        <span>[00:00:03] Ana (Product Manager):</span>
        <span className="pl-3.5">
          necesitamos que el checkout recuerde la tarjeta
        </span>
        <span>[00:00:21] Luis (Tech Lead):</span>
        <span className="pl-3.5">
          el servicio de tokenización ya existe, es reusar
        </span>
        <span>[00:00:44] Ana (Product Manager):</span>
        <span className="pl-3.5">si la rechazan hay que pedir CVV otra vez</span>
        <span>[00:01:02] Mara (QA):</span>
        <span className="pl-3.5">¿y en compra como invitado?</span>
      </div>
    </main>
  );
}
