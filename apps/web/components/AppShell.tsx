"use client";

import type { ReactNode } from "react";
import { useRouter } from "next/navigation";
import { dark } from "@clerk/themes";
import {
  ClerkProvider,
  Show,
  SignInButton,
  SignUpButton,
  UserButton,
} from "@clerk/react";

/**
 * Client-side Clerk shell.
 *
 * The App Router build of `@clerk/nextjs` registers React Server Actions, which
 * `output: "export"` rejects outright. `@clerk/react` is the same SDK without the
 * server half, so it works in a fully static bundle. Trade-off: the session is
 * resolved in the browser, so route protection is client-side (see app/dashboard).
 * The authoritative check stays server-side, in the API Gateway authorizer.
 */
const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ?? "";

export function AppShell({ children }: { children: ReactNode }) {
  const router = useRouter();

  return (
    <ClerkProvider
      publishableKey={publishableKey}
      routerPush={(to) => router.push(to)}
      routerReplace={(to) => router.replace(to)}
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
      signInFallbackRedirectUrl="/dashboard"
      signUpFallbackRedirectUrl="/dashboard"
      appearance={{
        theme: dark,
        variables: {
          colorPrimary: "#9184d9",
          colorBackground: "#161826",
          colorForeground: "#e9e9ed",
          borderRadius: "8px",
          fontFamily: "Inter, system-ui, sans-serif",
        },
      }}
    >
      <header className="flex items-center gap-3 border-b border-border-soft px-7 py-3">
        <span className="inline-flex h-[26px] w-[26px] items-center justify-center rounded-[7px] font-mono text-[11px] text-accent-soft shadow-[inset_0_0_0_1px_var(--color-accent)]">
          PO
        </span>
        <span className="text-[15px] font-medium tracking-[-0.01em]">
          Agente PO
        </span>
        <div className="ml-auto flex items-center gap-3">
          <Show when="signed-out">
            <SignInButton />
            <SignUpButton />
          </Show>
          <Show when="signed-in">
            <UserButton />
          </Show>
        </div>
      </header>
      {children}
    </ClerkProvider>
  );
}
