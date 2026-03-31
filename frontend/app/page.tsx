import Link from "next/link";

import { getPlanCheckoutUrl, SUBSCRIPTION_PLANS } from "../lib/plans";

export default function HomePage() {
  const cards = [
    {
      title: "Overview Dashboard",
      href: "/dashboard",
      description: "Executive metrics, plan mix, upgrade signals, and revenue snapshot.",
    },
    {
      title: "Research Rankings",
      href: "/rankings",
      description: "Breakthrough papers, emerging topics, and rising entities.",
    },
    {
      title: "Document Intelligence",
      href: "/documents",
      description: "Paper summaries and grounded Q&A.",
    },
    {
      title: "Graph Explorer",
      href: "/graph",
      description: "Interactive research network view placeholder.",
    },
  ];

  return (
    <main className="min-h-screen text-white">
      <div className="mx-auto max-w-7xl px-6 py-14">
        <div className="mb-14 grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="rounded-[2rem] border border-white/10 bg-[var(--panel)] p-8 shadow-2xl shadow-cyan-950/20">
            <p className="mb-3 text-sm uppercase tracking-[0.25em] text-cyan-400">
              Frontier Research Intelligence Platform
            </p>
            <h1 className="mb-4 text-4xl font-semibold tracking-tight sm:text-5xl">
              Research workflows for users, revenue visibility for operators.
            </h1>
            <p className="max-w-3xl text-lg text-slate-300">
              The platform now has a path for Clerk auth, Stripe-backed billing events,
              and admin analytics so product usage and sales numbers can be read together.
            </p>

            <div className="mt-8 flex flex-wrap gap-4">
              <Link
                href="/dashboard"
                className="rounded-full bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
              >
                Open business dashboard
              </Link>
              <a
                href={getPlanCheckoutUrl("student")}
                className="rounded-full border border-white/15 px-5 py-3 text-sm font-semibold text-white transition hover:border-cyan-300 hover:text-cyan-100"
              >
                Start Clerk auth flow
              </a>
            </div>
          </section>

          <section className="rounded-[2rem] border border-amber-300/20 bg-[linear-gradient(180deg,rgba(251,191,36,0.14),rgba(15,23,42,0.86))] p-8 shadow-xl shadow-amber-950/10">
            <p className="text-xs uppercase tracking-[0.3em] text-amber-200">
              Commercial spine
            </p>
            <div className="mt-6 grid gap-4">
              <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-4">
                <p className="text-sm text-slate-400">What is tracked</p>
                <p className="mt-2 text-lg font-medium text-white">
                  Plans, subscriptions, paid invoices, product activity, and upgrade signals.
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-4">
                <p className="text-sm text-slate-400">Who it serves</p>
                <p className="mt-2 text-lg font-medium text-white">
                  Founders, finance, sales, growth, and future admin operators.
                </p>
              </div>
            </div>
          </section>
        </div>

        <div className="mb-14">
          <p className="mb-4 text-sm uppercase tracking-[0.25em] text-amber-200">
            Auth and billing launch paths
          </p>
          <div className="grid gap-6 lg:grid-cols-3">
            {SUBSCRIPTION_PLANS.map((plan) => (
              <a
                key={plan.code}
                href={getPlanCheckoutUrl(plan.code)}
                className="rounded-[1.75rem] border border-white/10 bg-[var(--panel)] p-6 transition hover:-translate-y-1 hover:border-cyan-300/40"
              >
                <p className="text-sm uppercase tracking-[0.25em] text-cyan-300">
                  {plan.name}
                </p>
                <h2 className="mt-3 text-3xl font-semibold">{plan.price}</h2>
                <p className="mt-3 text-sm text-slate-300">{plan.description}</p>
                <p className="mt-6 text-sm font-medium text-cyan-200">
                  Open Clerk sign up and plan capture
                </p>
              </a>
            ))}
          </div>
        </div>

        <div className="mb-12">
          <p className="mb-3 text-sm uppercase tracking-[0.25em] text-cyan-400">
            Frontier Research Intelligence Platform
          </p>
          <h2 className="mb-4 text-3xl font-semibold tracking-tight sm:text-4xl">
            Product surfaces
          </h2>
          <p className="max-w-3xl text-lg text-slate-300">
            Explore breakthrough candidates, emerging fields, rising researchers, institution momentum,
            and document-level AI summaries in one interface.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          {cards.map((card) => (
            <Link
              key={card.href}
              href={card.href}
              className="rounded-2xl border border-white/10 bg-[var(--panel)] p-6 shadow-lg transition hover:border-cyan-500 hover:bg-slate-900/80"
            >
              <h2 className="mb-2 text-xl font-medium">{card.title}</h2>
              <p className="text-sm text-slate-400">{card.description}</p>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
