"use client";

import { useEffect, useState } from "react";

import { fetchApi } from "../../lib/api";

type OverviewResponse = {
  window_days: number;
  totals: {
    profiles: number;
    customers: number;
    paid_customers: number;
    active_subscriptions: number;
    transactions: number;
    mrr_cents: number;
    revenue_cents: number;
    searches: number;
    views: number;
    compares: number;
    uploads: number;
  };
  plan_mix: Array<{ plan_code: string; count: number }>;
  upgrade_candidates: Array<{
    profile_id: string;
    current_plan_code: string;
    best_fit_upgrade_plan: string | null;
    upgrade_propensity_score: number;
    total_revenue_cents: number;
    profiles?: { email?: string; full_name?: string; clerk_user_id?: string };
  }>;
  recent_transactions: Array<{
    stripe_invoice_id?: string;
    amount_total_cents: number;
    status: string;
    currency: string;
    collected_at?: string;
  }>;
};

export default function DashboardPage() {
  const [apiStatus, setApiStatus] = useState("Checking...");
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchApi<{ message: string }>("/")
      .then((data) => setApiStatus(data.message || "API online"))
      .catch(() => setApiStatus("API unavailable"));

    fetchApi<OverviewResponse>("/admin/dashboard/overview")
      .then((data) => setOverview(data))
      .catch((err: Error) => setError(err.message));
  }, []);

  const cards = overview
    ? [
        { label: "Profiles", value: overview.totals.profiles.toLocaleString() },
        { label: "Paid customers", value: overview.totals.paid_customers.toLocaleString() },
        { label: "MRR", value: `$${(overview.totals.mrr_cents / 100).toFixed(2)}` },
        { label: "Revenue window", value: `$${(overview.totals.revenue_cents / 100).toFixed(2)}` },
        { label: "Searches", value: overview.totals.searches.toLocaleString() },
        { label: "Views", value: overview.totals.views.toLocaleString() },
      ]
    : [];

  return (
    <main className="min-h-screen px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl">
        <h1 className="mb-2 text-3xl font-semibold">Overview Dashboard</h1>
        <p className="mb-8 text-slate-400">
          Executive summary across product activity, revenue, plan mix, and upgrade opportunities.
        </p>

        <div className="mb-8 rounded-2xl border border-white/10 bg-[var(--panel)] p-6">
          <h2 className="mb-2 text-lg font-medium">Backend Status</h2>
          <p className="text-cyan-400">{apiStatus}</p>
        </div>

        {error ? (
          <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 p-6 text-rose-100">
            Dashboard data is not available yet. {error}
          </div>
        ) : null}

        {overview ? (
          <>
            <div className="mb-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {cards.map((card) => (
                <div
                  key={card.label}
                  className="rounded-2xl border border-white/10 bg-[var(--panel)] p-6"
                >
                  <p className="text-sm uppercase tracking-[0.2em] text-slate-400">
                    {card.label}
                  </p>
                  <p className="mt-3 text-3xl font-semibold text-white">{card.value}</p>
                </div>
              ))}
            </div>

            <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
              <section className="rounded-2xl border border-white/10 bg-[var(--panel)] p-6">
                <h2 className="text-lg font-medium text-white">Plan Mix</h2>
                <div className="mt-5 space-y-4">
                  {overview.plan_mix.map((row) => (
                    <div key={row.plan_code}>
                      <div className="mb-2 flex items-center justify-between text-sm text-slate-300">
                        <span className="uppercase tracking-[0.2em]">{row.plan_code}</span>
                        <span>{row.count}</span>
                      </div>
                      <div className="h-2 rounded-full bg-slate-800">
                        <div
                          className="h-2 rounded-full bg-cyan-400"
                          style={{
                            width: `${Math.max(10, (row.count / Math.max(overview.totals.customers || 1, 1)) * 100)}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <section className="rounded-2xl border border-white/10 bg-[var(--panel)] p-6">
                <h2 className="text-lg font-medium text-white">Upgrade Candidates</h2>
                <div className="mt-5 space-y-4">
                  {overview.upgrade_candidates.length ? (
                    overview.upgrade_candidates.map((candidate) => (
                      <div
                        key={candidate.profile_id}
                        className="rounded-2xl border border-white/10 bg-slate-950/30 p-4"
                      >
                        <div className="flex items-center justify-between gap-4">
                          <div>
                            <p className="font-medium text-white">
                              {candidate.profiles?.full_name || candidate.profiles?.email || candidate.profile_id}
                            </p>
                            <p className="text-sm text-slate-400">
                              {candidate.current_plan_code} to {candidate.best_fit_upgrade_plan || "stay"}
                            </p>
                          </div>
                          <p className="text-xl font-semibold text-cyan-300">
                            {candidate.upgrade_propensity_score}
                          </p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-slate-400">No upgrade candidates yet.</p>
                  )}
                </div>
              </section>
            </div>

            <section className="mt-6 rounded-2xl border border-white/10 bg-[var(--panel)] p-6">
              <h2 className="text-lg font-medium text-white">Recent Revenue Events</h2>
              <div className="mt-5 space-y-3">
                {overview.recent_transactions.length ? (
                  overview.recent_transactions.map((transaction, index) => (
                    <div
                      key={`${transaction.stripe_invoice_id || "txn"}-${index}`}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-slate-950/30 px-4 py-3 text-sm"
                    >
                      <span className="text-slate-300">{transaction.status}</span>
                      <span className="font-medium text-white">
                        ${(transaction.amount_total_cents / 100).toFixed(2)} {transaction.currency.toUpperCase()}
                      </span>
                      <span className="text-slate-400">
                        {transaction.collected_at
                          ? new Date(transaction.collected_at).toLocaleString()
                          : "Pending timestamp"}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-400">No transactions recorded in this window.</p>
                )}
              </div>
            </section>
          </>
        ) : null}
      </div>
    </main>
  );
}
