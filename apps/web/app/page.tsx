import Link from "next/link";

export default function Home() {
  return (
    <main className="flex-1 flex flex-col items-center justify-center gap-4 p-8 text-center">
      <h1 className="text-3xl font-semibold">Agente PO</h1>
      <p className="max-w-md text-sm text-gray-500">
        Convierte la transcripción de una reunión en un backlog trazable:
        épicas, historias de usuario y criterios de aceptación, cada uno
        respaldado por el fragmento exacto de la transcripción que lo origina.
      </p>
      <Link
        href="/dashboard"
        className="rounded-full bg-foreground text-background px-4 py-2 text-sm font-medium"
      >
        Ir al dashboard
      </Link>
    </main>
  );
}
