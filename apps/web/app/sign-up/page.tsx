"use client";

import { SignUp } from "@clerk/react";

/** See the note in app/sign-in/page.tsx about hash routing. */
export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <SignUp routing="hash" />
    </div>
  );
}
