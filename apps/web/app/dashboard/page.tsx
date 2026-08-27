import { currentUser } from "@clerk/nextjs/server";
import { TranscriptPipelineForm } from "@/components/TranscriptPipelineForm";

export default async function DashboardPage() {
  const user = await currentUser();

  return (
    <main className="flex-1">
      <div className="flex items-center gap-3 border-b border-border-soft px-6 py-2.5">
        <span className="text-[13px] text-text-5">Dashboard</span>
        <span className="ml-auto text-[12.5px] text-text-5">
          Sesión activa:{" "}
          <span className="font-mono text-text-3">
            {user?.primaryEmailAddress?.emailAddress ?? user?.id}
          </span>
        </span>
      </div>
      <TranscriptPipelineForm />
    </main>
  );
}
