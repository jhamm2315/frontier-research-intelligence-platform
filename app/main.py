from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.api import documents, research

app = FastAPI(
    title="Frontier Research Intelligence Platform",
    version="0.1.0",
    description="Scientific discovery intelligence system with graph analytics, document intelligence, and research question answering."
)

app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(research.router, prefix="/research", tags=["Research"])


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Frontier Research Intelligence Platform</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #0b1120;
                color: #f8fafc;
                margin: 0;
                padding: 0;
            }
            .navbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 18px 32px;
                border-bottom: 1px solid #1e293b;
                background: #0f172a;
                position: sticky;
                top: 0;
                z-index: 10;
            }
            .brand {
                font-size: 1.2rem;
                font-weight: bold;
                color: #22d3ee;
            }
            .navlinks {
                color: #94a3b8;
                font-size: 0.95rem;
            }
            .layout {
                display: grid;
                grid-template-columns: 320px 1fr;
                gap: 24px;
                max-width: 1450px;
                margin: 24px auto;
                padding: 0 24px 24px 24px;
            }
            .sidebar, .mainpanel {
                background: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 16px;
                padding: 24px;
                box-shadow: 0 12px 30px rgba(0,0,0,0.25);
            }
            .sidebar h2, .mainpanel h1, .mainpanel h2, .mainpanel h3 {
                color: #22d3ee;
                margin-top: 0;
            }
            .sidebar p, .mainpanel p {
                color: #cbd5e1;
                line-height: 1.6;
            }
            label {
                display: block;
                margin-top: 16px;
                margin-bottom: 8px;
                font-weight: bold;
                color: #e2e8f0;
            }
            input, select, textarea, button {
                width: 100%;
                box-sizing: border-box;
                border-radius: 10px;
                border: 1px solid #334155;
                padding: 14px;
                font-size: 1rem;
            }
            input, select, textarea {
                background: #020617;
                color: white;
            }
            textarea {
                min-height: 110px;
                resize: vertical;
            }
            button {
                margin-top: 12px;
                background: #22d3ee;
                color: #0f172a;
                font-weight: bold;
                cursor: pointer;
                border: none;
            }
            button:hover {
                background: #67e8f9;
            }
            .sample-btn {
                margin-top: 10px;
                background: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                text-align: left;
            }
            .sample-btn:hover {
                background: #334155;
            }
            .panel, .doccard {
                margin-top: 24px;
                padding: 20px;
                background: #020617;
                border: 1px solid #334155;
                border-radius: 12px;
            }
            .evidence {
                margin-top: 18px;
                padding-top: 12px;
                border-top: 1px solid #334155;
            }
            .evidence-item {
                margin-bottom: 14px;
                padding: 12px;
                background: #111827;
                border-radius: 10px;
                border: 1px solid #1f2937;
            }
            .meta {
                font-size: 0.9rem;
                color: #94a3b8;
                margin-bottom: 6px;
            }
            .small {
                font-size: 0.9rem;
                color: #94a3b8;
            }
            .docmeta {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
                margin-top: 12px;
            }
            .docmeta div {
                background: #111827;
                padding: 10px;
                border-radius: 10px;
                border: 1px solid #1f2937;
            }
            .summary-section {
                margin-top: 18px;
                padding: 14px;
                background: #0b1220;
                border: 1px solid #334155;
                border-radius: 10px;
            }
            .summary-section h3 {
                margin-bottom: 8px;
            }
            .link {
                color: #67e8f9;
                word-break: break-all;
            }
            .success {
                color: #86efac;
            }
            @media (max-width: 980px) {
                .layout {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="navbar">
            <div class="brand">Frontier Research Intelligence Platform</div>
            <div class="navlinks">Educational Research Explorer • AI Summaries • Scientific Discovery</div>
        </div>

        <div class="layout">
            <div class="sidebar">
                <h2>How to Use This Tool</h2>
                <p>
                    Search papers by title, topic, author, or institution. All papers are searchable from metadata.
                    Some papers also have full document intelligence, including AI summaries and grounded Q&A.
                </p>
                <p>
                    You can also search arXiv and ingest new papers directly into the platform.
                </p>

                <h2>Sample Questions</h2>
                <button class="sample-btn" onclick="setQuestion('What is this paper about?')">What is this paper about?</button>
                <button class="sample-btn" onclick="setQuestion('What methods does this paper use?')">What methods does this paper use?</button>
                <button class="sample-btn" onclick="setQuestion('What are the main findings?')">What are the main findings?</button>
                <button class="sample-btn" onclick="setQuestion('How could this paper be used in practice?')">How could this paper be used in practice?</button>
            </div>

            <div class="mainpanel">
                <h1>Search and Explore Research Papers</h1>
                <p>
                    Search your platform catalog or ingest new open-access research from arXiv.
                </p>

                <label for="paperSearch">Search platform papers</label>
                <input id="paperSearch" type="text" placeholder="Example: graph learning" />
                <button onclick="searchPapers()">Search Papers</button>

                <div class="panel" id="searchResults" style="display:none;">
                    <h2>Search Results</h2>
                    <div id="searchResultsContent"></div>
                </div>

                <label for="arxivSearch">Search arXiv</label>
                <input id="arxivSearch" type="text" placeholder="Example: graph neural networks" />
                <button onclick="searchArxiv()">Search arXiv</button>

                <div class="panel" id="arxivResults" style="display:none;">
                    <h2>arXiv Results</h2>
                    <div id="arxivResultsContent"></div>
                </div>

                <div class="doccard" id="paperCard" style="display:none;">
                    <h2 id="paperTitle"></h2>

                    <div class="docmeta">
                        <div><strong>Author</strong><br><span id="paperAuthor"></span></div>
                        <div><strong>Institution</strong><br><span id="paperInstitution"></span></div>
                        <div><strong>Topic</strong><br><span id="paperTopic"></span></div>
                        <div><strong>Citation</strong><br><span id="paperCitation"></span></div>
                        <div><strong>Published</strong><br><span id="paperPublished"></span></div>
                        <div><strong>Source</strong><br><span id="paperSource"></span></div>
                    </div>

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

                    <div class="summary-section">
                        <h3>PDF / Source Link</h3>
                        <p><a id="paperPdfUrl" class="link" href="#" target="_blank"></a></p>
                    </div>
                </div>

                <label for="question">Ask a question about the selected document</label>
                <textarea id="question" placeholder="Example: What methods does this paper use?"></textarea>
                <button onclick="askQuestion()">Ask</button>

                <div class="panel" id="qaPanel" style="display:none;">
                    <h2>Answer</h2>
                    <div id="answer"></div>
                    <div class="evidence" id="evidence"></div>
                </div>
            </div>
        </div>

        <script>
            let currentDocumentId = null;
            let currentWorkId = null;

            function setQuestion(text) {
                document.getElementById("question").value = text;
            }

            async function searchPapers() {
                const query = document.getElementById("paperSearch").value.trim();
                const resultsBox = document.getElementById("searchResults");
                const resultsContent = document.getElementById("searchResultsContent");

                if (!query) {
                    alert("Please enter a search term.");
                    return;
                }

                resultsBox.style.display = "block";
                resultsContent.innerHTML = "Loading...";

                try {
                    const response = await fetch(`/research/search?q=${encodeURIComponent(query)}&limit=20`);
                    const data = await response.json();

                    if (!data || data.length === 0) {
                        resultsContent.innerHTML = "<p class='small'>No papers found.</p>";
                        return;
                    }

                    resultsContent.innerHTML = "";

                    data.forEach(item => {
                        const card = document.createElement("div");
                        card.className = "evidence-item";
                        card.innerHTML = `
                            <div class="meta">
                                ${item.availability_label || "Unknown"} | Year: ${item.publication_year || "Unknown"} | Citations: ${item.cited_by_count || 0}
                            </div>
                            <div><strong>${item.title || "Untitled"}</strong></div>
                            <div class="small">Topic: ${item.display_topic || item.primary_topic || "Unknown"}</div>
                            <div class="small">Author: ${item.display_author || "Unknown"}</div>
                            <div class="small">Institution: ${item.display_institution || "Unknown"}</div>
                            <div style="margin-top:8px;">
                                <button onclick="openPaper('${item.work_id}')">Open Paper</button>
                            </div>
                        `;
                        resultsContent.appendChild(card);
                    });
                } catch (error) {
                    resultsContent.innerHTML = `<p class='small'>Search failed: ${error}</p>`;
                }
            }

            async function openPaper(workId) {
                currentWorkId = workId;

                const response = await fetch(`/research/paper/${workId}`);
                const data = await response.json();

                if (data.message || data.error) {
                    alert(data.message || data.error);
                    return;
                }

                const meta = data.metadata || {};
                const ai = data.ai_summary || {};

                currentDocumentId = meta.document_id || null;

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

                document.getElementById("paperCard").style.display = "block";
                window.scrollTo({ top: 0, behavior: "smooth" });
            }

            async function searchArxiv() {
                const query = document.getElementById("arxivSearch").value.trim();
                const resultsBox = document.getElementById("arxivResults");
                const resultsContent = document.getElementById("arxivResultsContent");

                if (!query) {
                    alert("Please enter an arXiv search term.");
                    return;
                }

                resultsBox.style.display = "block";
                resultsContent.innerHTML = "Loading...";

                try {
                    const response = await fetch(`/research/arxiv-search?q=${encodeURIComponent(query)}&limit=10`);
                    const data = await response.json();

                    if (!data || data.length === 0) {
                        resultsContent.innerHTML = "<p class='small'>No arXiv papers found.</p>";
                        return;
                    }

                    resultsContent.innerHTML = "";

                    data.forEach(item => {
                        const authors = (item.authors || []).join(", ");
                        const card = document.createElement("div");
                        card.className = "evidence-item";
                        card.innerHTML = `
                            <div><strong>${item.title || "Untitled"}</strong></div>
                            <div class="small">Authors: ${authors || "Unknown"}</div>
                            <div class="small">Category: ${item.primary_category || "Unknown"}</div>
                            <div class="small">Published: ${item.published || "Unknown"}</div>
                            <div class="small">arXiv ID: ${item.arxiv_id || ""}</div>
                            <div style="margin-top:8px;">
                                <button onclick="ingestArxiv('${item.arxiv_id}')">Ingest into Platform</button>
                            </div>
                        `;
                        resultsContent.appendChild(card);
                    });
                } catch (error) {
                    resultsContent.innerHTML = `<p class='small'>arXiv search failed: ${error}</p>`;
                }
            }

            async function ingestArxiv(arxivId) {
                try {
                    const response = await fetch(`/research/arxiv-ingest?arxiv_id=${encodeURIComponent(arxivId)}`, {
                        method: "POST"
                    });
                    const data = await response.json();

                    if (data.success) {
                        alert(`Ingested: ${data.title}`);
                        document.getElementById("paperSearch").value = data.title || arxivId;
                        await searchPapers();
                    } else {
                        alert(data.message || "Ingest failed.");
                    }
                } catch (error) {
                    alert("Ingest failed: " + error);
                }
            }

            async function askQuestion() {
                const question = document.getElementById("question").value.trim();
                const answerBox = document.getElementById("answer");
                const evidenceBox = document.getElementById("evidence");
                const qaPanel = document.getElementById("qaPanel");

                if (!question) {
                    alert("Please enter a question.");
                    return;
                }

                if (!currentDocumentId) {
                    alert("Please open a paper with a full document first.");
                    return;
                }

                qaPanel.style.display = "block";
                answerBox.innerHTML = "Loading...";
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

                    answerBox.innerHTML = `<p>${data.answer || "No answer returned."}</p>`;

                    if (data.evidence && data.evidence.length > 0) {
                        evidenceBox.innerHTML = "<h3>Supporting Evidence</h3>";
                        data.evidence.forEach(item => {
                            evidenceBox.innerHTML += `
                                <div class="evidence-item">
                                    <div class="meta">
                                        Document: ${item.document_id} |
                                        Chunk: ${item.chunk_id} |
                                        Section: ${item.section_guess} |
                                        Score: ${item.score}
                                    </div>
                                    <div>${item.text}</div>
                                </div>
                            `;
                        });
                    } else {
                        evidenceBox.innerHTML = "<p class='small'>No supporting evidence found.</p>";
                    }
                } catch (error) {
                    answerBox.innerHTML = "<p>Something went wrong while asking the question.</p>";
                    evidenceBox.innerHTML = `<p class='small'>${error}</p>`;
                }
            }
        </script>
    </body>
    </html>
    """
