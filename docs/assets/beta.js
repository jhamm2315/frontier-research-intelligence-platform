(function () {
  const config = window.FRIP_BETA_CONFIG || {};
  const state = {
    theme: localStorage.getItem("frip-beta-theme") || "dark",
    authMode: "sign-in",
    user: null,
    token: null,
    currentDocumentId: null,
    currentPaperMeta: null,
    currentPaperAi: null,
    comparePapers: [],
    workspace: {
      saved: [],
      queue: [],
      favorites: [],
      uploads: [],
    },
    supabase: null,
  };

  function $(id) {
    return document.getElementById(id);
  }

  function showToast(message) {
    const toast = $("toast");
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("visible");
    clearTimeout(window.__fripBetaToast);
    window.__fripBetaToast = window.setTimeout(() => {
      toast.classList.remove("visible");
    }, 2800);
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function setTheme(theme) {
    state.theme = theme;
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("frip-beta-theme", theme);
  }

  function initTheme() {
    setTheme(state.theme);
    $("themeToggle")?.addEventListener("click", () => {
      setTheme(state.theme === "dark" ? "light" : "dark");
    });
  }

  function getApiUrl(path) {
    const base = String(config.apiBaseUrl || "").replace(/\/+$/, "");
    if (!base) {
      throw new Error("Missing apiBaseUrl in FRIP_BETA_CONFIG.");
    }
    return `${base}${path}`;
  }

  function getSelectedFriendSignal() {
    const checked = document.querySelector('input[name="tell_friend"]:checked');
    return checked ? checked.value : "maybe";
  }

  function getInterestList() {
    return ($("profileInterests")?.value || "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function getBetaProfilePayload() {
    const user = state.user;
    if (!user) return null;
    const email = user.primaryEmailAddress?.emailAddress || user.emailAddresses?.[0]?.emailAddress || "";
    return {
      clerk_user_id: user.id,
      username: $("profileUsername")?.value.trim() || user.username || "",
      email,
      full_name: $("profileFullName")?.value.trim() || user.fullName || `${user.firstName || ""} ${user.lastName || ""}`.trim(),
      first_name: user.firstName || "",
      last_name: user.lastName || "",
      avatar_url: user.imageUrl || "",
      institution: $("profileInstitution")?.value.trim() || "",
      role_title: $("profileRoleTitle")?.value.trim() || "",
      github_url: $("profileGithub")?.value.trim() || "",
      linkedin_url: $("profileLinkedin")?.value.trim() || "",
      research_interests: getInterestList(),
      onboarding_notes: [
        $("profileNotes")?.value.trim() || "",
        `beta_tell_friend=${getSelectedFriendSignal()}`,
        `beta_primary_use_case=${$("betaPrimaryUseCase")?.value.trim() || ""}`,
        `beta_feedback=${$("betaFeedback")?.value.trim() || ""}`,
      ].filter(Boolean).join("\n"),
      plan: "free",
      auth_provider: "clerk",
    };
  }

  async function getToken(forceRefresh = false) {
    if (!window.Clerk?.session) return null;
    if (!forceRefresh && state.token) return state.token;
    try {
      state.token = await window.Clerk.session.getToken();
      return state.token;
    } catch (error) {
      console.error(error);
      state.token = null;
      return null;
    }
  }

  async function apiFetch(path, options = {}, requireAuth = false) {
    const headers = { ...(options.headers || {}) };
    if (requireAuth) {
      const token = await getToken(false);
      if (!token) {
        openAuthModal("sign-in");
        throw new Error("A signed-in Clerk session is required.");
      }
      headers.Authorization = `Bearer ${token}`;
    }
    const response = await fetch(getApiUrl(path), {
      ...options,
      headers,
    });
    if ((response.status === 401 || response.status === 403) && requireAuth) {
      openAuthModal("sign-in");
    }
    return response;
  }

  function initSupabase() {
    if (!config.supabaseUrl || !config.supabaseAnonKey || !window.supabase?.createClient) {
      return;
    }
    state.supabase = window.supabase.createClient(config.supabaseUrl, config.supabaseAnonKey);
  }

  async function persistBetaSignal() {
    if (!state.user || !state.supabase) {
      return { persisted: false, mode: "disabled" };
    }
    const payload = {
      clerk_user_id: state.user.id,
      email: state.user.primaryEmailAddress?.emailAddress || state.user.emailAddresses?.[0]?.emailAddress || null,
      full_name: $("profileFullName")?.value.trim() || state.user.fullName || null,
      institution: $("profileInstitution")?.value.trim() || null,
      role_title: $("profileRoleTitle")?.value.trim() || null,
      selected_plan: "free_beta",
      tell_friend_signal: getSelectedFriendSignal(),
      primary_use_case: $("betaPrimaryUseCase")?.value.trim() || null,
      feedback: $("betaFeedback")?.value.trim() || null,
      github_url: $("profileGithub")?.value.trim() || null,
      linkedin_url: $("profileLinkedin")?.value.trim() || null,
      research_interests: getInterestList(),
      source: "github_pages_beta",
      metadata: {
        page: window.location.href,
        app_name: config.appName || "FRIP Beta",
      },
    };
    const { error } = await state.supabase
      .from(config.betaSignalTable || "beta_interest_signals")
      .upsert(payload, { onConflict: "clerk_user_id" });
    if (error) {
      console.error(error);
      return { persisted: false, mode: "supabase_error", error };
    }
    return { persisted: true, mode: "supabase" };
  }

  function setAuthHeading(mode) {
    state.authMode = mode;
    $("authHeading").textContent = mode === "sign-up" ? "Create beta account" : "Sign in";
  }

  function openAuthModal(mode) {
    setAuthHeading(mode || state.authMode);
    $("authModal")?.classList.remove("is-hidden");
    $("authModal")?.setAttribute("aria-hidden", "false");
    mountAuthView();
  }

  function closeAuthModal() {
    $("authModal")?.classList.add("is-hidden");
    $("authModal")?.setAttribute("aria-hidden", "true");
  }

  function updateBetaSummary(profile) {
    const target = $("betaSummary");
    if (!target) return;
    if (!state.user) {
      target.innerHTML = "<p>Sign in to sync your beta profile and recommendation signal.</p>";
      return;
    }
    target.innerHTML = `
      <p><strong>${escapeHtml(profile?.full_name || state.user.fullName || state.user.username || "Signed-in beta user")}</strong></p>
      <p class="small-copy">${escapeHtml(profile?.email || state.user.primaryEmailAddress?.emailAddress || "")}</p>
      <p class="small-copy">Signal: ${escapeHtml(getSelectedFriendSignal())} · Plan: free_beta</p>
    `;
  }

  async function syncBetaProfile() {
    const payload = getBetaProfilePayload();
    if (!payload) {
      showToast("Sign in first so we know whose beta signal this is.");
      openAuthModal("sign-in");
      return;
    }
    const response = await apiFetch("/product/auth/sync-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }, true);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      showToast(data.detail || "Profile sync failed.");
      return;
    }
    await persistBetaSignal();
    updateBetaSummary(data.profile);
    showToast("Beta profile synced.");
  }

  async function saveSignalOnly() {
    if (!state.user) {
      showToast("Sign in first so the signal is tied to a real user.");
      openAuthModal("sign-in");
      return;
    }
    const result = await persistBetaSignal();
    if (result.persisted) {
      showToast("Recommendation signal saved.");
      updateBetaSummary();
      return;
    }
    showToast("Supabase signal capture is not configured yet.");
  }

  function mountAuthView() {
    const mount = $("authMount");
    if (!mount) return;
    if (!config.clerkPublishableKey || !window.Clerk) {
      mount.innerHTML = "<div class='result-card'><strong>Clerk not configured yet.</strong><div class='small-copy'>Add your Clerk publishable key to FRIP_BETA_CONFIG to use sign-in here.</div></div>";
      return;
    }
    mount.innerHTML = "";
    if (state.authMode === "sign-up") {
      window.Clerk.mountSignUp(mount, { signInUrl: "#" });
    } else {
      window.Clerk.mountSignIn(mount, { signUpUrl: "#" });
    }
  }

  async function initClerk() {
    if (!config.clerkPublishableKey) {
      return;
    }
    if (!window.Clerk) {
      showToast("Clerk script not ready yet.");
      return;
    }
    window.Clerk.load({
      publishableKey: config.clerkPublishableKey,
    }).then(async () => {
      state.user = window.Clerk.user || null;
      window.Clerk.addListener(async ({ user }) => {
        state.user = user || null;
        state.token = null;
        if (state.user) {
          await getToken(true);
          updateBetaSummary();
          loadWorkspace().catch(console.error);
          closeAuthModal();
        } else {
          updateBetaSummary();
        }
      });
      if (state.user) {
        await getToken(true);
        const userButton = $("clerkUserButton");
        if (userButton) {
          userButton.innerHTML = "";
          window.Clerk.mountUserButton(userButton);
        }
        closeAuthModal();
      }
      updateBetaSummary();
    }).catch((error) => {
      console.error(error);
      showToast("Clerk failed to initialize.");
    });
  }

  function setLoadingButton(button, loading, text) {
    if (!button) return;
    if (loading) {
      button.dataset.originalText = button.textContent;
      button.textContent = text;
      button.disabled = true;
    } else {
      button.textContent = button.dataset.originalText || button.textContent;
      button.disabled = false;
    }
  }

  function renderSearchResults(targetId, items, kind) {
    const target = $(targetId);
    if (!target) return;
    if (!Array.isArray(items) || !items.length) {
      target.innerHTML = "<div class='small-copy'>No results yet.</div>";
      return;
    }
    target.innerHTML = items.map((item) => {
      const source = item.source || item.source_system || item.primary_category || item.institution || "source";
      const workId = item.work_id || "";
      const arxivId = item.arxiv_id || "";
      const openLink = item.open_access_url || item.pdf_url || item.source_url || item.entry_url || "";
      return `
        <article class="result-card">
          <strong>${escapeHtml(item.title || "Untitled")}</strong>
          <div class="small-copy">${escapeHtml(source)}</div>
          <div class="small-copy">${escapeHtml(item.display_author || item.author || item.authors?.join?.(", ") || "")}</div>
          <div class="button-row compact">
            ${workId ? `<button class="ghost-button open-paper" type="button" data-work-id="${escapeHtml(workId)}">Open</button>` : ""}
            ${kind === "arxiv" && arxivId ? `<button class="ghost-button ingest-arxiv" type="button" data-arxiv-id="${escapeHtml(arxivId)}" data-mode="full">Ingest</button>` : ""}
            ${openLink ? `<a class="ghost-button" href="${escapeHtml(openLink)}" target="_blank" rel="noreferrer">Source</a>` : ""}
            ${(item.work_id || item.title) ? `<button class="ghost-button add-compare" type="button" data-work-id="${escapeHtml(item.work_id || arxivId || "")}" data-title="${escapeHtml(item.title || "Untitled")}">Compare</button>` : ""}
          </div>
        </article>
      `;
    }).join("");
  }

  async function searchPlatform() {
    const query = $("platformQuery")?.value.trim();
    if (!query) {
      showToast("Add a search query first.");
      return;
    }
    const response = await apiFetch(`/research/search?q=${encodeURIComponent(query)}&limit=20`);
    const data = await response.json().catch(() => []);
    renderSearchResults("platformResults", Array.isArray(data) ? data : [], "platform");
  }

  async function searchArxiv() {
    const query = $("arxivQuery")?.value.trim();
    if (!query) {
      showToast("Add an arXiv query first.");
      return;
    }
    const response = await apiFetch(`/research/arxiv-search?q=${encodeURIComponent(query)}&limit=20`);
    const data = await response.json().catch(() => []);
    renderSearchResults("arxivResults", Array.isArray(data) ? data : [], "arxiv");
  }

  async function searchFederated() {
    const query = $("federatedQuery")?.value.trim();
    if (!query) {
      showToast("Add a federated search query first.");
      return;
    }
    const response = await apiFetch(`/research/federated-search?q=${encodeURIComponent(query)}&limit_per_source=12&page=1`);
    const data = await response.json().catch(() => []);
    renderSearchResults("federatedResults", Array.isArray(data) ? data : [], "federated");
  }

  function renderPaper(meta, ai) {
    state.currentPaperMeta = meta;
    state.currentPaperAi = ai;
    state.currentDocumentId = meta.document_id || null;
    const badge = $("paperBadge");
    if (badge) {
      badge.textContent = meta.availability_label || "Paper ready";
      badge.classList.toggle("good", meta.has_full_document === true || meta.has_full_document === 1);
      badge.classList.toggle("warn", !(meta.has_full_document === true || meta.has_full_document === 1));
    }
    const view = $("paperView");
    if (!view) return;
    view.classList.remove("empty");
    const sourceLink = meta.pdf_url || meta.entry_url || "#";
    view.innerHTML = `
      <div class="paper-meta-grid">
        <div class="paper-meta"><strong>${escapeHtml(meta.title || "Untitled")}</strong><div class="small-copy">Title</div></div>
        <div class="paper-meta"><strong>${escapeHtml(meta.author || "Unknown")}</strong><div class="small-copy">Author</div></div>
        <div class="paper-meta"><strong>${escapeHtml(meta.institution || "Unknown")}</strong><div class="small-copy">Institution</div></div>
        <div class="paper-meta"><strong>${escapeHtml(meta.topic || meta.primary_topic || "Unknown")}</strong><div class="small-copy">Topic</div></div>
      </div>
      <div class="paper-sections">
        <div class="paper-section"><strong>Plain English</strong><p>${escapeHtml(ai.plain_english_summary || ai.executive_summary || "No summary available.")}</p></div>
        <div class="paper-section"><strong>Academic</strong><p>${escapeHtml(ai.academic_summary || ai.technical_summary || "No technical summary available.")}</p></div>
        <div class="paper-section"><strong>Methods</strong><p>${escapeHtml(ai.methods_summary || "Not available.")}</p></div>
        <div class="paper-section"><strong>Results</strong><p>${escapeHtml(ai.results_summary || "Not available.")}</p></div>
        <div class="paper-section"><strong>Limitations</strong><p>${escapeHtml(ai.limitations_summary || "Not available.")}</p></div>
        <div class="paper-section"><strong>Applications</strong><p>${escapeHtml(ai.practical_applications || "Not available.")}</p></div>
        <div class="paper-section wide"><strong>Source</strong><p><a href="${escapeHtml(sourceLink)}" target="_blank" rel="noreferrer">${escapeHtml(sourceLink)}</a></p></div>
      </div>
    `;
  }

  async function openPaper(workId) {
    if (!workId) {
      showToast("That result is missing a work id.");
      return;
    }
    const response = await apiFetch(`/research/paper/${encodeURIComponent(workId)}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      showToast(data.detail || data.message || "Paper open failed.");
      return;
    }
    renderPaper(data.metadata || {}, data.ai_summary || {});
  }

  async function askPaperQuestion() {
    if (!state.currentDocumentId) {
      showToast("Open a paper with a full document first.");
      return;
    }
    const question = $("questionInput")?.value.trim();
    if (!question) {
      showToast("Ask something first.");
      return;
    }
    const response = await apiFetch("/documents/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        document_id: state.currentDocumentId,
      }),
    });
    const data = await response.json().catch(() => ({}));
    $("qaAnswer").innerHTML = `<p>${escapeHtml(data.answer || "No answer returned.")}</p>`;
    $("qaEvidence").innerHTML = (data.evidence || []).map((item) => `
      <article class="evidence-card">
        <div class="small-copy">${escapeHtml(item.section_guess || "evidence")} · ${escapeHtml(item.chunk_id || "")}</div>
        <div>${escapeHtml(item.text || "")}</div>
      </article>
    `).join("") || "<div class='small-copy'>No evidence returned.</div>";
  }

  async function copyApaCitation() {
    if (!state.currentPaperMeta) {
      showToast("Open a paper first.");
      return;
    }
    const response = await apiFetch("/product/citations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: state.currentPaperMeta.title || "",
        authors: state.currentPaperMeta.author
          ? state.currentPaperMeta.author.split(",").map((item) => item.trim()).filter(Boolean)
          : [],
        publication_year: state.currentPaperMeta.publication_year || state.currentPaperMeta.published || "",
        institution: state.currentPaperMeta.institution || "",
        pdf_url: state.currentPaperMeta.pdf_url || "",
        entry_url: state.currentPaperMeta.entry_url || "",
        source_url: state.currentPaperMeta.entry_url || state.currentPaperMeta.pdf_url || "",
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data.apa) {
      showToast("Citation unavailable.");
      return;
    }
    await navigator.clipboard.writeText(data.apa);
    showToast("APA citation copied.");
  }

  async function workspaceAction(endpoint) {
    if (!state.currentPaperMeta) {
      showToast("Open a paper first.");
      return;
    }
    const response = await apiFetch(`/product/workspace/${encodeURIComponent(state.user?.id || "demo_user")}/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.currentPaperMeta),
    }, true);
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      showToast(data.detail || "Workspace update failed.");
      return;
    }
    showToast("Workspace updated.");
    await loadWorkspace();
  }

  function renderWorkspaceList(targetId, items, emptyText) {
    const target = $(targetId);
    if (!target) return;
    if (!items || !items.length) {
      target.innerHTML = `<div class="small-copy">${escapeHtml(emptyText)}</div>`;
      return;
    }
    target.innerHTML = items.map((item) => `
      <article class="result-card">
        <strong>${escapeHtml(item.title || "Untitled")}</strong>
        <div class="small-copy">${escapeHtml(item.source_system || item.institution || item.source_type || "")}</div>
      </article>
    `).join("");
  }

  async function loadWorkspace() {
    if (!state.user) {
      renderWorkspaceList("savedList", [], "Sign in to use the workspace.");
      renderWorkspaceList("queueList", [], "Sign in to use the queue.");
      renderWorkspaceList("favoritesList", [], "Sign in to use favorites.");
      renderWorkspaceList("uploadsList", [], "Sign in to view uploads.");
      return;
    }
    const userId = state.user.id;
    const workspaceResponse = await apiFetch(`/product/workspace/${encodeURIComponent(userId)}`, {}, true);
    const uploadsResponse = await apiFetch(`/product/uploads/${encodeURIComponent(userId)}`, {}, true);
    const workspace = await workspaceResponse.json().catch(() => ({}));
    const uploads = await uploadsResponse.json().catch(() => ({}));
    renderWorkspaceList("savedList", workspace.saved_papers || [], "No saved papers yet.");
    renderWorkspaceList("queueList", workspace.reading_queue || [], "No queued papers yet.");
    renderWorkspaceList("favoritesList", workspace.favorites || [], "No favorites yet.");
    renderWorkspaceList("uploadsList", uploads.uploads || [], "No uploads yet.");
  }

  function renderCompareList() {
    const target = $("compareList");
    if (!target) return;
    if (!state.comparePapers.length) {
      target.innerHTML = "<div class='small-copy'>No papers added yet.</div>";
      return;
    }
    target.innerHTML = state.comparePapers.map((item, index) => `
      <article class="result-card">
        <strong>${escapeHtml(item.title || "Untitled")}</strong>
        <div class="small-copy mono">${escapeHtml(item.work_id || "")}</div>
        <div class="button-row compact">
          <button class="ghost-button remove-compare" type="button" data-index="${index}">Remove</button>
        </div>
      </article>
    `).join("");
  }

  function addComparePaper(workId, title) {
    if (!workId) return;
    if (state.comparePapers.some((item) => item.work_id === workId)) {
      showToast("That paper is already in the compare list.");
      return;
    }
    state.comparePapers.push({ work_id: workId, title: title || workId });
    renderCompareList();
  }

  async function runCompare() {
    if (state.comparePapers.length < 2) {
      showToast("Add at least two papers.");
      return;
    }
    const response = await apiFetch("/research/compare-papers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        work_ids: state.comparePapers.map((item) => item.work_id),
        user_question: $("compareQuestion")?.value.trim() || "",
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.error) {
      showToast(data.detail || data.error || "Comparison failed.");
      return;
    }
    $("compareOutput").innerHTML = `
      <p><strong>Summary</strong></p>
      <p>${escapeHtml(data.comparison?.comparison_summary || "No summary returned.")}</p>
      <p class="small-copy">${escapeHtml(data.comparison?.recommended_paper?.reason || "")}</p>
    `;
  }

  async function ingestArxiv(arxivId, mode, button) {
    setLoadingButton(button, true, "Ingesting...");
    const response = await apiFetch(`/research/arxiv-ingest?arxiv_id=${encodeURIComponent(arxivId)}&mode=${encodeURIComponent(mode)}&user_id=${encodeURIComponent(state.user?.id || "beta_demo")}&plan=free`, {
      method: "POST",
    });
    const data = await response.json().catch(() => ({}));
    setLoadingButton(button, false);
    if (!response.ok) {
      showToast(data.detail || "arXiv ingest failed.");
      return;
    }
    if (data.matched_work_id) {
      await openPaper(data.matched_work_id);
    }
    showToast("arXiv ingest complete.");
  }

  async function uploadLocal(button) {
    if (!state.user) {
      showToast("Sign in to upload files.");
      openAuthModal("sign-in");
      return;
    }
    const input = $("uploadFile");
    const file = input?.files?.[0];
    if (!file) {
      showToast("Choose a file first.");
      return;
    }
    const formData = new FormData();
    formData.append("user_id", state.user.id);
    formData.append("file", file);
    setLoadingButton(button, true, "Uploading...");
    const response = await apiFetch("/product/uploads/local", {
      method: "POST",
      body: formData,
    }, true);
    setLoadingButton(button, false);
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      showToast(data.detail || "Upload failed.");
      return;
    }
    input.value = "";
    showToast("File uploaded.");
    await loadWorkspace();
  }

  async function uploadRemote(button) {
    if (!state.user) {
      showToast("Sign in to ingest URLs.");
      openAuthModal("sign-in");
      return;
    }
    const url = $("uploadUrl")?.value.trim();
    if (!url) {
      showToast("Paste a URL first.");
      return;
    }
    setLoadingButton(button, true, "Ingesting...");
    const response = await apiFetch("/product/uploads/url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: state.user.id,
        url,
      }),
    }, true);
    setLoadingButton(button, false);
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      showToast(data.detail || "URL ingest failed.");
      return;
    }
    $("uploadUrl").value = "";
    showToast("URL ingested.");
    await loadWorkspace();
  }

  function bindTabs() {
    document.querySelectorAll(".tab-button").forEach((button) => {
      button.addEventListener("click", () => {
        const tab = button.dataset.tab;
        document.querySelectorAll(".tab-button").forEach((node) => node.classList.remove("active"));
        button.classList.add("active");
        document.querySelectorAll(".search-block").forEach((panel) => {
          panel.classList.toggle("is-hidden", panel.dataset.panel !== tab);
        });
      });
    });
  }

  function bindEvents() {
    $("openSignIn")?.addEventListener("click", () => openAuthModal("sign-in"));
    $("openSignUp")?.addEventListener("click", () => openAuthModal("sign-up"));
    $("heroAuth")?.addEventListener("click", () => openAuthModal("sign-up"));
    $("closeAuth")?.addEventListener("click", closeAuthModal);
    $("showSignIn")?.addEventListener("click", () => openAuthModal("sign-in"));
    $("showSignUp")?.addEventListener("click", () => openAuthModal("sign-up"));
    $("heroExplore")?.addEventListener("click", () => {
      document.getElementById("explore")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    $("syncBetaProfile")?.addEventListener("click", syncBetaProfile);
    $("saveBetaSignal")?.addEventListener("click", saveSignalOnly);
    $("searchPlatform")?.addEventListener("click", searchPlatform);
    $("searchArxiv")?.addEventListener("click", searchArxiv);
    $("searchFederated")?.addEventListener("click", searchFederated);
    $("askPaper")?.addEventListener("click", askPaperQuestion);
    $("copyApa")?.addEventListener("click", copyApaCitation);
    $("savePaper")?.addEventListener("click", () => workspaceAction("save-paper"));
    $("queuePaper")?.addEventListener("click", () => workspaceAction("queue-paper"));
    $("favoritePaper")?.addEventListener("click", () => workspaceAction("favorite-paper"));
    $("runCompare")?.addEventListener("click", runCompare);
    $("clearCompare")?.addEventListener("click", () => {
      state.comparePapers = [];
      renderCompareList();
      $("compareOutput").innerHTML = "<p>No comparison yet.</p>";
    });
    $("refreshWorkspace")?.addEventListener("click", loadWorkspace);
    $("uploadLocal")?.addEventListener("click", (event) => uploadLocal(event.currentTarget));
    $("uploadRemote")?.addEventListener("click", (event) => uploadRemote(event.currentTarget));
    document.querySelectorAll(".explain-button").forEach((button) => {
      button.addEventListener("click", () => {
        const level = button.dataset.level || "student";
        const box = $("questionInput");
        if (!box) return;
        const base = box.value.trim() || "What is this paper really saying?";
        box.value = `${base} Explain it for a ${level} audience.`;
      });
    });
    document.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;
      if (target.matches(".open-paper")) {
        openPaper(target.dataset.workId || "");
      }
      if (target.matches(".ingest-arxiv")) {
        ingestArxiv(target.dataset.arxivId || "", target.dataset.mode || "full", target);
      }
      if (target.matches(".add-compare")) {
        addComparePaper(target.dataset.workId || "", target.dataset.title || "");
      }
      if (target.matches(".remove-compare")) {
        const index = Number(target.dataset.index || -1);
        if (index >= 0) {
          state.comparePapers.splice(index, 1);
          renderCompareList();
        }
      }
    });
  }

  function init() {
    initTheme();
    initSupabase();
    bindTabs();
    bindEvents();
    renderCompareList();
    updateBetaSummary();
    initClerk();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
