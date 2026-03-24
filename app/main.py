from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.api import documents, research, product

app = FastAPI(
    title="Frontier Research Intelligence Platform",
    version="0.1.0",
    description="Scientific discovery intelligence system with graph analytics, document intelligence, and research question answering."
)

app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(research.router, prefix="/research", tags=["Research"])
app.include_router(product.router, prefix="/product", tags=["Product"])


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="en" data-theme="dark">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Frontier Research Intelligence Platform</title>
        <style>
            :root {
                --bg: #07111f;
                --bg-elev: rgba(13, 23, 39, 0.88);
                --bg-soft: #0d1b2d;
                --card: rgba(13, 23, 39, 0.78);
                --card-strong: rgba(10, 19, 34, 0.92);
                --text: #eef6ff;
                --muted: #9fb3c8;
                --border: rgba(148, 163, 184, 0.16);
                --accent: #5eead4;
                --accent-strong: #22d3ee;
                --accent-dark: #0f172a;
                --success: #86efac;
                --warning: #fbbf24;
                --danger: #f87171;
                --shadow: 0 16px 40px rgba(0, 0, 0, 0.30);
                --hero-glow:
                    radial-gradient(circle at top left, rgba(34, 211, 238, 0.20), transparent 35%),
                    radial-gradient(circle at top right, rgba(94, 234, 212, 0.18), transparent 28%);
            }

            html[data-theme="light"] {
                --bg: #f4f9ff;
                --bg-elev: rgba(255, 255, 255, 0.88);
                --bg-soft: #eef5fb;
                --card: rgba(255, 255, 255, 0.92);
                --card-strong: rgba(255, 255, 255, 0.98);
                --text: #0f172a;
                --muted: #516173;
                --border: rgba(15, 23, 42, 0.10);
                --accent: #14b8a6;
                --accent-strong: #0891b2;
                --accent-dark: #ecfeff;
                --success: #16a34a;
                --warning: #b45309;
                --danger: #dc2626;
                --shadow: 0 16px 40px rgba(15, 23, 42, 0.10);
                --hero-glow:
                    radial-gradient(circle at top left, rgba(20, 184, 166, 0.10), transparent 35%),
                    radial-gradient(circle at top right, rgba(8, 145, 178, 0.10), transparent 28%);
            }

            * {
                box-sizing: border-box;
            }

            html {
                scroll-behavior: smooth;
            }

            body {
                margin: 0;
                font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                background: var(--bg);
                color: var(--text);
                transition: background 0.25s ease, color 0.25s ease;
            }

            a {
                color: inherit;
                text-decoration: none;
            }

            .shell {
                min-height: 100vh;
                background: var(--hero-glow);
            }

            .topbar {
                position: sticky;
                top: 0;
                z-index: 40;
                backdrop-filter: blur(16px);
                background: var(--bg-elev);
                border-bottom: 1px solid var(--border);
            }

            .topbar-inner {
                max-width: 1600px;
                margin: 0 auto;
                padding: 16px 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 16px;
            }

            .brand-wrap {
                display: flex;
                align-items: center;
                gap: 14px;
            }

            .brand-badge {
                width: 44px;
                height: 44px;
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, var(--accent), var(--accent-strong));
                color: #03111a;
                font-weight: 800;
                box-shadow: var(--shadow);
            }

            .brand-copy h1 {
                margin: 0;
                font-size: 1rem;
                letter-spacing: 0.02em;
            }

            .brand-copy p {
                margin: 2px 0 0 0;
                font-size: 0.84rem;
                color: var(--muted);
            }

            .top-actions {
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
            }

            .ghost-btn, .primary-btn, .secondary-btn, .danger-btn {
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 10px 14px;
                font-size: 0.92rem;
                cursor: pointer;
                transition: 0.2s ease;
            }

            .ghost-btn {
                background: transparent;
                color: var(--text);
            }

            .ghost-btn:hover {
                background: rgba(148, 163, 184, 0.08);
            }

            .primary-btn {
                background: linear-gradient(135deg, var(--accent), var(--accent-strong));
                color: #03111a;
                border: none;
                font-weight: 700;
            }

            .primary-btn:hover {
                transform: translateY(-1px);
                filter: brightness(1.03);
            }

            .secondary-btn {
                background: var(--bg-soft);
                color: var(--text);
            }

            .secondary-btn:hover {
                border-color: var(--accent);
            }

            .danger-btn {
                background: rgba(248, 113, 113, 0.10);
                color: var(--danger);
                border-color: rgba(248, 113, 113, 0.25);
            }

            .danger-btn:hover {
                background: rgba(248, 113, 113, 0.16);
            }

            .hero {
                max-width: 1600px;
                margin: 0 auto;
                padding: 42px 24px 28px 24px;
                display: grid;
                grid-template-columns: 1.25fr 0.75fr;
                gap: 24px;
            }

            .hero-card, .hero-side {
                background: var(--card);
                border: 1px solid var(--border);
                border-radius: 24px;
                box-shadow: var(--shadow);
                backdrop-filter: blur(18px);
            }

            .hero-card {
                padding: 34px;
            }

            .hero-tag {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                font-size: 0.82rem;
                padding: 8px 12px;
                border-radius: 999px;
                background: rgba(34, 211, 238, 0.10);
                color: var(--accent-strong);
                border: 1px solid rgba(34, 211, 238, 0.18);
                margin-bottom: 18px;
            }

            .hero-card h2 {
                margin: 0;
                font-size: clamp(2rem, 3.6vw, 3.4rem);
                line-height: 1.04;
                letter-spacing: -0.03em;
            }

            .hero-card p {
                margin: 18px 0 0 0;
                max-width: 860px;
                color: var(--muted);
                font-size: 1.03rem;
                line-height: 1.75;
            }

            .hero-actions {
                display: flex;
                flex-wrap: wrap;
                gap: 12px;
                margin-top: 24px;
            }

            .hero-side {
                padding: 24px;
                display: flex;
                flex-direction: column;
                gap: 16px;
            }

            .stat-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
            }

            .stat-card {
                background: var(--bg-soft);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 16px;
            }

            .stat-card .label {
                font-size: 0.8rem;
                color: var(--muted);
                margin-bottom: 8px;
            }

            .stat-card .value {
                font-size: 1.45rem;
                font-weight: 800;
            }

            .hero-note {
                font-size: 0.92rem;
                color: var(--muted);
                line-height: 1.7;
            }

            .layout {
                max-width: 1600px;
                margin: 0 auto;
                padding: 0 24px 40px 24px;
                display: grid;
                grid-template-columns: 340px 1fr;
                gap: 24px;
            }

            .sidebar, .mainpanel {
                background: var(--card);
                border: 1px solid var(--border);
                border-radius: 24px;
                box-shadow: var(--shadow);
                backdrop-filter: blur(18px);
            }

            .sidebar {
                padding: 24px;
                height: fit-content;
                position: sticky;
                top: 92px;
            }

            .mainpanel {
                padding: 24px;
            }

            .sidebar h3, .mainpanel h2, .mainpanel h3 {
                margin-top: 0;
                color: var(--text);
            }

            .sidebar p, .mainpanel p, .mainpanel li {
                color: var(--muted);
                line-height: 1.7;
            }

            .nav-list {
                display: grid;
                gap: 10px;
                margin-top: 18px;
            }

            .nav-pill {
                padding: 12px 14px;
                border-radius: 14px;
                background: var(--bg-soft);
                border: 1px solid var(--border);
                color: var(--text);
                font-size: 0.92rem;
            }

            .nav-pill strong {
                display: block;
                margin-bottom: 4px;
            }

            .sample-group {
                margin-top: 24px;
            }

            .sample-btn {
                width: 100%;
                text-align: left;
                margin-top: 10px;
                padding: 12px 14px;
                border-radius: 14px;
                background: var(--bg-soft);
                border: 1px solid var(--border);
                color: var(--text);
                cursor: pointer;
            }

            .sample-btn:hover {
                border-color: var(--accent-strong);
            }

            .workflow-rail {
                display: grid;
                grid-template-columns: repeat(6, 1fr);
                gap: 10px;
                margin-bottom: 22px;
            }

            .workflow-step {
                background: var(--bg-soft);
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 12px;
                min-height: 92px;
            }

            .workflow-step .step {
                font-size: 0.75rem;
                color: var(--accent-strong);
                margin-bottom: 6px;
                font-weight: 700;
                letter-spacing: 0.03em;
            }

            .workflow-step .title {
                font-weight: 700;
                margin-bottom: 6px;
            }

            .workflow-step .desc {
                font-size: 0.84rem;
                color: var(--muted);
                line-height: 1.45;
            }

            .panel {
                background: var(--bg-soft);
                border: 1px solid var(--border);
                border-radius: 20px;
                padding: 20px;
                margin-top: 22px;
            }

            .section-heading {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 10px;
                flex-wrap: wrap;
            }

            .section-heading h2 {
                margin: 0;
                font-size: 1.15rem;
            }

            .row {
                display: grid;
                grid-template-columns: 1fr auto;
                gap: 12px;
                align-items: center;
            }

            .stack {
                display: grid;
                gap: 12px;
            }

            .input, .textarea, .select {
                width: 100%;
                border-radius: 14px;
                border: 1px solid var(--border);
                background: rgba(2, 6, 23, 0.75);
                color: var(--text);
                padding: 14px 16px;
                font-size: 0.96rem;
                outline: none;
            }

            html[data-theme="light"] .input,
            html[data-theme="light"] .textarea,
            html[data-theme="light"] .select {
                background: rgba(255, 255, 255, 0.85);
            }

            .textarea {
                min-height: 120px;
                resize: vertical;
            }

            .results {
                display: grid;
                gap: 14px;
                margin-top: 16px;
            }

            .result-card {
                background: var(--card);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 16px;
            }

            .meta {
                font-size: 0.84rem;
                color: var(--muted);
                margin-bottom: 8px;
            }

            .small {
                font-size: 0.9rem;
                color: var(--muted);
            }

            .doc-card {
                display: none;
                background: var(--card);
                border: 1px solid var(--border);
                border-radius: 22px;
                padding: 22px;
                margin-top: 24px;
            }

            .doc-card h2 {
                margin-top: 0;
                font-size: 1.55rem;
            }

            .docmeta {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
                margin-top: 16px;
            }

            .docmeta-item {
                background: var(--bg-soft);
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 14px;
            }

            .docmeta-item strong {
                display: block;
                font-size: 0.85rem;
                margin-bottom: 8px;
                color: var(--muted);
            }

            .summary-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
                margin-top: 18px;
            }

            .summary-section {
                background: var(--bg-soft);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 16px;
            }

            .summary-section h3 {
                margin: 0 0 10px 0;
                font-size: 1rem;
            }

            .summary-full {
                grid-column: 1 / -1;
            }

            .link {
                color: var(--accent-strong);
                word-break: break-all;
            }

            .status-pill {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 6px 10px;
                border-radius: 999px;
                font-size: 0.78rem;
                border: 1px solid var(--border);
                background: rgba(148, 163, 184, 0.08);
            }

            .status-pill.full {
                color: var(--success);
                border-color: rgba(134, 239, 172, 0.3);
                background: rgba(134, 239, 172, 0.08);
            }

            .status-pill.meta {
                color: var(--warning);
                border-color: rgba(251, 191, 36, 0.25);
                background: rgba(251, 191, 36, 0.08);
            }

            .status-pill.source {
                color: var(--accent-strong);
                border-color: rgba(34, 211, 238, 0.20);
                background: rgba(34, 211, 238, 0.08);
            }

            .qa-panel {
                margin-top: 24px;
            }

            .evidence {
                margin-top: 18px;
                display: grid;
                gap: 12px;
            }

            .evidence-item {
                background: var(--bg-soft);
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 14px;
            }

            .pill-row {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-top: 10px;
            }

            .topic-pill {
                font-size: 0.78rem;
                padding: 7px 10px;
                border-radius: 999px;
                background: rgba(34, 211, 238, 0.08);
                border: 1px solid rgba(34, 211, 238, 0.18);
                color: var(--accent-strong);
            }

            .connectors {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 12px;
                margin-top: 16px;
            }

            .connector-card {
                background: var(--bg-soft);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 16px;
            }

            .connector-card .title {
                font-weight: 700;
                margin-bottom: 6px;
            }

            .connector-card .desc {
                font-size: 0.88rem;
                color: var(--muted);
                line-height: 1.55;
            }

            .coming-soon {
                margin-top: 10px;
                font-size: 0.78rem;
                color: var(--accent-strong);
            }

            .toolbar {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-top: 14px;
            }

            .split {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
            }

            .list-card {
                background: var(--bg-soft);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 14px;
                min-height: 160px;
            }

            .list-card h3 {
                margin-top: 0;
                margin-bottom: 10px;
            }

            .list-item {
                padding: 10px 12px;
                border-radius: 12px;
                background: var(--card-strong);
                border: 1px solid var(--border);
                margin-top: 8px;
            }

            .source-badge {
                display: inline-block;
                padding: 5px 9px;
                border-radius: 999px;
                font-size: 0.75rem;
                border: 1px solid var(--border);
                background: rgba(94, 234, 212, 0.08);
                color: var(--accent-strong);
                margin-bottom: 8px;
            }

            .filter-bar {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-top: 14px;
            }

            .filter-chip {
                padding: 8px 11px;
                border-radius: 999px;
                border: 1px solid var(--border);
                background: var(--card);
                color: var(--text);
                cursor: pointer;
                font-size: 0.82rem;
            }

            .filter-chip.active {
                background: rgba(34, 211, 238, 0.10);
                border-color: rgba(34, 211, 238, 0.25);
                color: var(--accent-strong);
            }

            .modal-backdrop {
                display: none;
                position: fixed;
                inset: 0;
                background: rgba(2, 6, 23, 0.55);
                backdrop-filter: blur(6px);
                z-index: 100;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }

            .modal {
                width: min(520px, 100%);
                background: var(--card);
                border: 1px solid var(--border);
                border-radius: 24px;
                box-shadow: var(--shadow);
                padding: 24px;
            }

            .modal h3 {
                margin-top: 0;
            }

            .modal-actions {
                display: flex;
                gap: 10px;
                justify-content: flex-end;
                margin-top: 16px;
            }

            .toast {
                position: fixed;
                right: 20px;
                bottom: 20px;
                z-index: 200;
                max-width: 380px;
                background: var(--card-strong);
                border: 1px solid var(--border);
                border-radius: 16px;
                box-shadow: var(--shadow);
                padding: 14px 16px;
                display: none;
            }

            @media (max-width: 1200px) {
                .hero {
                    grid-template-columns: 1fr;
                }
                .connectors {
                    grid-template-columns: 1fr 1fr;
                }
                .docmeta {
                    grid-template-columns: 1fr 1fr;
                }
                .workflow-rail {
                    grid-template-columns: repeat(3, 1fr);
                }
                .split {
                    grid-template-columns: 1fr;
                }
            }

            @media (max-width: 980px) {
                .layout {
                    grid-template-columns: 1fr;
                }
                .sidebar {
                    position: static;
                }
                .summary-grid {
                    grid-template-columns: 1fr;
                }
            }

            @media (max-width: 640px) {
                .topbar-inner,
                .hero,
                .layout {
                    padding-left: 16px;
                    padding-right: 16px;
                }
                .docmeta {
                    grid-template-columns: 1fr;
                }
                .connectors {
                    grid-template-columns: 1fr;
                }
                .row {
                    grid-template-columns: 1fr;
                }
                .workflow-rail {
                    grid-template-columns: 1fr 1fr;
                }
            }
        </style>
        <script
            async
            crossorigin="anonymous"
            data-clerk-publishable-key="pk_test_bWVycnktaW5zZWN0LTkyLmNsZXJrLmFjY291bnRzLmRldiQ"
            src="https://cdn.jsdelivr.net/npm/@clerk/clerk-js@latest/dist/clerk.browser.js"></script>
    </head>
    <body>
        <div class="shell">
            <div class="topbar">
                <div class="topbar-inner">
                    <div class="brand-wrap">
                        <div class="brand-badge">FR</div>
                        <div class="brand-copy">
                            <h1>Frontier Research Intelligence</h1>
                            <p>AI-assisted research discovery, summarization, citation, and paper chat</p>
                        </div>
                    </div>
                    <div class="top-actions">
                        <button class="ghost-btn" onclick="toggleTheme()">Toggle Light / Dark</button>
                        <div id="clerk-user-button"></div>
                        <button class="ghost-btn" id="signInBtn" onclick="openAuthModal()">Sign In</button>
                        <button class="ghost-btn" onclick="scrollToPricing()">Pricing Plans</button>
                        <button class="primary-btn" onclick="document.getElementById('paperSearch').focus()">Start Exploring</button>
                    </div>
                </div>
            </div>

            <section class="hero">
                <div class="hero-card">
                    <div class="hero-tag">AI research copilot • student-first • source-grounded</div>
                    <h2>The smart research paper explorer built for students, analysts, and researchers.</h2>
                    <p>
                        Search your platform catalog, ingest open research from arXiv, explore institutional sources, review AI-generated summaries,
                        copy citations in multiple formats, save papers into your workspace, and begin drafting your own white paper or research paper
                        inside the platform.
                    </p>
                    <div class="hero-actions">
                        <button class="primary-btn" onclick="document.getElementById('paperSearch').focus()">Search Platform Papers</button>
                        <button class="secondary-btn" onclick="document.getElementById('arxivSearch').focus()">Search arXiv</button>
                        <button class="secondary-btn" onclick="document.getElementById('workspacePanel').scrollIntoView({behavior:'smooth'})">Open Workspace</button>
                    </div>
                </div>

                <div class="hero-side">
                    <div class="stat-grid">
                        <div class="stat-card">
                            <div class="label">Live Modes</div>
                            <div class="value">Hybrid</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Core Capabilities</div>
                            <div class="value">Search + Chat</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Paper Sources</div>
                            <div class="value">OpenAlex + arXiv</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Summary Engine</div>
                            <div class="value">Local LLM</div>
                        </div>
                    </div>
                    <div class="hero-note">
                        This is a full research operating system with Harvard, MIT, Stanford, Europe PMC, CORE, white paper ingestion, scholar works, writing tools, and premium workspace features.
                    </div>
                </div>
            </section>

            <div class="layout">
                <aside class="sidebar">
                    <h3>How to Use</h3>
                    <p>
                        The flow will guide users naturally through: search, open, summarize, cite, ask, save, and then draft your own paper
                        from the research you collect.
                    </p>

                    <div class="nav-list">
                        <div class="nav-pill">
                            <strong>1. Search the catalog</strong>
                            Find papers already available inside the platform.
                        </div>
                        <div class="nav-pill">
                            <strong>2. Search arXiv</strong>
                            Pull new papers into the platform when needed.
                        </div>
                        <div class="nav-pill">
                            <strong>3. Search institutions</strong>
                            Explore Harvard, MIT, Stanford, and other open sources.
                        </div>
                        <div class="nav-pill">
                            <strong>4. Open the paper</strong>
                            Review metadata, summaries, methods, findings, and links.
                        </div>
                        <div class="nav-pill">
                            <strong>5. Cite and save</strong>
                            Copy formatted citations and save papers into your workspace.
                        </div>
                        <div class="nav-pill">
                            <strong>6. Ask + draft</strong>
                            Ask grounded AI questions and build your own research paper next.
                        </div>
                    </div>

                    <div class="sample-group">
                        <h3>Try these prompts</h3>
                        <button class="sample-btn" onclick="setQuestion('What is this paper about?')">What is this paper about?</button>
                        <button class="sample-btn" onclick="setQuestion('What methods does this paper use?')">What methods does this paper use?</button>
                        <button class="sample-btn" onclick="setQuestion('What are the main findings?')">What are the main findings?</button>
                        <button class="sample-btn" onclick="setQuestion('How could this paper be used in practice?')">How could this paper be used in practice?</button>
                    </div>
                    
                    <div class="sample-group">
                        <h3>System Status</h3>
                        <div class="nav-list">
                            <div class="nav-pill"><strong>Search</strong>Ready</div>
                            <div class="nav-pill"><strong>Uploads</strong>Ready</div>
                            <div class="nav-pill"><strong>Builder</strong>Ready</div>
                            <div class="nav-pill"><strong>DOCX Export</strong>Ready</div>
                            <div class="nav-pill"><strong>PDF Export</strong>Ready</div>
                        </div>
                    </div>
                    
                </aside>
                    
                <main class="mainpanel">
                    <div class="workflow-rail">
                        <div class="workflow-step">
                            <div class="step">STEP 1</div>
                            <div class="title">Search</div>
                            <div class="desc">Find papers across platform, arXiv, and institutional sources.</div>
                        </div>
                        <div class="workflow-step">
                            <div class="step">STEP 2</div>
                            <div class="title">Open</div>
                            <div class="desc">Inspect metadata, summaries, source links, and topic tags.</div>
                        </div>
                        <div class="workflow-step">
                            <div class="step">STEP 3</div>
                            <div class="title">Summarize</div>
                            <div class="desc">Review AI plain-English and academic paper summaries.</div>
                        </div>
                        <div class="workflow-step">
                            <div class="step">STEP 4</div>
                            <div class="title">Cite</div>
                            <div class="desc">Copy APA, MLA, Chicago, BibTeX, or RIS instantly.</div>
                        </div>
                        <div class="workflow-step">
                            <div class="step">STEP 5</div>
                            <div class="title">Ask</div>
                            <div class="desc">Use grounded AI Q&A over the selected document.</div>
                        </div>
                        <div class="workflow-step">
                            <div class="step">STEP 6</div>
                            <div class="title">Build</div>
                            <div class="desc">Save papers, notes, and begin drafting your own report.</div>
                        </div>
                    </div>

                    <div class="panel">
                        <div class="section-heading">
                            <h2>Platform Search</h2>
                            <span class="small">Search papers already in your catalog</span>
                        </div>

                        <div class="filter-bar">
                            <button class="filter-chip active" onclick="setPlatformFilter('all', this)">All</button>
                            <button class="filter-chip" onclick="setPlatformFilter('full', this)">Full Document</button>
                            <button class="filter-chip" onclick="setPlatformFilter('metadata', this)">Metadata Only</button>
                        </div>

                        <div class="row" style="margin-top:14px;">
                            <input class="input" id="paperSearch" type="text" placeholder="Example: artificial intelligence, quantum, healthcare, classification" />
                            <button class="primary-btn" onclick="searchPapers()">Search Papers</button>
                        </div>

                        <div class="results" id="searchResultsContent"></div>
                    </div>

                    <div class="panel">
                        <div class="section-heading">
                            <h2>Live Source Connectors</h2>
                            <span class="small">Pull in new papers from open-access sources</span>
                        </div>

                        <div class="row">
                            <input class="input" id="arxivSearch" type="text" placeholder="Example: document classification" />
                            <button class="primary-btn" onclick="searchArxiv()">Search arXiv</button>
                        </div>

                        <div class="results" id="arxivResultsContent"></div>

                        <div class="connectors">
                            <div class="connector-card">
                                <div class="title">arXiv</div>
                                <div class="desc">Live search and ingest supported now.</div>
                            </div>
                            <div class="connector-card">
                                <div class="title">Institutional Search</div>
                                <div class="desc">Federated discovery across Harvard, MIT, Stanford, and LibraryCloud.</div>
                            </div>
                            <div class="connector-card">
                                <div class="title">White Papers</div>
                                <div class="desc">Upload and URL ingestion path can be connected next.</div>
                                <div class="coming-soon">Ready for next backend routes</div>
                            </div>
                            <div class="connector-card">
                                <div class="title">Future APIs</div>
                                <div class="desc">Europe PMC, CORE, Semantic Scholar, and Crossref.</div>
                                <div class="coming-soon">Planned</div>
                            </div>
                        </div>
                    </div>

                    <div class="panel">
                        <div class="section-heading">
                            <h2>Federated Institutional Search</h2>
                            <span class="small">Search across Harvard, MIT, Stanford, and Harvard LibraryCloud</span>
                        </div>

                        <div class="row">
                            <input class="input" id="federatedSearch" type="text" placeholder="Example: graph learning" />
                            <button class="primary-btn" onclick="searchFederated()">Search Sources</button>
                        </div>

                        <div class="results" id="federatedResultsContent"></div>
                    </div>

                    <section class="doc-card" id="paperCard">
                        <div class="section-heading">
                            <div>
                                <h2 id="paperTitle">Paper Title</h2>
                                <div class="small">Open, summarize, cite, ask, save, and build from this source.</div>
                            </div>
                            <span id="availabilityBadge" class="status-pill">Status</span>
                        </div>

                        <div class="docmeta">
                            <div class="docmeta-item"><strong>Author</strong><span id="paperAuthor"></span></div>
                            <div class="docmeta-item"><strong>Institution</strong><span id="paperInstitution"></span></div>
                            <div class="docmeta-item"><strong>Topic</strong><span id="paperTopic"></span></div>
                            <div class="docmeta-item"><strong>Citation</strong><span id="paperCitation"></span></div>
                            <div class="docmeta-item"><strong>Published</strong><span id="paperPublished"></span></div>
                            <div class="docmeta-item"><strong>Source</strong><span id="paperSource"></span></div>
                        </div>

                        <div class="pill-row" id="paperCategories"></div>

                        <div class="toolbar">
                            <button class="secondary-btn" onclick="saveCurrentPaper()">Save Paper</button>
                            <button class="secondary-btn" onclick="queueCurrentPaper()">Reading Queue</button>
                            <button class="secondary-btn" onclick="favoriteCurrentPaper()">Favorite</button>
                            <button class="secondary-btn" onclick="copyCitation('apa')">Copy APA</button>
                            <button class="secondary-btn" onclick="copyCitation('mla')">Copy MLA</button>
                            <button class="secondary-btn" onclick="copyCitation('chicago')">Copy Chicago</button>
                            <button class="secondary-btn" onclick="copyCitation('bibtex')">Copy BibTeX</button>
                            <button class="secondary-btn" onclick="copyCitation('ris')">Copy RIS</button>
                        </div>

                        <div class="summary-grid">
                            <div class="summary-section">
                                <h3>Plain English Summary</h3>
                                <p id="plainEnglishSummary"></p>
                            </div>
                            <div class="summary-section">
                                <h3>Academic Summary</h3>
                                <p id="academicSummary"></p>
                            </div>
                            <div class="summary-section">
                                <h3>Methods</h3>
                                <p id="methodsSummary"></p>
                            </div>
                            <div class="summary-section">
                                <h3>Results</h3>
                                <p id="resultsSummary"></p>
                            </div>
                            <div class="summary-section">
                                <h3>Limitations</h3>
                                <p id="limitationsSummary"></p>
                            </div>
                            <div class="summary-section">
                                <h3>Practical Applications</h3>
                                <p id="practicalApplications"></p>
                            </div>
                            <div class="summary-section">
                                <h3>Suggested Topics</h3>
                                <p id="suggestedTopics"></p>
                            </div>
                            <div class="summary-section">
                                <h3>Citation Guidance</h3>
                                <p id="citationGuidance"></p>
                            </div>
                            <div class="summary-section summary-full">
                                <h3>Source Link</h3>
                                <p><a id="paperPdfUrl" class="link" href="#" target="_blank"></a></p>
                            </div>
                        </div>
                    </section>

<div class="panel" id="multiPaperPanel">
    <div class="section-heading">
        <h2>Multi-Paper Comparison</h2>
        <span class="small">Select multiple papers and compare them with AI</span>
    </div>

    <div class="small" style="margin-bottom:10px;">
        Open papers from your search results, add them to compare, then generate a structured comparison.
    </div>

    <div class="toolbar">
        <button class="secondary-btn" onclick="addCurrentPaperToCompare()">Add Current Paper</button>
        <button class="danger-btn" onclick="clearComparePapers()">Clear Compare List</button>
    </div>

    <div class="list-card" style="margin-top:14px;">
        <h3>Selected Papers</h3>
        <div id="comparePapersList"></div>
    </div>

    <div class="stack" style="margin-top:16px;">
        <label>Comparison Focus</label>
        <textarea
            class="textarea"
            id="compareQuestion"
            placeholder="Example: Which of these papers is best for document classification in real-world business use?"
        ></textarea>
    </div>

    <div class="toolbar">
        <button class="primary-btn" onclick="runMultiPaperCompare()">Compare Papers</button>
    </div>

    <div id="compareResults" style="display:none; margin-top:16px;">
        <div class="summary-section">
            <h3>Comparison Summary</h3>
            <div id="compareSummary"></div>
        </div>

        <div class="summary-grid" style="margin-top:16px;">
            <div class="summary-section">
                <h3>Common Themes</h3>
                <div id="compareThemes"></div>
            </div>
            <div class="summary-section">
                <h3>Key Differences</h3>
                <div id="compareDifferences"></div>
            </div>
            <div class="summary-section">
                <h3>Methods Comparison</h3>
                <div id="compareMethods"></div>
            </div>
            <div class="summary-section">
                <h3>Results Comparison</h3>
                <div id="compareResultsText"></div>
            </div>
            <div class="summary-section">
                <h3>Limitations Comparison</h3>
                <div id="compareLimitations"></div>
            </div>
            <div class="summary-section">
                <h3>Recommended Paper</h3>
                <div id="compareRecommended"></div>
            </div>
            <div class="summary-section">
                <h3>Best for Students</h3>
                <div id="compareBestStudents"></div>
            </div>
            <div class="summary-section">
                <h3>Best for Researchers</h3>
                <div id="compareBestResearchers"></div>
            </div>
            <div class="summary-section summary-full">
                <h3>Best for Practical Use</h3>
                <div id="compareBestPractical"></div>
            </div>
        </div>
    </div>
</div>

<div class="panel qa-panel">
    <div class="section-heading">
        <h2>Ask the Paper</h2>
        <span class="small">Grounded AI Q&A using the selected full document</span>
    </div>
    <textarea class="textarea" id="question" placeholder="Ask about methods, findings, limitations, use cases, comparisons, or next steps."></textarea>
    <div class="toolbar">
        <button class="primary-btn" onclick="askQuestion()">Ask</button>
        <button class="secondary-btn" onclick="setExplainLevel('high_school')">Explain for High School</button>
        <button class="secondary-btn" onclick="setExplainLevel('college')">Explain for College</button>
        <button class="secondary-btn" onclick="setExplainLevel('graduate')">Explain for Graduate</button>
        <button class="secondary-btn" onclick="setExplainLevel('researcher')">Explain for Researcher</button>
    </div>

    <div id="qaPanel" style="display:none;">
        <div class="summary-section" style="margin-top:16px;">
            <h3>Answer</h3>
            <div id="answer"></div>
        </div>
        <div class="evidence" id="evidence"></div>
    </div>
</div>

<div class="panel" id="comparisonHistoryPanel">
    <div class="section-heading">
        <h2>Comparison History</h2>
        <span class="small">Save and reload prior multi-paper comparisons</span>
    </div>

                        <div class="toolbar">
                            <button class="secondary-btn" onclick="saveCurrentComparison()">Save Current Comparison</button>
                            <button class="secondary-btn" onclick="loadComparisonHistory()">Refresh History</button>
                        </div>

                        <div class="list-card" style="margin-top:14px;">
                            <h3>Saved Comparisons</h3>
                            <div id="comparisonHistoryList"></div>
                        </div>
                    </div>

                    <div class="panel" id="workspacePanel">
                        <div class="section-heading">
                            <h2>Workspace</h2>
                            <span class="small">API-backed workspace with local recent history</span>
                        </div>

                        <div class="split">
                            <div class="list-card">
                                <h3>Saved Papers</h3>
                                <div id="savedPapersList"></div>
                            </div>
                            <div class="list-card">
                                <h3>Reading Queue</h3>
                                <div id="readingQueueList"></div>
                            </div>
                            <div class="list-card">
                                <h3>Favorites</h3>
                                <div id="favoritesList"></div>
                            </div>
                            <div class="list-card">
                                <h3>Recent Papers</h3>
                                <div id="recentPapersList"></div>
                            </div>
                        </div>

                        <div class="stack" style="margin-top:16px;">
                            <label>Quick Note</label>
                            <textarea class="textarea" id="quickNote" placeholder="Add a note tied to the current paper..."></textarea>
                            <div class="toolbar">
                                <button class="secondary-btn" onclick="saveQuickNote()">Save Note</button>
                                <button class="secondary-btn" onclick="addCurrentPaperToDraft()">Add Current Paper to Draft</button>
                            </div>
                        </div>
                    </div>

                    <div class="panel">
                        <div class="section-heading">
                            <h2>Research Builder</h2>
                            <span class="small">Create your own white paper or research draft inside the platform</span>
                        </div>

                        <div class="stack">
                            <label>Project Title</label>
                            <input class="input" id="builderTitle" type="text" placeholder="Example: AI Trends in Document Classification" />

                            <label>Abstract / Thesis</label>
                            <textarea class="textarea" id="builderAbstract" placeholder="Describe the topic, thesis, or objective of your paper..."></textarea>

                            <label>Draft Section</label>
                            <textarea class="textarea" id="builderSection" placeholder="Draft an introduction, literature review, or argument. You can cite saved sources later."></textarea>
                        </div>

                        <div class="toolbar">
                            <button class="primary-btn" onclick="saveBuilderDraft()">Save Draft</button>
                            <button class="secondary-btn" onclick="copyBuilderMarkdown()">Copy as Markdown</button>
                            <button class="secondary-btn" onclick="copyBuilderHtml()">Copy as HTML</button>
                            <button class="secondary-btn" onclick="exportBuilderDocxStub()">Export DOCX</button>
                            <button class="secondary-btn" onclick="exportBuilderPdfStub()">Export PDF</button>
                        </div>

                        <div class="summary-section" style="margin-top:16px;">
                            <h3>Draft Preview</h3>
                            <div id="builderPreview" class="small">Your draft preview will appear here after saving.</div>
                        </div>
                    </div>

                    <div class="panel">
                        <div class="section-heading">
                            <h2>Upload Center</h2>
                            <span class="small">UI-ready for PDF, TXT, DOCX, and URL ingestion</span>
                        </div>

                        <div class="stack">
                            <label>Upload Local File</label>
                            <input class="input" id="uploadFileInput" type="file" />
                            <label>Ingest Public URL</label>
                            <input class="input" id="urlIngestInput" type="text" placeholder="Paste a public white paper or research URL" />
                        </div>

                        <div class="toolbar">
                            <button class="secondary-btn" onclick="handleLocalUploadStub()">Upload File</button>
                            <button class="secondary-btn" onclick="handleUrlIngestStub()">Ingest URL</button>
                        </div>
                        
                        <div class="list-card" style="margin-top:16px;">
                            <h3>Uploaded Sources</h3>
                            <div id="uploadedSourcesList"></div>
                        </div>

                        <div class="small" style="margin-top:10px;">
                            URL ingestion and browser file upload are now live.
                            </div>
                    </div>
                            
                        <div class="panel" id="pricingPanel">
                            <div class="section-heading">
                                <h2>Pricing</h2>
                                <span class="small">Choose the plan that fits your research workflow</span>
                            </div>

                            <div class="split">
                                <div class="list-card">
                                    <h3>Free</h3>
                                    <div class="small">A lightweight entry tier so anyone can use the platform</div>
                                    <ul>
                                        <li>5 searches/day</li>
                                        <li>1 arXiv ingest/day</li>
                                        <li>3 questions/day</li>
                                        <li>1 upload/day</li>
                                        <li>Basic paper viewing only</li>
                                    </ul>
                                    <div class="toolbar">
                                        <button class="secondary-btn" onclick="showToast('Free tier is active and available to all users.')">Use Free Tier</button>
                                    </div>
                                </div>

                                <div class="list-card">
                                    <h3>Student</h3>
                                    <div class="small">$2.99/month with a verified .edu email</div>
                                    <ul>
                                        <li>100 searches/day</li>
                                        <li>25 arXiv ingests/day</li>
                                        <li>100 questions/day</li>
                                        <li>20 uploads/day</li>
                                        <li>Expanded builder and exports</li>
                                    </ul>
                                    <div class="toolbar">
                                        <button class="primary-btn" onclick="openPricingCheckout('student')">Choose Student - $2.99/mo</button>
                                    </div>
                                </div>

                                <div class="list-card">
                                    <h3>Pro</h3>
                                    <div class="small">$9.99/month for advanced individual research workflows</div>
                                    <ul>
                                        <li>500 searches/day</li>
                                        <li>100 arXiv ingests/day</li>
                                        <li>500 questions/day</li>
                                        <li>100 uploads/day</li>
                                        <li>Priority export and larger workspace capacity</li>
                                    </ul>
                                    <div class="toolbar">
                                        <button class="primary-btn" onclick="openPricingCheckout('pro')">Choose Pro - $9.99/mo</button>
                                    </div>
                                </div>

                                <div class="list-card">
                                    <h3>Enterprise</h3>
                                    <div class="small">$14.99/month for power users, teams, and broader commercial use</div>
                                    <ul>
                                        <li>Unlimited-like high daily usage caps</li>
                                        <li>Highest upload and workspace limits</li>
                                        <li>Team-ready research workflows</li>
                                        <li>Priority support and export access</li>
                                        <li>Future advanced enterprise controls</li>
                                    </ul>
                                    <div class="toolbar">
                                        <button class="primary-btn" onclick="openPricingCheckout('enterprise')">Choose Enterprise - $14.99/mo</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>

        <div class="modal-backdrop" id="authModal">
            <div class="modal">
                <h3>Sign In</h3>
                <p class="small">
                    Sign in to your Frontier Research Intelligence workspace using the secure Clerk portal below.
                </p>
                <div id="clerk-sign-in"></div>
                <div class="modal-actions">
                    <button class="ghost-btn" onclick="closeAuthModal()">Close</button>
                </div>
            </div>
        </div>

        <div class="toast" id="toast"></div>

        <script>
            function applyTheme(theme) {
                document.documentElement.setAttribute("data-theme", theme);
                localStorage.setItem("frip-theme", theme);
            }

            function toggleTheme() {
                const current = document.documentElement.getAttribute("data-theme") || "dark";
                applyTheme(current === "dark" ? "light" : "dark");
            }

            (function initThemeEarly() {
                const stored = localStorage.getItem("frip-theme");
                applyTheme(stored || "dark");
            })();

            function scrollToPricing() {
                const panel = document.getElementById("pricingPanel");
                if (panel) {
                    panel.scrollIntoView({ behavior: "smooth", block: "start" });
                }
            }

            function closeAuthModal() {
                const modal = document.getElementById("authModal");
                if (modal) {
                    modal.style.display = "none";
                }
            }

            function openAuthModal() {
                const modal = document.getElementById("authModal");
                if (modal) {
                    modal.style.display = "flex";
                }

                const el = document.getElementById("clerk-sign-in");
                if (el) {
                    el.innerHTML = "<div class='small'>Loading secure Clerk sign-in...</div>";
                }

                const tryMount = () => {
                    if (window.Clerk) {
                        mountSignInFallback();
                        return true;
                    }
                    return false;
                };

                if (!tryMount()) {
                    let attempts = 0;
                    const maxAttempts = 20;
                    const intervalId = setInterval(() => {
                        attempts += 1;
                        if (tryMount() || attempts >= maxAttempts) {
                            clearInterval(intervalId);
                            if (!window.Clerk) {
                                const signInEl = document.getElementById("clerk-sign-in");
                                if (signInEl) {
                                    signInEl.innerHTML = "<div class='small'>Secure sign-in could not load yet. Refresh and try again.</div>";
                                }
                            }
                        }
                    }, 300);
                }
            }

            function mountSignInFallback() {
                const el = document.getElementById("clerk-sign-in");
                if (!el || !window.Clerk) return;

                el.innerHTML = "";
                window.Clerk.mountSignIn(el, {
                    appearance: {
                        elements: {
                            card: {
                                boxShadow: "none",
                                border: "1px solid rgba(148, 163, 184, 0.16)",
                                backgroundColor: "transparent"
                            }
                        }
                    }
                });
                el.dataset.mounted = "true";
            }

            function openPricingCheckout(planCode) {
                const labels = {
                    student: "Student plan selected: $2.99/month",
                    pro: "Pro plan selected: $9.99/month",
                    enterprise: "Enterprise plan selected: $14.99/month"
                };
                const message = labels[planCode] || `Plan selected: ${planCode}`;
                const toast = document.getElementById("toast");
                if (toast) {
                    toast.textContent = message;
                    toast.style.display = "block";
                    clearTimeout(window.__toastTimeout);
                    window.__toastTimeout = setTimeout(() => {
                        toast.style.display = "none";
                    }, 2600);
                }
            }

            async function initClerkFallback() {
                if (!window.Clerk) return;
                try {
                    await window.Clerk.load();
                    const signInBtn = document.getElementById("signInBtn");
                    const userButton = document.getElementById("clerk-user-button");

                    if (window.Clerk.user) {
                        if (userButton) {
                            userButton.innerHTML = "";
                            window.Clerk.mountUserButton(userButton);
                        }
                        if (signInBtn) {
                            signInBtn.style.display = "none";
                        }
                    } else if (signInBtn) {
                        signInBtn.style.display = "inline-flex";
                    }
                } catch (error) {
                    console.error("Clerk fallback init failed:", error);
                }
            }

            document.addEventListener("DOMContentLoaded", function () {
                initClerkFallback();
            });
        </script>
        <script>
            let currentDocumentId = null;
            let comparePaperIds = [];
            let currentPaperMeta = null;
            let currentPaperAi = null;
            let platformFilter = "all";
            let explainLevel = "college";
            const USER_ID = "demo_user";
            const USER_PLAN = "free";
            let currentProjectId = null;
            let lastComparisonPayload = null;

            const STORE_KEYS = {
                saved: "fri_saved_papers",
                queue: "fri_reading_queue",
                favorites: "fri_favorites",
                recents: "fri_recent_papers",
                notes: "fri_notes",
                builder: "fri_builder_draft"
            };
            
            const AppState = {
                user: {
                id: USER_ID,
                plan: USER_PLAN
            },
                paper: {
                meta: null,
                ai: null,
                documentId: null
            },
                project: {
                id: null
            },
                ui: {
                platformFilter: "all",
                explainLevel: "college"
            }
};

            function applyTheme(theme) {
                document.documentElement.setAttribute("data-theme", theme);
                localStorage.setItem("frip-theme", theme);
            }

            function toggleTheme() {
                const current = document.documentElement.getAttribute("data-theme") || "dark";
                applyTheme(current === "dark" ? "light" : "dark");
            }

            (function initTheme() {
                const stored = localStorage.getItem("frip-theme");
                applyTheme(stored || "dark");
            })();

            function openAuthModal() {
                const modal = document.getElementById("authModal");
                if (modal) {
                    modal.style.display = "flex";
                }

                const el = document.getElementById("clerk-sign-in");
                if (el) {
                    el.innerHTML = "<div class='small'>Loading secure Clerk sign-in...</div>";
                }

                const tryMount = () => {
                    if (window.Clerk) {
                        mountSignIn();
                        return true;
                    }
                    return false;
                };

                if (!tryMount()) {
                    let attempts = 0;
                    const maxAttempts = 20;
                    const intervalId = setInterval(() => {
                        attempts += 1;
                        if (tryMount() || attempts >= maxAttempts) {
                            clearInterval(intervalId);
                            if (!window.Clerk) {
                                const signInEl = document.getElementById("clerk-sign-in");
                                if (signInEl) {
                                    signInEl.innerHTML = "<div class='small'>Secure sign-in could not load yet. Refresh and try again.</div>";
                                }
                            }
                        }
                    }, 300);
                }
            }

            function closeAuthModal() {
                const modal = document.getElementById("authModal");
                if (modal) {
                    modal.style.display = "none";
                }
            }

            function fakeSignIn() {
                openAuthModal();
            }

            function setQuestion(text) {
                const el = document.getElementById("question");
                if (el) {
                    el.value = text;
                }
            }

            function setExplainLevel(level) {
                explainLevel = level;
                const questionBox = document.getElementById("question");
                if (!questionBox) return;

                const base = questionBox.value.trim();
                const fallback = "What is this paper about?";
                questionBox.value = `${base || fallback} Explain it for a ${level.replace("_", " ")} audience.`;
            }

            function escapeHtml(value) {
                return String(value ?? "")
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;");
            }

            function showToast(message) {
                const toast = document.getElementById("toast");
                if (!toast) return;
                toast.textContent = message;
                toast.style.display = "block";
                clearTimeout(window.__toastTimeout);
                window.__toastTimeout = setTimeout(() => {
                    toast.style.display = "none";
                }, 2600);
            }
            
            function setLoading(buttonEl, isLoading, loadingText = "Loading...") {
                        if (!buttonEl) return;

                        if (isLoading) {
                            if (!buttonEl.dataset.originalText) {
                                buttonEl.dataset.originalText = buttonEl.innerHTML;
                            }
                            buttonEl.innerHTML = loadingText;
                            buttonEl.disabled = true;
                            buttonEl.style.opacity = "0.75";
                        } else {
                            if (buttonEl.dataset.originalText) {
                                buttonEl.innerHTML = buttonEl.dataset.originalText;
                            }
                            buttonEl.disabled = false;
                            buttonEl.style.opacity = "1";
                        }
                    }

                    function handleError(message, error = null) {
                        console.error(message, error);
                        showToast(message);
                    }
                    
                  function scrollToPricing() {
                        const panel = document.getElementById("pricingPanel");
                        if (panel) {
                            panel.scrollIntoView({ behavior: "smooth", block: "start" });
                        }
                    }

                    function openPricingCheckout(planCode) {
                        showToast(`Checkout for ${planCode} will be wired to Stripe next.`);
                    }  
            
            function renderComparePapersList() {
                const el = document.getElementById("comparePapersList");
                if (!el) return;

                if (!comparePaperIds.length) {
                    el.innerHTML = "<div class='small'>No papers selected for comparison yet.</div>";
                    return;
                }

                el.innerHTML = comparePaperIds.map((paper, idx) => `
                    <div class="list-item">
                        <div><strong>${escapeHtml(paper.title || "Untitled")}</strong></div>
                        <div class="small">${escapeHtml(paper.work_id || "")}</div>
                        <div class="toolbar" style="margin-top:8px;">
                            <button class="danger-btn" onclick="removeComparePaper(${idx})">Remove</button>
                        </div>
                    </div>
                `).join("");
            }
            
            function mountSignIn() {
                const el = document.getElementById("clerk-sign-in");
                if (!el || !window.Clerk) return;

                el.innerHTML = "";
                window.Clerk.mountSignIn(el, {
                    appearance: {
                        elements: {
                            card: {
                                boxShadow: "none",
                                border: "1px solid rgba(148, 163, 184, 0.16)",
                                backgroundColor: "transparent"
                            }
                        }
                    }
                });
            }

            function mountUserButton() {
                const el = document.getElementById("clerk-user-button");
                const signInBtn = document.getElementById("signInBtn");
                if (!el || !window.Clerk) return;

                el.innerHTML = "";

                if (window.Clerk.user) {
                    window.Clerk.mountUserButton(el);
                    if (signInBtn) {
                        signInBtn.style.display = "none";
                    }
                } else {
                    if (signInBtn) {
                        signInBtn.style.display = "inline-flex";
                    }
                }
            }
            
            
            function addCurrentPaperToCompare() {
                if (!currentPaperMeta) {
                    showToast("Open a paper first.");
                    return;
                }

                const exists = comparePaperIds.some(p => p.work_id === currentPaperMeta.work_id);
                if (exists) {
                    showToast("That paper is already in the compare list.");
                    return;
                }

                comparePaperIds.push({
                    work_id: currentPaperMeta.work_id,
                    title: currentPaperMeta.title || "Untitled"
                });

                renderComparePapersList();
                showToast("Paper added to comparison.");
            }

            function removeComparePaper(index) {
                comparePaperIds.splice(index, 1);
                renderComparePapersList();
                showToast("Paper removed from comparison.");
            }

            function clearComparePapers() {
                comparePaperIds = [];
                renderComparePapersList();
                document.getElementById("compareResults").style.display = "none";
                showToast("Compare list cleared.");
            }

            function renderBulletList(items) {
                if (!items || !items.length) {
                    return "<div class='small'>Not available.</div>";
                }

                return "<ul>" + items.map(item => `<li>${escapeHtml(item)}</li>`).join("") + "</ul>";
            }
async function runMultiPaperCompare() {
    if (comparePaperIds.length < 2) {
        showToast("Add at least 2 papers to compare.");
        return;
    }

    const question = document.getElementById("compareQuestion").value.trim();
    const workIds = comparePaperIds.map(p => p.work_id);

    const compareResults = document.getElementById("compareResults");
    const compareSummary = document.getElementById("compareSummary");

    compareResults.style.display = "block";
    compareSummary.innerHTML = "Comparing papers...";

    try {
        const response = await fetch("/research/compare-papers", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                work_ids: workIds,
                user_question: question
            })
        });

        const data = await response.json();

        if (data.error) {
            showToast(data.error);
            return;
        }

        const comparison = data.comparison || {};

        lastComparisonPayload = {
            work_ids: workIds,
            paper_titles: comparePaperIds.map(p => p.title || p.work_id),
            question: question,
            summary: comparison.comparison_summary || ""
        };

        document.getElementById("compareSummary").innerHTML =
            `<p>${escapeHtml(comparison.comparison_summary || "No comparison summary available.")}</p>`;

        document.getElementById("compareThemes").innerHTML =
            renderBulletList(comparison.common_themes || []);

        document.getElementById("compareDifferences").innerHTML =
            renderBulletList(comparison.key_differences || []);

        document.getElementById("compareMethods").innerHTML =
            `<p>${escapeHtml(comparison.methods_comparison || "Not available.")}</p>`;

        document.getElementById("compareResultsText").innerHTML =
            `<p>${escapeHtml(comparison.results_comparison || "Not available.")}</p>`;

        document.getElementById("compareLimitations").innerHTML =
            `<p>${escapeHtml(comparison.limitations_comparison || "Not available.")}</p>`;

        document.getElementById("compareBestStudents").innerHTML =
            `<p>${escapeHtml(comparison.best_for_students || "Not available.")}</p>`;

        document.getElementById("compareBestResearchers").innerHTML =
            `<p>${escapeHtml(comparison.best_for_researchers || "Not available.")}</p>`;

        document.getElementById("compareBestPractical").innerHTML =
            `<p>${escapeHtml(comparison.best_for_practical_use || "Not available.")}</p>`;

        const rec = comparison.recommended_paper || {};
        document.getElementById("compareRecommended").innerHTML = `
            <p><strong>${escapeHtml(rec.work_id || "Unknown")}</strong></p>
            <p>${escapeHtml(rec.reason || "No recommendation reason available.")}</p>
        `;

        showToast("Comparison complete.");
    } catch (error) {
        console.error(error);
        showToast("Multi-paper comparison failed.");
    }
}

async function saveCurrentComparison() {
    if (!lastComparisonPayload) {
        showToast("Run a comparison first.");
        return;
    }

    try {
        const response = await fetch(`/product/workspace/${USER_ID}/comparisons`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                title: `Comparison of ${lastComparisonPayload.paper_titles.length} papers`,
                work_ids: lastComparisonPayload.work_ids,
                paper_titles: lastComparisonPayload.paper_titles,
                question: lastComparisonPayload.question,
                summary: lastComparisonPayload.summary
            })
        });

        if (!response.ok) {
            showToast("Failed to save comparison.");
            return;
        }

        await loadComparisonHistory();
        showToast("Comparison saved.");
    } catch (error) {
        console.error(error);
        showToast("Failed to save comparison.");
    }
}

async function initClerk() {
    if (!window.Clerk) {
        console.error("Clerk failed to load");
        return;
    }

    await window.Clerk.load();

    if (window.Clerk.user) {
        console.log("User signed in:", window.Clerk.user.id);
        syncUserFromClerk();
        mountUserButton();
        closeAuthModal();
    } else {
        console.log("User NOT signed in");
        mountUserButton();
    }
}

function syncUserFromClerk() {
    if (!window.Clerk || !window.Clerk.user) return;

    const user = window.Clerk.user;

    AppState.user.id = user.id;
    AppState.user.email = user.primaryEmailAddress?.emailAddress || "";

    console.log("Synced user:", AppState.user.id);
}

async function loadComparisonHistory() {
    const listEl = document.getElementById("comparisonHistoryList");
    if (!listEl) return;

    listEl.innerHTML = "<div class='small'>Loading comparison history...</div>";

    try {
        const response = await fetch(`/product/workspace/${USER_ID}/comparisons`);
        const data = await response.json();
        const comparisons = data.comparisons || [];

        if (!comparisons.length) {
            listEl.innerHTML = "<div class='small'>No saved comparisons yet.</div>";
            window.__comparisonHistoryCache = [];
            return;
        }

        listEl.innerHTML = comparisons.map(item => {
            const comparisonKey = item.id || item.comparison_id || "";
            return `
                <div class="list-item">
                    <div><strong>${escapeHtml(item.title || "Untitled Comparison")}</strong></div>
                    <div class="small">${escapeHtml(item.created_at || "")}</div>
                    <div class="small" style="margin-top:6px;">${escapeHtml(item.summary || "No summary saved.")}</div>
                    <div class="toolbar" style="margin-top:8px;">
                        <button class="secondary-btn" onclick="reloadComparisonFromHistory('${escapeHtml(comparisonKey)}')">Reload</button>
                        <button class="danger-btn" onclick="deleteComparisonHistoryItem('${escapeHtml(comparisonKey)}')">Delete</button>
                    </div>
                </div>
            `;
        }).join("");

        window.__comparisonHistoryCache = comparisons;
    } catch (error) {
        console.error(error);
        listEl.innerHTML = "<div class='small'>Failed to load comparison history.</div>";
    }
}

function reloadComparisonFromHistory(comparisonId) {
    const comparisons = window.__comparisonHistoryCache || [];
    const item = comparisons.find(c => (c.id || c.comparison_id) === comparisonId);

    if (!item) {
        showToast("Comparison not found.");
        return;
    }

    comparePaperIds = (item.work_ids || []).map((workId, idx) => ({
        work_id: workId,
        title: (item.paper_titles || [])[idx] || workId
    }));

    renderComparePapersList();

    const questionBox = document.getElementById("compareQuestion");
    if (questionBox) {
        questionBox.value = item.question || "";
    }

    showToast("Comparison reloaded.");
}

async function deleteComparisonHistoryItem(comparisonId) {
    try {
        const response = await fetch(`/product/workspace/${USER_ID}/comparisons/${comparisonId}`, {
            method: "DELETE"
        });

        if (!response.ok) {
            showToast("Failed to delete comparison.");
            return;
        }

        await loadComparisonHistory();
        showToast("Comparison deleted.");
    } catch (error) {
        console.error(error);
        showToast("Failed to delete comparison.");
    }
}

            function getStore(key, fallback = []) {
                try {
                    return JSON.parse(localStorage.getItem(key)) || fallback;
                } catch {
                    return fallback;
                }
            }

            function setStore(key, value) {
                localStorage.setItem(key, JSON.stringify(value));
            }

            function dedupeByWorkId(items) {
                const seen = new Set();
                return items.filter(item => {
                    const key = item.work_id || item.document_id || item.title;
                    if (seen.has(key)) return false;
                    seen.add(key);
                    return true;
                });
            }

            async function loadWorkspaceFromApi() {
                try {
                    const response = await fetch(`/product/workspace/${USER_ID}`);
                    const data = await response.json();
                    renderWorkspaceListsFromApi(data);
                } catch (error) {
                    console.error("Workspace load failed:", error);
                    showToast("Workspace load failed.");
                }
            }

            function renderWorkspaceLists() {
                const saved = getStore(STORE_KEYS.saved, []);
                const queue = getStore(STORE_KEYS.queue, []);
                const favorites = getStore(STORE_KEYS.favorites, []);
                const recents = getStore(STORE_KEYS.recents, []);

                renderList("savedPapersList", saved, "No saved papers yet.");
                renderList("readingQueueList", queue, "No queued papers yet.");
                renderList("favoritesList", favorites, "No favorites yet.");
                renderList("recentPapersList", recents, "No recent papers yet.");
            }

            function renderWorkspaceListsFromApi(workspace) {
                renderList("savedPapersList", workspace.saved_papers || [], "No saved papers yet.");
                renderList("readingQueueList", workspace.reading_queue || [], "No queued papers yet.");
                renderList("favoritesList", workspace.favorites || [], "No favorites yet.");
                renderList("recentPapersList", getStore(STORE_KEYS.recents, []), "No recent papers yet.");
            }

            function renderList(elementId, items, emptyText) {
                const el = document.getElementById(elementId);
                if (!el) return;

                if (!items || !items.length) {
                    el.innerHTML = `<div class="small">${escapeHtml(emptyText)}</div>`;
                    return;
                }

                el.innerHTML = "";
                items.slice(0, 12).forEach(item => {
                    const div = document.createElement("div");
                    div.className = "list-item";
                    div.innerHTML = `
                        <div><strong>${escapeHtml(item.title || "Untitled")}</strong></div>
                        <div class="small">${escapeHtml(item.source_system || item.source || item.institution || "Unknown source")}</div>
                    `;
                    el.appendChild(div);
                });
            }

            function pushRecentPaper(meta) {
                if (!meta) return;
                let recents = getStore(STORE_KEYS.recents, []);
                recents.unshift({
                    work_id: meta.work_id,
                    document_id: meta.document_id,
                    title: meta.title,
                    source_system: meta.source_system,
                    institution: meta.institution
                });
                recents = dedupeByWorkId(recents).slice(0, 12);
                setStore(STORE_KEYS.recents, recents);
                renderWorkspaceLists();
            }

            function setPlatformFilter(value, button) {
                    platformFilter = value;
                    AppState.ui.platformFilter = value;

                    document.querySelectorAll(".filter-chip").forEach(el => {
                        el.classList.remove("active");
                    });

                    if (button) {
                        button.classList.add("active");
                    }

                    const inputEl = document.getElementById("paperSearch");
                    const resultsContent = document.getElementById("searchResultsContent");

                    if (resultsContent && inputEl && inputEl.value.trim()) {
                        searchPapers();
                    }
                }

async function copyCitation(format) {
    const paperMeta = AppState?.paper?.meta || currentPaperMeta;

    if (!paperMeta) {
        showToast("Open a paper first.");
        return;
    }

    try {
        const response = await fetch(`/product/citations`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                title: paperMeta.title || "",
                authors: paperMeta.author
                    ? paperMeta.author.split(",").map(v => v.trim()).filter(Boolean)
                    : [],
                publication_year: paperMeta.publication_year || paperMeta.published || "",
                institution: paperMeta.institution || "",
                pdf_url: paperMeta.pdf_url || "",
                entry_url: paperMeta.entry_url || "",
                source_url: paperMeta.entry_url || paperMeta.pdf_url || ""
            })
        });

        let citations = {};
        try {
            citations = await response.json();
        } catch {
            citations = {};
        }

        if (!response.ok) {
            console.error("Citation API failed:", citations);
            showToast(`Citation generation failed (${response.status}).`);
            return;
        }

        const text = citations[format];
        if (!text) {
            showToast(`No ${format.toUpperCase()} citation returned.`);
            return;
        }

        await navigator.clipboard.writeText(text);
        showToast(`${format.toUpperCase()} citation copied.`);
    } catch (error) {
        console.error(error);
        showToast("Citation copy failed.");
    }
}

async function saveCurrentPaper() {
    const paperMeta = AppState?.paper?.meta || currentPaperMeta;

    if (!paperMeta) {
        showToast("Open a paper first.");
        return;
    }

    try {
        const response = await fetch(`/product/workspace/${USER_ID}/save-paper`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(paperMeta)
        });

        let data = {};
        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok) {
            console.error("Save paper failed:", data);
            showToast(data.detail || data.message || `Failed to save paper (${response.status}).`);
            return;
        }

        await loadWorkspaceFromApi();
        showToast("Paper saved.");
    } catch (error) {
        console.error(error);
        showToast("Failed to save paper.");
    }
}

async function queueCurrentPaper() {
    const paperMeta = AppState?.paper?.meta || currentPaperMeta;

    if (!paperMeta) {
        showToast("Open a paper first.");
        return;
    }

    try {
        const response = await fetch(`/product/workspace/${USER_ID}/queue-paper`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(paperMeta)
        });

        let data = {};
        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok) {
            console.error("Queue paper failed:", data);
            showToast(data.detail || data.message || `Failed to queue paper (${response.status}).`);
            return;
        }

        await loadWorkspaceFromApi();
        showToast("Added to reading queue.");
    } catch (error) {
        console.error(error);
        showToast("Failed to queue paper.");
    }
}

async function favoriteCurrentPaper() {
    const paperMeta = AppState?.paper?.meta || currentPaperMeta;

    if (!paperMeta) {
        showToast("Open a paper first.");
        return;
    }

    try {
        const response = await fetch(`/product/workspace/${USER_ID}/favorite-paper`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(paperMeta)
        });

        let data = {};
        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok) {
            console.error("Favorite paper failed:", data);
            showToast(data.detail || data.message || `Failed to favorite paper (${response.status}).`);
            return;
        }

        await loadWorkspaceFromApi();
        showToast("Added to favorites.");
    } catch (error) {
        console.error(error);
        showToast("Failed to favorite paper.");
    }
}

async function exportBuilderDocxStub() {
    if (!currentProjectId) {
        showToast("Save a draft first.");
        return;
    }

    const buttonEl = event?.target || null;
    setLoading(buttonEl, true, "Exporting...");

    try {
        const response = await fetch(
            `/product/authoring/${USER_ID}/projects/${currentProjectId}/export/docx`
        );

        if (!response.ok) {
            showToast("DOCX export failed.");
            return;
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = `research_project_${currentProjectId}.docx`;
        document.body.appendChild(a);
        a.click();
        a.remove();

        window.URL.revokeObjectURL(url);
        showToast("DOCX export downloaded.");
    } catch (error) {
        handleError("DOCX export failed.", error);
    } finally {
        setLoading(buttonEl, false);
    }
}

async function exportBuilderPdfStub() {
    if (!currentProjectId) {
        showToast("Save a draft first.");
        return;
    }

    const buttonEl = event?.target || null;
    setLoading(buttonEl, true, "Exporting...");

    try {
        const response = await fetch(
            `/product/authoring/${USER_ID}/projects/${currentProjectId}/export/pdf`
        );

        if (!response.ok) {
            const err = await response.json().catch(() => null);
            showToast(err?.detail || "PDF export failed.");
            return;
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = `research_project_${currentProjectId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();

        window.URL.revokeObjectURL(url);
        showToast("PDF export downloaded.");
    } catch (error) {
        handleError("PDF export failed.", error);
    } finally {
        setLoading(buttonEl, false);
    }
}

// Insert loadUploadedSources before handleLocalUploadStub if not present
async function loadUploadedSources() {
    const listEl = document.getElementById("uploadedSourcesList");
    if (!listEl) return;

    listEl.innerHTML = "<div class='small'>Loading uploaded sources...</div>";

    try {
        const response = await fetch(`/product/uploads/${USER_ID}`);

        let data = {};
        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok) {
            console.error("Load uploaded sources failed:", data);
            listEl.innerHTML = "<div class='small'>Failed to load uploaded sources.</div>";
            return;
        }

        const uploads = data.uploads || [];

        if (!uploads.length) {
            listEl.innerHTML = "<div class='small'>No uploaded sources yet.</div>";
            return;
        }

        listEl.innerHTML = uploads.map(item => `
            <div class="list-item">
                <div><strong>${escapeHtml(item.title || item.file_name || "Untitled Upload")}</strong></div>
                <div class="small">${escapeHtml(item.source_type || item.file_type || "uploaded")}</div>
                <div class="toolbar" style="margin-top:8px;">
                    <button class="secondary-btn" onclick="openUploadedDocument('${escapeHtml(item.document_id || "")}')">Open</button>
                </div>
            </div>
        `).join("");
    } catch (error) {
        console.error(error);
        listEl.innerHTML = "<div class='small'>Failed to load uploaded sources.</div>";
    }
}

async function handleLocalUploadStub() {
    const fileInput = document.getElementById("uploadFileInput");
    const file = fileInput ? fileInput.files[0] : null;

    if (!file) {
        showToast("Choose a file first.");
        return;
    }

    try {
        const formData = new FormData();
        formData.append("user_id", USER_ID);
        formData.append("plan", USER_PLAN);
        formData.append("file", file);

        const response = await fetch("/product/uploads/local", {
            method: "POST",
            body: formData
        });

        let data = {};
        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok) {
            console.error("File upload failed:", data);
            showToast(data.detail || data.message || `File upload failed (${response.status}).`);
            return;
        }

        showToast(`Uploaded: ${data.file_name || file.name}`);

        if (fileInput) {
            fileInput.value = "";
        }

        await loadUploadedSources();
    } catch (error) {
        console.error(error);
        showToast("File upload failed.");
    }
}

async function handleUrlIngestStub() {
    const urlInput = document.getElementById("urlIngestInput");
    const url = urlInput ? urlInput.value.trim() : "";

    if (!url) {
        showToast("Paste a URL first.");
        return;
    }

    try {
        const response = await fetch("/product/uploads/url", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: USER_ID,
                plan: USER_PLAN,
                url: url
            })
        });

        let data = {};
        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok) {
            console.error("URL ingest failed:", data);
            showToast(data.detail || data.message || `URL ingest failed (${response.status}).`);
            return;
        }

        showToast(`URL ingested: ${data.file_name || data.title || "document created"}`);

        if (urlInput) {
            urlInput.value = "";
        }

        await loadUploadedSources();
    } catch (error) {
        console.error(error);
        showToast("URL ingest failed.");
    }
}

async function searchPapers() {
    const inputEl = document.getElementById("paperSearch");
    const resultsContent = document.getElementById("searchResultsContent");
    const query = inputEl ? inputEl.value.trim() : "";

    if (!resultsContent) {
        console.error("searchResultsContent element not found.");
        return;
    }

    if (!query) {
        showToast("Please enter a search term.");
        resultsContent.innerHTML = "<div class='small'>Enter a search term to find papers.</div>";
        return;
    }

    resultsContent.innerHTML = "<div class='small'>Loading platform papers...</div>";

    try {
        const response = await fetch(`/research/search?q=${encodeURIComponent(query)}&limit=20`, {
            method: "GET",
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(`Search request failed with status ${response.status}`);
        }

        const data = await response.json();
        let filtered = Array.isArray(data) ? data : [];

        const activeFilter = AppState?.ui?.platformFilter || platformFilter || "all";

        if (activeFilter === "full") {
            filtered = filtered.filter(item => item.has_full_document === 1 || item.has_full_document === true);
        } else if (activeFilter === "metadata") {
            filtered = filtered.filter(item => item.has_full_document !== 1 && item.has_full_document !== true);
        }

        if (!filtered.length) {
            const emptyLabel =
                activeFilter === "full"
                    ? "No full-document papers found."
                    : activeFilter === "metadata"
                        ? "No metadata-only papers found."
                        : "No papers found.";

            resultsContent.innerHTML = `<div class='small'>${emptyLabel}</div>`;
            return;
        }

        resultsContent.innerHTML = "";

        filtered.forEach(item => {
            const statusClass =
                item.has_full_document === 1 || item.has_full_document === true ? "full" : "meta";
            const workId = item.work_id || item.id || "";

            const card = document.createElement("div");
            card.className = "result-card";
            card.innerHTML = `
                <div class="section-heading" style="margin-bottom:8px;">
                    <div>
                        <div class="meta">Year: ${escapeHtml(item.publication_year || "Unknown")} • Citations: ${escapeHtml(item.cited_by_count || 0)}</div>
                        <div><strong>${escapeHtml(item.title || "Untitled")}</strong></div>
                        <div class="small">Topic: ${escapeHtml(item.display_topic || item.primary_topic || "Unknown")}</div>
                        <div class="small">Author: ${escapeHtml(item.display_author || item.author || "Unknown")}</div>
                        <div class="small">Institution: ${escapeHtml(item.display_institution || item.institution || "Unknown")}</div>
                    </div>
                    <span class="status-pill ${statusClass}">${escapeHtml(item.availability_label || "Unknown")}</span>
                </div>
                <div class="toolbar">
                    <button class="secondary-btn" onclick="openPaper('${escapeHtml(workId)}')">Open Paper</button>
                </div>
            `;
            resultsContent.appendChild(card);
        });
    } catch (error) {
        console.error("Platform search failed:", error);
        resultsContent.innerHTML = "<div class='small'>Search failed. Check the /research/search route.</div>";
        showToast("Platform search failed.");
    }
}

            async function openUploadedDocument(documentId) {
    if (!documentId) {
        showToast("Uploaded document is missing a document_id.");
        return;
    }

    try {
        const response = await fetch(`/product/uploads/document/${encodeURIComponent(documentId)}`);
        const data = await response.json();

        if (!response.ok || data.detail || data.error) {
            showToast(data.detail || data.error || "Failed to open uploaded document.");
            return;
        }

        const meta = data.metadata || {};
        const ai = data.ai_summary || {};

        currentDocumentId = meta.document_id || documentId;
        currentPaperMeta = meta;
        currentPaperAi = ai;

        AppState.paper.documentId = currentDocumentId;
        AppState.paper.meta = meta;
        AppState.paper.ai = ai;

        document.getElementById("paperTitle").textContent = meta.title || "Uploaded Document";
        document.getElementById("paperAuthor").textContent = meta.author || "Unknown";
        document.getElementById("paperInstitution").textContent = meta.institution || "Unknown";
        document.getElementById("paperTopic").textContent = meta.topic || meta.primary_topic || "User Provided";
        document.getElementById("paperCitation").textContent = meta.citation || "No citation available";
        document.getElementById("paperPublished").textContent = meta.published || meta.publication_year || "Unknown";
        document.getElementById("paperSource").textContent = meta.source_system || "uploaded";

        document.getElementById("plainEnglishSummary").textContent =
            ai.plain_english_summary || "No summary available.";
        document.getElementById("academicSummary").textContent =
            ai.academic_summary || "No academic summary available.";
        document.getElementById("methodsSummary").textContent =
            ai.methods_summary || "Not extracted yet.";
        document.getElementById("resultsSummary").textContent =
            ai.results_summary || "Not extracted yet.";
        document.getElementById("limitationsSummary").textContent =
            ai.limitations_summary || "Not extracted yet.";
        document.getElementById("practicalApplications").textContent =
            ai.practical_applications || "Not extracted yet.";
        document.getElementById("suggestedTopics").textContent =
            ai.suggested_topics || "Not available.";
        document.getElementById("citationGuidance").textContent =
            ai.citation_guidance || "Not available.";

        const badge = document.getElementById("availabilityBadge");
        badge.textContent = meta.availability_label || "Full Document";
        badge.className = "status-pill full";

        const pdfUrlEl = document.getElementById("paperPdfUrl");
        pdfUrlEl.href = "#";
        pdfUrlEl.textContent = "Uploaded document";

        const categoriesWrap = document.getElementById("paperCategories");
        categoriesWrap.innerHTML = "";
        const cats = (meta.categories || "").split(",").map(v => v.trim()).filter(Boolean);
        cats.forEach(cat => {
            const pill = document.createElement("span");
            pill.className = "topic-pill";
            pill.textContent = cat;
            categoriesWrap.appendChild(pill);
        });

        document.getElementById("paperCard").style.display = "block";
        pushRecentPaper(meta);
        window.scrollTo({ top: 760, behavior: "smooth" });
        showToast("Uploaded document opened.");
    } catch (error) {
        console.error(error);
        showToast("Failed to open uploaded document.");
    }
}

async function searchArxiv() {
    const inputEl = document.getElementById("arxivSearch");
    const resultsContent = document.getElementById("arxivResultsContent");
    const query = inputEl ? inputEl.value.trim() : "";

    if (!resultsContent) {
        console.error("arxivResultsContent element not found.");
        return;
    }

    if (!query) {
        showToast("Please enter an arXiv search term.");
        resultsContent.innerHTML = "<div class='small'>Enter a search term to search arXiv.</div>";
        return;
    }

    resultsContent.innerHTML = "<div class='small'>Searching arXiv...</div>";

    try {
        const response = await fetch(`/research/arxiv-search?q=${encodeURIComponent(query)}&limit=10`, {
            method: "GET",
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(`arXiv search failed with status ${response.status}`);
        }

        const data = await response.json();
        const items = Array.isArray(data) ? data : [];

        if (!items.length) {
            resultsContent.innerHTML = "<div class='small'>No arXiv papers found.</div>";
            return;
        }

        resultsContent.innerHTML = "";

        items.forEach(item => {
            const authors = Array.isArray(item.authors) ? item.authors.join(", ") : "";
            const arxivId = item.arxiv_id || "";

            const card = document.createElement("div");
            card.className = "result-card";
            card.innerHTML = `
                <div class="source-badge">arXiv</div>
                <div><strong>${escapeHtml(item.title || "Untitled")}</strong></div>
                <div class="small">Authors: ${escapeHtml(authors || "Unknown")}</div>
                <div class="small">Category: ${escapeHtml(item.primary_category || "Unknown")}</div>
                <div class="small">Published: ${escapeHtml(item.published || "Unknown")}</div>
                <div class="small">arXiv ID: ${escapeHtml(arxivId)}</div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:12px;">
                    <button class="secondary-btn" onclick="ingestArxiv('${escapeHtml(arxivId)}', 'abstract')">Quick Ingest</button>
                    <button class="primary-btn" onclick="ingestArxiv('${escapeHtml(arxivId)}', 'full')">Full PDF Ingest</button>
                </div>
            `;
            resultsContent.appendChild(card);
        });
    } catch (error) {
        console.error("arXiv search failed:", error);
        resultsContent.innerHTML = "<div class='small'>arXiv search failed. Check the /research/arxiv-search route.</div>";
        showToast("arXiv search failed.");
    }
}

async function searchFederated() {
    const query = document.getElementById("federatedSearch").value.trim();
    const resultsContent = document.getElementById("federatedResultsContent");
    const buttonEl = event?.target || null;

    if (!query) {
        showToast("Please enter a federated search term.");
        return;
    }

    resultsContent.innerHTML = "<div class='small'>Searching institutional sources...</div>";
    setLoading(buttonEl, true, "Searching...");

    try {
        const response = await fetch(`/research/federated-search?q=${encodeURIComponent(query)}&limit_per_source=4`);
        const data = await response.json();

        if (!data || data.length === 0) {
            resultsContent.innerHTML = "<div class='small'>No federated results found.</div>";
            return;
        }

        resultsContent.innerHTML = "";

        data.forEach(item => {
            const authors = (item.authors || []).join(", ");
            const url = item.open_access_url || item.pdf_url || item.source_url || "";
            const card = document.createElement("div");
            card.className = "result-card";
            card.innerHTML = `
                <div class="source-badge">${escapeHtml(item.source || "source")}</div>
                <div><strong>${escapeHtml(item.title || "Untitled")}</strong></div>
                <div class="small">Institution: ${escapeHtml(item.institution || "Unknown")}</div>
                <div class="small">Authors: ${escapeHtml(authors || "Unknown")}</div>
                <div class="small">Published: ${escapeHtml(item.published || "Unknown")}</div>
                <div class="small">Availability: ${escapeHtml(item.availability || "Unknown")}</div>
                <div class="small" style="margin-top:8px;">${escapeHtml(item.abstract || "").slice(0, 360)}${(item.abstract || "").length > 360 ? "..." : ""}</div>
                ${url ? `<div class="toolbar"><a class="secondary-btn" href="${escapeHtml(url)}" target="_blank">Open Source</a></div>` : ""}
            `;
            resultsContent.appendChild(card);
        });
    } catch (error) {
        resultsContent.innerHTML = "<div class='small'>Federated search failed.</div>";
        handleError("Federated search failed.", error);
    } finally {
        setLoading(buttonEl, false);
    }
}

async function ingestArxiv(arxivId, mode, buttonEl = null) {
    if (!arxivId) {
        showToast("This paper is missing an arXiv ID.");
        return;
    }

    setLoading(buttonEl, true, mode === "full" ? "Ingesting PDF..." : "Ingesting...");

    try {
        const response = await fetch(
            `/research/arxiv-ingest?arxiv_id=${encodeURIComponent(arxivId)}&mode=${encodeURIComponent(mode)}`,
            { method: "POST" }
        );

        let data = {};
        try {
            data = await response.json();
        } catch {
            data = {};
        }

        if (!response.ok || !data.success) {
            console.error("Ingest failed response:", data);
            showToast(data.message || `Ingest failed (${response.status}).`);
            return;
        }

        showToast(`Ingested (${mode}): ${data.title || arxivId}`);

        if (data.matched_work_id) {
            const paperSearchEl = document.getElementById("paperSearch");
            if (paperSearchEl) {
                paperSearchEl.value = data.title || arxivId;
            }
            await searchPapers();
            await openPaper(data.matched_work_id);
        } else {
            const paperSearchEl = document.getElementById("paperSearch");
            if (paperSearchEl) {
                paperSearchEl.value = data.title || arxivId;
            }
            await searchPapers();
            showToast("Paper ingested. Search results refreshed.");
        }
    } catch (error) {
        console.error(error);
        showToast("Ingest failed.");
    } finally {
        setLoading(buttonEl, false);
    }
}

          async function askQuestion() {
    const questionBox = document.getElementById("question");
    const answerBox = document.getElementById("answer");
    const evidenceBox = document.getElementById("evidence");
    const qaPanel = document.getElementById("qaPanel");
    const question = questionBox ? questionBox.value.trim() : "";

    if (!question) {
        alert("Please enter a question.");
        return;
    }

    if (!currentDocumentId) {
        alert("Please open a paper with a full document first.");
        return;
    }

    qaPanel.style.display = "block";
    answerBox.innerHTML = "Loading answer...";
    evidenceBox.innerHTML = "";

    try {
        const response = await fetch("/documents/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question,
                document_id: currentDocumentId
            })
        });

        const data = await response.json();

        answerBox.innerHTML = `<p>${escapeHtml(data.answer || "No answer returned.")}</p>`;

        if (data.evidence && data.evidence.length > 0) {
            evidenceBox.innerHTML = "<h3>Supporting Evidence</h3>";

            data.evidence.forEach(item => {
                evidenceBox.innerHTML += `
                    <div class="evidence-item">
                        <div class="meta">
                            Document: ${escapeHtml(item.document_id)} |
                            Source: ${escapeHtml(item.section_guess)} |
                            Reference: ${escapeHtml(item.chunk_id)} |
                            Score: ${escapeHtml(item.score)}
                        </div>
                        <div>${escapeHtml(item.text)}</div>
                    </div>
                `;
            });
        } else {
            evidenceBox.innerHTML = "<div class='small'>No supporting evidence found.</div>";
        }

    } catch (error) {
        console.error(error);
        answerBox.innerHTML = "<p>Failed to retrieve answer.</p>";
        evidenceBox.innerHTML = "";
    }
}
                    
function setLoading(el, isLoading, text = "Loading...") {
    if (!el) return;
    if (isLoading) {
        el.dataset.original = el.innerHTML;
        el.innerHTML = text;
        el.disabled = true;
    } else {
        el.innerHTML = el.dataset.original || el.innerHTML;
        el.disabled = false;
    }
}

async function openPaper(workId) {
    if (!workId) {
        showToast("This paper is missing a work ID.");
        return;
    }

    try {
        const response = await fetch(`/research/paper/${encodeURIComponent(workId)}`);
        const data = await response.json();

        if (!response.ok || data.message || data.error) {
            showToast(data.message || data.error || "Failed to open paper.");
            return;
        }

        const meta = data.metadata || {};
        const ai = data.ai_summary || {};

        currentDocumentId = meta.document_id || null;
        currentPaperMeta = meta;
        currentPaperAi = ai;
        AppState.paper.meta = meta;
        AppState.paper.ai = ai;
        AppState.paper.documentId = currentDocumentId;

        document.getElementById("paperTitle").textContent = meta.title || "Untitled";
        document.getElementById("paperAuthor").textContent = meta.author || "Unknown";
        document.getElementById("paperInstitution").textContent = meta.institution || "Unknown";
        document.getElementById("paperTopic").textContent = meta.topic || meta.primary_topic || "Unknown";
        document.getElementById("paperCitation").textContent = meta.citation || "No citation available";
        document.getElementById("paperPublished").textContent = meta.published || meta.publication_year || "Unknown";
        document.getElementById("paperSource").textContent = meta.source_system || "Unknown";

        document.getElementById("plainEnglishSummary").textContent = ai.plain_english_summary || ai.executive_summary || "No AI summary available.";
        document.getElementById("academicSummary").textContent = ai.academic_summary || ai.technical_summary || "No academic summary available.";
        document.getElementById("methodsSummary").textContent = ai.methods_summary || "Not available.";
        document.getElementById("resultsSummary").textContent = ai.results_summary || "Not available.";
        document.getElementById("limitationsSummary").textContent = ai.limitations_summary || "Not available.";
        document.getElementById("practicalApplications").textContent = ai.practical_applications || "Not available.";
        document.getElementById("suggestedTopics").textContent = ai.suggested_topics || "Not available.";
        document.getElementById("citationGuidance").textContent = ai.citation_guidance || "Not available.";

        const badge = document.getElementById("availabilityBadge");
        badge.textContent = meta.availability_label || "Unknown";
        badge.className = "status-pill " + ((meta.has_full_document === 1 || meta.has_full_document === true) ? "full" : "meta");

        const pdfUrlEl = document.getElementById("paperPdfUrl");
        if (meta.pdf_url) {
            pdfUrlEl.href = meta.pdf_url;
            pdfUrlEl.textContent = meta.pdf_url;
        } else if (meta.entry_url) {
            pdfUrlEl.href = meta.entry_url;
            pdfUrlEl.textContent = meta.entry_url;
        } else {
            pdfUrlEl.href = "#";
            pdfUrlEl.textContent = "No external source link available";
        }

        const categoriesWrap = document.getElementById("paperCategories");
        categoriesWrap.innerHTML = "";
        const cats = (meta.categories || "").split(",").map(v => v.trim()).filter(Boolean);
        cats.forEach(cat => {
            const pill = document.createElement("span");
            pill.className = "topic-pill";
            pill.textContent = cat;
            categoriesWrap.appendChild(pill);
        });

        document.getElementById("paperCard").style.display = "block";
        pushRecentPaper(meta);
        document.getElementById("paperCard").scrollIntoView({ behavior: "smooth", block: "start" });
        showToast("Paper opened.");
    } catch (error) {
        handleError("Failed to open paper.", error);
    }
}
            await initClerk();
            document.addEventListener("DOMContentLoaded", async () => {
                try {
                    await loadWorkspaceFromApi();
                } catch (error) {
                    console.error(error);
                }

                try {
                    await renderBuilderPreview();
                    await loadComparisonHistory();
                    await loadUploadedSources();
                } catch (error) {
                    console.error(error);
                }

                renderWorkspaceLists();
                renderComparePapersList();
            });
        </script>
    </body>
    </html>
    """