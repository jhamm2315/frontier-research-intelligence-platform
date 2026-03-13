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
                max-width: 1400px;
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
            .sidebar h2, .mainpanel h1, .mainpanel h2 {
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
                margin-top: 16px;
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
            .result, .doccard {
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
            <div class="navlinks">Educational Research Explorer • Grounded Q&A • Scientific Discovery</div>
        </div>

        <div class="layout">
            <div class="sidebar">
                <h2>How to Use This Tool</h2>
                <p>
                    This application helps students and researchers explore research papers,
                    understand what they are about, and ask grounded questions based on source content.
                </p>
                <p>
                    Start by searching for a paper by title, topic, author, or institution.
                    If a full document is available, you can open it and ask questions about its
                    methods, results, limitations, or overall purpose.
                </p>

                <h2>Sample Questions</h2>
                <button class="sample-btn" onclick="setQuestion('What methods does the graph learning paper use?')">
                    What methods does the graph learning paper use?
                </button>
                <button class="sample-btn" onclick="setQuestion('What are the limitations of this paper?')">
                    What are the limitations of this paper?
                </button>
                <button class="sample-btn" onclick="setQuestion('What does this paper conclude?')">
                    What does this paper conclude?
                </button>
            </div>

            <div class="mainpanel">
                <h1>Ask Questions About Research Documents</h1>
                <p>
                    Search papers across the platform. All papers are searchable from metadata,
                    but only some have full document intelligence available for summaries and Q&A.
                </p>

                <label for="paperSearch">Search papers by title, topic, author, or institution</label>
                <input id="paperSearch" type="text" placeholder="Example: artificial intelligence" />
                <button onclick="searchPapers()">Search Papers</button>

                <div class="result" id="searchResults" style="display:none;">
                    <h2>Search Results</h2>
                    <div id="searchResultsContent"></div>
                </div>

                <label for="documentSelect">Select a document</label>
                <select id="documentSelect" onchange="loadDocumentSummary()">
                    <option value="">Loading documents...</option>
                </select>

                <div class="doccard" id="doccard" style="display:none;">
                    <h2 id="docTitle"></h2>
                    <div class="docmeta">
                        <div><strong>Author</strong><br><span id="docAuthor"></span></div>
                        <div><strong>Institution</strong><br><span id="docInstitution"></span></div>
                        <div><strong>Topic</strong><br><span id="docTopic"></span></div>
                        <div><strong>Citation</strong><br><span id="docCitation"></span></div>
                    </div>
                    <div style="margin-top:16px;">
                        <strong>Executive Summary</strong>
                        <p id="docSummary"></p>
                    </div>
                </div>

                <label for="question">Ask a question</label>
                <textarea id="question" placeholder="Example: What methods does this paper use?"></textarea>

                <button onclick="askQuestion()">Ask</button>

                <div class="result" id="result" style="display:none;">
                    <h2>Answer</h2>
                    <div id="answer"></div>
                    <div class="evidence" id="evidence"></div>
                </div>
            </div>
        </div>

        <script>
            async function loadDocuments() {
                const select = document.getElementById("documentSelect");
                const response = await fetch("/documents/list");
                const docs = await response.json();

                select.innerHTML = '<option value="">Choose a document</option>';
                docs.forEach(doc => {
                    const option = document.createElement("option");
                    option.value = doc.document_id;
                    option.textContent = `${doc.document_id} — ${doc.title}`;
                    select.appendChild(option);
                });

                if (docs.length > 0) {
                    select.value = docs[0].document_id;
                    loadDocumentSummary();
                }
            }

            async function loadDocumentSummary() {
                const documentId = document.getElementById("documentSelect").value;
                const card = document.getElementById("doccard");

                if (!documentId) {
                    card.style.display = "none";
                    return;
                }

                const response = await fetch(`/documents/${documentId}/summary`);
                const data = await response.json();

                document.getElementById("docTitle").textContent = data.title || "Untitled";
                document.getElementById("docAuthor").textContent = data.author || "Unknown";
                document.getElementById("docInstitution").textContent = data.institution || "Unknown";
                document.getElementById("docTopic").textContent = data.topic || "Unknown";
                document.getElementById("docCitation").textContent = data.citation || "No citation available";
                document.getElementById("docSummary").textContent = data.executive_summary || "No summary available.";

                card.style.display = "block";
            }

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

                resultsContent.innerHTML = "Loading...";
                resultsBox.style.display = "block";

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
                                ${item.availability_label} | Year: ${item.publication_year || "Unknown"} | Citations: ${item.cited_by_count || 0}
                            </div>
                            <div><strong>${item.title || "Untitled"}</strong></div>
                            <div class="small">Topic: ${item.display_topic || item.primary_topic || "Unknown"}</div>
                            <div class="small">Author: ${item.display_author || "Unknown"}</div>
                            <div class="small">Institution: ${item.display_institution || "Unknown"}</div>
                            <div style="margin-top:8px;">
                                <button onclick="selectPaperFromSearch('${item.document_id || ""}', '${item.title ? item.title.replace(/'/g, "\\'") : ""}')">
                                    ${item.has_full_document === 1 ? "Open Document Mode" : "Metadata Only"}
                                </button>
                            </div>
                        `;
                        resultsContent.appendChild(card);
                    });
                } catch (error) {
                    resultsContent.innerHTML = `<p class='small'>Search failed: ${error}</p>`;
                }
            }

            function selectPaperFromSearch(documentId, title) {
                if (documentId) {
                    const select = document.getElementById("documentSelect");
                    select.value = documentId;
                    loadDocumentSummary();
                    document.getElementById("question").value = "What is this paper about?";
                    window.scrollTo({ top: 0, behavior: "smooth" });
                } else {
                    alert(`"${title}" is currently metadata-only. Full document Q&A is not available yet.`);
                }
            }

            async function askQuestion() {
                const question = document.getElementById("question").value.trim();
                const documentId = document.getElementById("documentSelect").value;
                const resultBox = document.getElementById("result");
                const answerBox = document.getElementById("answer");
                const evidenceBox = document.getElementById("evidence");

                if (!question) {
                    alert("Please enter a question.");
                    return;
                }

                answerBox.innerHTML = "Loading...";
                evidenceBox.innerHTML = "";
                resultBox.style.display = "block";

                try {
                    const response = await fetch("/documents/ask", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            question: question,
                            document_id: documentId || null
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

            loadDocuments();
        </script>
    </body>
    </html>
    """
