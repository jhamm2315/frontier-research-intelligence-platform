import type { Metadata } from "next";
import Link from "next/link";

import { API_BASE } from "../lib/api";
import "./globals.css";


export const metadata: Metadata = {
  title: "Frontier Research Intelligence",
  description: "Research product, billing, and business analytics control center.",
};

const navigation = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/rankings", label: "Rankings" },
  { href: "/documents", label: "Documents" },
  { href: "/graph", label: "Graph" },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[var(--bg)] text-[var(--ink)] antialiased">
        <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.16),_transparent_22%),radial-gradient(circle_at_top_right,_rgba(251,191,36,0.12),_transparent_24%),linear-gradient(180deg,_rgba(15,23,42,0.16),_transparent_28%)]" />
        <div className="relative">
          <header className="border-b border-white/10 bg-slate-950/70 backdrop-blur">
            <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-6 py-5">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-cyan-300">
                  MINT Ops Layer
                </p>
                <p className="text-lg font-semibold text-white">
                  Frontier Research Intelligence
                </p>
              </div>

              <nav className="hidden items-center gap-5 text-sm text-slate-300 md:flex">
                {navigation.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="transition hover:text-white"
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>

              <a
                href={`${API_BASE}/plans/student`}
                className="rounded-full border border-cyan-400/40 bg-cyan-400/10 px-4 py-2 text-sm font-medium text-cyan-100 transition hover:border-cyan-300 hover:bg-cyan-300/20"
              >
                Launch Clerk + Billing
              </a>
            </div>
          </header>

          {children}
        </div>
      </body>
    </html>
  );
}
