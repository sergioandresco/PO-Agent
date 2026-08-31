"use client";

import { SignIn } from "@clerk/react";

/**
 * Hash routing keeps every step of the sign-in flow (factors, MFA, reset) on this
 * single URL. A static export cannot prerender Clerk's nested catch-all routes,
 * so path routing would 404 on the second step.
 */
export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignIn routing="hash" />
    </div>
  );
}
