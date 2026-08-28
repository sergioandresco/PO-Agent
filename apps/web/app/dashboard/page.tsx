"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@clerk/react";
import { TranscriptPipelineForm } from "@/components/TranscriptPipelineForm";

/**
 * Client-side route guard.
 *
 * The static export has no server, so there is no proxy/middleware to protect
 * this route. Clerk resolves the session in the browser; until it does we render
 * a neutral shell, and unauthenticated visitors are redirected to /sign-in.
 * The real authorization boundary is the API: every request carries the Clerk JWT
 * and the backend authorizer validates it.
 */
export default function DashboardPage() {
  const { isLoaded, isSignedIn, user } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      router.replace("/sign-in");
    }
  }, [isLoaded, isSignedIn, router]);

  if (!isLoaded || !isSignedIn) {
    return (
      <main className="flex-1">
        <div className="flex items-center gap-3 border-b border-border-soft px-6 py-2.5">
          <span className="text-[13px] text-text-5">Dashboard</span>
          <span className="ml-auto text-[12.5px] text-text-5">
            Verificando sesion...
          </span>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1">
      <div className="flex items-center gap-3 border-b border-border-soft px-6 py-2.5">
        <span className="text-[13px] text-text-5">Dashboard</span>
        <span className="ml-auto text-[12.5px] text-text-5">
          Sesion activa:{" "}
          <span className="font-mono text-text-3">
            {user?.primaryEmailAddress?.emailAddress ?? user?.id}
          </span>
        </span>
      </div>
      <TranscriptPipelineForm />
    </main>
  );
}
