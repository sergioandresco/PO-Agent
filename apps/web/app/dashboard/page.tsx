import { currentUser } from "@clerk/nextjs/server";

export default async function DashboardPage() {
  const user = await currentUser();

  return (
    <main className="flex-1 flex flex-col gap-4 p-8">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p className="text-sm text-gray-500">
        Sesión activa: {user?.primaryEmailAddress?.emailAddress ?? user?.id}
      </p>
      <p className="text-sm text-gray-400">
        Aquí irá la carga de transcripciones y el seguimiento de jobs (paso 6
        del plan de construcción).
      </p>
    </main>
  );
}
