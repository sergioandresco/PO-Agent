import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { dark } from "@clerk/themes";
import {
  ClerkProvider,
  Show,
  SignInButton,
  SignUpButton,
  UserButton,
} from "@clerk/nextjs";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const jetBrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Agente PO",
  description: "Backlog trazable a partir de transcripciones de reuniones",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="es"
      className={`${inter.variable} ${jetBrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-canvas text-text">
        <ClerkProvider
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
      </body>
    </html>
  );
}
