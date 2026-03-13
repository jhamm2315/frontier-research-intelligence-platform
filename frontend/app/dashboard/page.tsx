"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default function DashboardPage() {
  const [apiStatus, setApiStatus] = useState("Checking...");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/")
      .then((res) => res.json())
      .then((data) => setApiStatus(data.message || "API online"))
      .catch(() => setApiStatus("API unavailable"));
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-white">
      <div className="mx-auto max-w-7xl">
        <h1 className="mb-2 text-3xl font-semibold">Overview Dashboard</h1>
        <p className="mb-8 text-slate-400">
          Executive summary and first-pass platform visuals.
        </p>

        <div className="mb-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="mb-2 text-lg font-medium">Backend Status</h2>
          <p className="text-cyan-400">{apiStatus}</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="mb-4 text-lg font-medium">Platform Signals</h2>
          <Plot
            data={[
              {
                type: "bar",
                x: ["Works", "Authors", "Institutions", "Topics", "Documents"],
                y: [191, 1853, 689, 1096, 3],
              },
            ]}
            layout={{
              title: "Current Platform Coverage",
              paper_bgcolor: "#0f172a",
              plot_bgcolor: "#0f172a",
              font: { color: "#ffffff" },
              margin: { l: 40, r: 20, t: 50, b: 40 },
            }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: "100%", height: "420px" }}
          />
        </div>
      </div>
    </main>
  );
}
