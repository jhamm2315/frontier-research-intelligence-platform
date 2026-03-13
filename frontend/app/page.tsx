import Link from "next/link";

export default function HomePage() {
  const cards = [
    {
      title: "Overview Dashboard",
      href: "/dashboard",
      description: "Executive metrics, top signals, and platform summary.",
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
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto max-w-7xl px-6 py-14">
        <div className="mb-12">
          <p className="mb-3 text-sm uppercase tracking-[0.25em] text-cyan-400">
            Frontier Research Intelligence Platform
          </p>
          <h1 className="mb-4 text-4xl font-semibold tracking-tight sm:text-5xl">
            Scientific discovery intelligence, turned into a product.
          </h1>
          <p className="max-w-3xl text-lg text-slate-300">
            Explore breakthrough candidates, emerging fields, rising researchers,
            institution momentum, and document-level AI summaries in one interface.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          {cards.map((card) => (
            <Link
              key={card.href}
              href={card.href}
              className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-lg transition hover:border-cyan-500 hover:bg-slate-900/80"
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
