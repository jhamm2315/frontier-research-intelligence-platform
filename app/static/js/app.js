(function () {
  const config = window.__FRIP_CONFIG__ || {};
  const state = {
    userId: localStorage.getItem("frip-user-id") || "demo_user",
    userPlan: localStorage.getItem("frip-selected-plan") || "free",
    clerkSessionToken: null,
    currentDocumentId: null,
    currentPaperMeta: null,
    currentPaperAi: null,
    comparePapers: [],
    lastComparisonPayload: null,
    currentProjectId: localStorage.getItem("frip-current-project-id") || null,
    explainLevel: "college",
    platformFilter: "all",
  };

  const STORE_KEYS = {
    recents: "frip_recent_papers",
    notes: "frip_notes_cache",
    authProfile: "frip_auth_profile",
  };

  function $(id) {
    return document.getElementById(id);
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function getStore(key, fallback) {
    try {
      const storage = key === STORE_KEYS.authProfile ? sessionStorage : localStorage;
      return JSON.parse(storage.getItem(key) || "null") ?? fallback;
    } catch {
      return fallback;
    }
  }

  function setStore(key, value) {
    const storage = key === STORE_KEYS.authProfile ? sessionStorage : localStorage;
    storage.setItem(key, JSON.stringify(value));
  }

  async function getClerkSessionToken(forceRefresh = false) {
    if (!window.Clerk?.session) return null;
    if (!forceRefresh && state.clerkSessionToken) {
      return state.clerkSessionToken;
    }
    try {
      const token = await window.Clerk.session.getToken();
      state.clerkSessionToken = token || null;
      return state.clerkSessionToken;
    } catch (error) {
      console.error("Clerk token fetch failed", error);
      state.clerkSessionToken = null;
      return null;
    }
  }

  async function authHeaders(forceRefresh = false) {
    const token = await getClerkSessionToken(forceRefresh);
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  async function authenticatedFetch(url, options = {}, forceRefresh = false) {
    const tokenHeaders = await authHeaders(forceRefresh);
    return fetch(url, {
      ...options,
      headers: {
        ...(options.headers || {}),
        ...tokenHeaders,
      },
    });
  }

  function isAuthFailure(response) {
    return response.status === 401 || response.status === 403;
  }

  function promptSignIn(message = "Sign in required for that action.") {
    showToast(message);
    if (document.body.dataset.page !== "auth") {
      const plan = localStorage.getItem("frip-selected-plan") || state.userPlan || "student";
      window.setTimeout(() => {
        window.location.href = `/auth?plan=${encodeURIComponent(plan)}&mode=sign-in`;
      }, 450);
    }
  }

  async function guardedProductFetch(url, options = {}, forceRefresh = false, failureMessage = "Sign in required for that action.") {
    const response = await authenticatedFetch(url, options, forceRefresh);
    if (isAuthFailure(response)) {
      promptSignIn(failureMessage);
    }
    return response;
  }

  function showToast(message) {
    let toast = document.querySelector(".toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.className = "toast";
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    clearTimeout(window.__fripToastTimeout);
    window.__fripToastTimeout = setTimeout(() => {
      toast.remove();
    }, 2400);
  }

  function setLoading(button, isLoading, text) {
    if (!button) return;
    if (isLoading) {
      button.dataset.originalText = button.innerHTML;
      button.innerHTML = text || "Loading...";
      button.disabled = true;
    } else {
      button.innerHTML = button.dataset.originalText || button.innerHTML;
      button.disabled = false;
    }
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("frip-theme", theme);
  }

  function initTheme() {
    applyTheme(localStorage.getItem("frip-theme") || "dark");
    $("themeToggle")?.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "dark";
      applyTheme(current === "dark" ? "light" : "dark");
    });
  }

  async function initClerk() {
    const publishableKey = config.clerkPublishableKey;
    if (!publishableKey) {
      if (document.body.dataset.page === "auth") {
        bindAuthToggle();
      }
      return;
    }

    if (!window.Clerk) {
      let attempts = 0;
      const interval = window.setInterval(() => {
        attempts += 1;
        if (window.Clerk) {
          window.clearInterval(interval);
          initClerk();
        } else if (attempts >= 20) {
          window.clearInterval(interval);
          if (document.body.dataset.page === "auth") {
            bindAuthToggle();
            renderAuthFallback("Clerk did not finish loading. Refresh and try again.");
          }
        }
      }, 250);
      return;
    }

    window.Clerk.load().then(async () => {
      if (window.Clerk.user) {
        state.userId = window.Clerk.user.id;
        localStorage.setItem("frip-user-id", state.userId);
        await getClerkSessionToken(true);
        mountUserButton();
        try {
          await syncUserFromClerk();
        } catch (error) {
          console.error("Profile sync failed", error);
        }
      } else {
        state.clerkSessionToken = null;
        mountUserButton();
      }

      if (document.body.dataset.page === "auth") {
        mountAuthView();
      }
    }).catch((error) => {
      console.error("Clerk init failed", error);
      if (document.body.dataset.page === "auth") {
        renderAuthFallback("Clerk is not configured yet. This page still preserves plan selection cleanly.");
      }
    });
  }

  function mountUserButton() {
    const slot = $("clerk-user-button");
    if (!slot) return;
    slot.innerHTML = "";
    if (window.Clerk?.user) {
      window.Clerk.mountUserButton(slot);
      const cta = document.querySelector('.topbar-actions a[href="/auth"]');
      if (cta) cta.textContent = "Account";
    }
  }

  async function syncUserFromClerk() {
    if (!window.Clerk?.user) return null;
    const user = window.Clerk.user;
    const authProfile = getStore(STORE_KEYS.authProfile, {});
    const payload = {
      clerk_user_id: user.id,
      username: authProfile.username || user.username || "",
      email: user.primaryEmailAddress?.emailAddress || user.emailAddresses?.[0]?.emailAddress || "",
      full_name: authProfile.full_name || user.fullName || `${user.firstName || ""} ${user.lastName || ""}`.trim(),
      first_name: user.firstName || "",
      last_name: user.lastName || "",
      avatar_url: user.imageUrl || "",
      institution: authProfile.institution || "",
      role_title: authProfile.role_title || "",
      github_url: authProfile.github_url || "",
      linkedin_url: authProfile.linkedin_url || "",
      research_interests: authProfile.research_interests || [],
      onboarding_notes: authProfile.onboarding_notes || "",
      plan: localStorage.getItem("frip-selected-plan") || state.userPlan || "free",
      auth_provider: "clerk",
    };
    const response = await guardedProductFetch("/product/auth/sync-profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }, true, "We need a verified session before we can sync your profile.");
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || `Profile sync failed (${response.status})`);
    }
    state.userId = payload.clerk_user_id;
    state.userPlan = data.profile?.plan || payload.plan;
    localStorage.setItem("frip-user-id", state.userId);
    localStorage.setItem("frip-selected-plan", state.userPlan);
    await getClerkSessionToken(true);
    return data;
  }

  function collectAuthProfileForm() {
    const interests = ($("authResearchInterests")?.value || "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    return {
      username: $("authUsername")?.value.trim() || "",
      full_name: $("authFullName")?.value.trim() || "",
      institution: $("authInstitution")?.value.trim() || "",
      role_title: $("authRoleTitle")?.value.trim() || "",
      research_interests: interests,
      github_url: $("authGithubUrl")?.value.trim() || "",
      linkedin_url: $("authLinkedinUrl")?.value.trim() || "",
      onboarding_notes: $("authIntroNote")?.value.trim() || "",
      billing_name: $("billingName")?.value.trim() || "",
      billing_email: $("billingEmail")?.value.trim() || "",
      billing_country: $("billingCountry")?.value.trim() || "",
      billing_postal_code: $("billingPostalCode")?.value.trim() || "",
    };
  }

  function hydrateAuthProfileForm() {
    const profile = getStore(STORE_KEYS.authProfile, {});
    if ($("authUsername")) $("authUsername").value = profile.username || "";
    if ($("authFullName")) $("authFullName").value = profile.full_name || "";
    if ($("authInstitution")) $("authInstitution").value = profile.institution || "";
    if ($("authRoleTitle")) $("authRoleTitle").value = profile.role_title || "";
    if ($("authResearchInterests")) $("authResearchInterests").value = (profile.research_interests || []).join(", ");
    if ($("authGithubUrl")) $("authGithubUrl").value = profile.github_url || "";
    if ($("authLinkedinUrl")) $("authLinkedinUrl").value = profile.linkedin_url || "";
    if ($("authIntroNote")) $("authIntroNote").value = profile.onboarding_notes || "";
    if ($("billingName")) $("billingName").value = profile.billing_name || "";
    if ($("billingEmail")) $("billingEmail").value = profile.billing_email || "";
    if ($("billingCountry")) $("billingCountry").value = profile.billing_country || "";
    if ($("billingPostalCode")) $("billingPostalCode").value = profile.billing_postal_code || "";
  }

  function bindAuthProfileActions() {
    $("authSaveProfile")?.addEventListener("click", () => {
      setStore(STORE_KEYS.authProfile, collectAuthProfileForm());
      showToast("Profile details saved for sign-up and checkout.");
    });
    $("connectGithub")?.addEventListener("click", () => {
      showToast("GitHub connection can be wired through Clerk or OAuth next.");
    });
    $("connectLinkedin")?.addEventListener("click", () => {
      showToast("LinkedIn connection can be wired through OAuth next.");
    });
  }

  function renderAuthFallback(message) {
    const mount = $("clerkMount");
    if (mount) {
      mount.innerHTML = `<div class="small-copy">${escapeHtml(message)}</div>`;
    }
  }

  function getSelectedPlan() {
    const params = new URLSearchParams(window.location.search);
    return params.get("plan") || localStorage.getItem("frip-selected-plan") || "student";
  }

  function getAuthMode() {
    const params = new URLSearchParams(window.location.search);
    return params.get("mode") === "sign-in" ? "sign-in" : "sign-up";
  }

  function updateAuthInsight() {
    const panel = $("authInsight");
    if (!panel) return;
    const recents = getStore(STORE_KEYS.recents, []);
    const notes = getStore(STORE_KEYS.notes, []);
    const recentTopics = recents.map((item) => item.topic || item.primary_topic).filter(Boolean);
    const noteHint = notes[0]?.content;
    let quote = "Sharp tools reward sharp curiosity.";
    let meta = "No history yet. We default to civilized optimism.";

    if (recentTopics.length) {
      quote = `You keep circling ${recentTopics[0]}. That usually means the interesting work is nearby.`;
      meta = "Personalized from your recent paper trail.";
    } else if (noteHint) {
      quote = "Your notes suggest you are not browsing. You are building.";
      meta = "Pulled from your recent workspace note.";
    }

    panel.innerHTML = `
      <p class="quote-kicker">Research insight</p>
      <blockquote>${escapeHtml(quote)}</blockquote>
      <p class="quote-meta">${escapeHtml(meta)}</p>
    `;
  }

  function mountAuthView() {
    const mount = $("clerkMount");
    if (!mount) return;

    const plan = getSelectedPlan();
    const mode = getAuthMode();
    state.userPlan = plan;
    localStorage.setItem("frip-selected-plan", plan);
    const planLabel = $("selectedPlanLabel");
    if (planLabel) {
      const match = (config.plans || []).find((item) => item.code === plan);
      planLabel.textContent = match?.name || plan;
    }

    const heading = $("authModeHeading");
    if (heading) {
      heading.textContent = mode === "sign-in" ? "Sign in" : "Create account";
    }

    updateAuthInsight();

    bindAuthToggle();
    hydrateAuthProfileForm();
    bindAuthProfileActions();

    if (!window.Clerk || !config.clerkPublishableKey) {
      renderAuthFallback("Clerk publishable key is missing. Plan capture still works.");
      return;
    }

    mount.innerHTML = "";
    if (mode === "sign-in") {
      window.Clerk.mountSignIn(mount, {
        signUpUrl: `/auth?plan=${encodeURIComponent(plan)}&mode=sign-up`,
      });
    } else {
      window.Clerk.mountSignUp(mount, {
        signInUrl: `/auth?plan=${encodeURIComponent(plan)}&mode=sign-in`,
      });
    }
  }

  function bindAuthToggle() {
    $("authToggle")?.addEventListener("click", () => {
      const plan = getSelectedPlan();
      const nextMode = getAuthMode() === "sign-in" ? "sign-up" : "sign-in";
      window.location.href = `/auth?plan=${encodeURIComponent(plan)}&mode=${encodeURIComponent(nextMode)}`;
    });
  }

  function renderList(elementId, items, emptyText, actionRenderer) {
    const el = $(elementId);
    if (!el) return;
    if (!items || !items.length) {
      el.innerHTML = `<div class="small-copy">${escapeHtml(emptyText)}</div>`;
      return;
    }
    el.innerHTML = items.map((item, index) => `
      <div class="result-card">
        <strong>${escapeHtml(item.title || item.paper_title || "Untitled")}</strong>
        <div class="small-copy">${escapeHtml(item.topic || item.source_system || item.institution || "")}</div>
        ${actionRenderer ? actionRenderer(item, index) : ""}
      </div>
    `).join("");
  }

  function pushRecentPaper(meta) {
    const recents = getStore(STORE_KEYS.recents, []);
    const next = [{ ...meta }, ...recents].filter((item, index, all) => {
      const key = item.work_id || item.document_id || item.title;
      return all.findIndex((row) => (row.work_id || row.document_id || row.title) === key) === index;
    }).slice(0, 12);
    setStore(STORE_KEYS.recents, next);
  }

  async function loadWorkspace() {
    const response = await guardedProductFetch(
      `/product/workspace/${encodeURIComponent(state.userId)}`,
      {},
      false,
      "Sign in to load your workspace."
    );
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Workspace load failed");
    return data;
  }

  async function loadWorkspacePage() {
    try {
      const workspace = await loadWorkspace();
      renderList("savedPapersList", workspace.saved_papers || [], "No saved papers yet.");
      renderList("readingQueueList", workspace.reading_queue || [], "No queue yet.");
      renderList("favoritesList", workspace.favorites || [], "No favorites yet.");
    } catch (error) {
      console.error(error);
      renderList("savedPapersList", [], "Workspace unavailable.");
      renderList("readingQueueList", [], "Workspace unavailable.");
      renderList("favoritesList", [], "Workspace unavailable.");
    }

    renderList("recentPapersList", getStore(STORE_KEYS.recents, []), "No recent papers yet.");
    renderNotes();
    await renderBuilderPreview();
    await loadComparisonHistory();
    await loadUploadedSources();
  }

  function renderNotes() {
    renderList("notesList", getStore(STORE_KEYS.notes, []), "No notes yet.");
  }

  async function saveQuickNote() {
    const noteEl = $("quickNote");
    const content = noteEl?.value.trim();
    if (!content) {
      showToast("Add a note first.");
      return;
    }

    const payload = {
      paper_work_id: state.currentPaperMeta?.work_id || null,
      paper_document_id: state.currentPaperMeta?.document_id || null,
      paper_title: state.currentPaperMeta?.title || "Workspace note",
      content,
      tags: [],
    };

    const response = await guardedProductFetch(`/product/workspace/${encodeURIComponent(state.userId)}/note`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }, false, "Sign in to save notes.");

    if (!response.ok) {
      showToast("Note save failed.");
      return;
    }

    const notes = getStore(STORE_KEYS.notes, []);
    notes.unshift(payload);
    setStore(STORE_KEYS.notes, notes.slice(0, 20));
    if (noteEl) noteEl.value = "";
    renderNotes();
    showToast("Note saved.");
  }

  async function ensureProject() {
    if (state.currentProjectId) return state.currentProjectId;
    const title = $("builderTitle")?.value.trim() || "Untitled Project";
    const response = await guardedProductFetch(`/product/authoring/${encodeURIComponent(state.userId)}/projects`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, project_type: "research_paper" }),
    }, false, "Sign in to create a draft project.");
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Project creation failed");
    state.currentProjectId = data.project_id;
    localStorage.setItem("frip-current-project-id", state.currentProjectId);
    return state.currentProjectId;
  }

  async function saveBuilderDraft() {
    const title = $("builderTitle")?.value.trim() || "Untitled Project";
    const abstract = $("builderAbstract")?.value.trim() || "";
    const section = $("builderSection")?.value.trim() || "";
    if (!title && !abstract && !section) {
      showToast("Add draft content first.");
      return;
    }

    const projectId = await ensureProject();
    const response = await guardedProductFetch(`/product/authoring/${encodeURIComponent(state.userId)}/projects/${encodeURIComponent(projectId)}/draft`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, abstract, content: section }),
    }, false, "Sign in to save your draft.");
    if (!response.ok) {
      showToast("Draft save failed.");
      return;
    }
    renderBuilderPreview();
    showToast("Draft saved.");
  }

  async function renderBuilderPreview() {
    const preview = $("builderPreview");
    if (!preview) return;
    const title = $("builderTitle")?.value.trim() || "Untitled Project";
    const abstract = $("builderAbstract")?.value.trim() || "";
    const section = $("builderSection")?.value.trim() || "";
    preview.innerHTML = `
      <strong>${escapeHtml(title)}</strong>
      ${abstract ? `<p>${escapeHtml(abstract)}</p>` : "<p class='small-copy'>No abstract yet.</p>"}
      ${section ? `<div>${escapeHtml(section).replace(/\n/g, "<br>")}</div>` : "<div class='small-copy'>No draft section yet.</div>"}
    `;
  }

  async function copyBuilderMarkdown() {
    const title = $("builderTitle")?.value.trim() || "Untitled Project";
    const abstract = $("builderAbstract")?.value.trim() || "";
    const section = $("builderSection")?.value.trim() || "";
    await navigator.clipboard.writeText(`# ${title}\n\n## Abstract\n${abstract}\n\n## Draft\n${section}`);
    showToast("Markdown copied.");
  }

  async function copyBuilderHtml() {
    const title = $("builderTitle")?.value.trim() || "Untitled Project";
    const abstract = $("builderAbstract")?.value.trim() || "";
    const section = $("builderSection")?.value.trim() || "";
    await navigator.clipboard.writeText(`<h1>${escapeHtml(title)}</h1><h2>Abstract</h2><p>${escapeHtml(abstract)}</p><h2>Draft</h2><p>${escapeHtml(section)}</p>`);
    showToast("HTML copied.");
  }

  async function downloadExport(kind) {
    const projectId = await ensureProject();
    const response = await guardedProductFetch(
      `/product/authoring/${encodeURIComponent(state.userId)}/projects/${encodeURIComponent(projectId)}/export/${kind}`,
      {},
      false,
      `Sign in to export ${kind.toUpperCase()} files.`
    );
    if (!response.ok) {
      showToast(`${kind.toUpperCase()} export failed.`);
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `frontier_research_project.${kind}`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    showToast(`${kind.toUpperCase()} exported.`);
  }

  async function loadUploadedSources() {
    const el = $("uploadedSourcesList");
    if (!el) return;
    const response = await guardedProductFetch(
      `/product/uploads/${encodeURIComponent(state.userId)}`,
      {},
      false,
      "Sign in to view uploaded sources."
    );
    const data = await response.json().catch(() => ({}));
    const uploads = data.uploads || [];
    renderList("uploadedSourcesList", uploads, "No uploaded sources yet.", (item) => {
      return `<div class="button-row compact"><button class="ghost-button uploaded-open" type="button" data-document-id="${escapeHtml(item.document_id || "")}">Open</button></div>`;
    });
  }

  async function uploadLocalFile(button) {
    const input = $("uploadFileInput");
    const file = input?.files?.[0];
    if (!file) {
      showToast("Choose a file first.");
      return;
    }
    const formData = new FormData();
    formData.append("user_id", state.userId);
    formData.append("plan", state.userPlan);
    formData.append("file", file);
    setLoading(button, true, "Uploading...");
    const response = await guardedProductFetch(
      "/product/uploads/local",
      { method: "POST", body: formData },
      false,
      "Sign in to upload files."
    );
    setLoading(button, false);
    if (!response.ok) {
      showToast("Upload failed.");
      return;
    }
    input.value = "";
    await loadUploadedSources();
    showToast("File uploaded.");
  }

  async function uploadUrl(button) {
    const input = $("urlIngestInput");
    const url = input?.value.trim();
    if (!url) {
      showToast("Paste a URL first.");
      return;
    }
    setLoading(button, true, "Ingesting...");
    const response = await guardedProductFetch("/product/uploads/url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: state.userId, plan: state.userPlan, url }),
    }, false, "Sign in to ingest URLs.");
    setLoading(button, false);
    if (!response.ok) {
      showToast("URL ingest failed.");
      return;
    }
    input.value = "";
    await loadUploadedSources();
    showToast("URL ingested.");
  }

  async function openUploadedDocument(documentId) {
    const response = await guardedProductFetch(
      `/product/uploads/document/${encodeURIComponent(documentId)}`,
      {},
      false,
      "Sign in to open uploaded documents."
    );
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      showToast("Uploaded document unavailable.");
      return;
    }
    hydratePaperCard(data.metadata || {}, data.ai_summary || {});
  }

  function hydratePaperCard(meta, ai) {
    state.currentDocumentId = meta.document_id || null;
    state.currentPaperMeta = meta;
    state.currentPaperAi = ai;
    const card = $("paperCard");
    if (!card) return;
    card.hidden = false;
    $("paperTitle").textContent = meta.title || "Untitled";
    $("paperAuthor").textContent = meta.author || "Unknown";
    $("paperInstitution").textContent = meta.institution || "Unknown";
    $("paperTopic").textContent = meta.topic || meta.primary_topic || "Unknown";
    $("paperCitation").textContent = meta.citation || "Unavailable";
    $("paperPublished").textContent = meta.published || meta.publication_year || "Unknown";
    $("paperSource").textContent = meta.source_system || "Unknown";
    $("plainEnglishSummary").textContent = ai.plain_english_summary || ai.executive_summary || "No summary available.";
    $("academicSummary").textContent = ai.academic_summary || ai.technical_summary || "No academic summary available.";
    $("methodsSummary").textContent = ai.methods_summary || "Not available.";
    $("resultsSummary").textContent = ai.results_summary || "Not available.";
    $("limitationsSummary").textContent = ai.limitations_summary || "Not available.";
    $("practicalApplications").textContent = ai.practical_applications || "Not available.";
    $("suggestedTopics").textContent = ai.suggested_topics || "Not available.";
    $("citationGuidance").textContent = ai.citation_guidance || "Not available.";
    const badge = $("availabilityBadge");
    badge.textContent = meta.availability_label || "Available";
    const sourceLink = $("paperPdfUrl");
    sourceLink.href = meta.pdf_url || meta.entry_url || "#";
    sourceLink.textContent = meta.pdf_url || meta.entry_url || "No source link available";
    const categoryWrap = $("paperCategories");
    categoryWrap.innerHTML = "";
    String(meta.categories || "").split(",").map((item) => item.trim()).filter(Boolean).forEach((item) => {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.textContent = item;
      categoryWrap.appendChild(chip);
    });
    pushRecentPaper(meta);
    card.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderResultCard(item, actionsHtml) {
    return `
      <article class="result-card">
        <div class="small-copy">${escapeHtml(item.source || item.source_system || item.publication_year || "")}</div>
        <strong>${escapeHtml(item.title || "Untitled")}</strong>
        <div class="small-copy">${escapeHtml(item.display_topic || item.primary_topic || item.topic || "")}</div>
        <div class="small-copy">${escapeHtml(item.display_author || item.author || item.institution || "")}</div>
        ${actionsHtml}
      </article>
    `;
  }

  async function searchPapers() {
    const query = $("paperSearch")?.value.trim();
    const target = $("searchResultsContent");
    if (!query || !target) return;
    target.innerHTML = "<div class='small-copy'>Searching catalog...</div>";
    const response = await fetch(`/research/search?q=${encodeURIComponent(query)}&limit=20&user_id=${encodeURIComponent(state.userId)}`);
    const rows = await response.json().catch(() => []);
    const filtered = Array.isArray(rows) ? rows.filter((row) => {
      if (state.platformFilter === "full") return row.has_full_document === 1 || row.has_full_document === true;
      if (state.platformFilter === "metadata") return !(row.has_full_document === 1 || row.has_full_document === true);
      return true;
    }) : [];
    target.innerHTML = filtered.length ? filtered.map((item) => renderResultCard(item, `<div class="button-row compact"><button class="ghost-button open-paper" type="button" data-work-id="${escapeHtml(item.work_id || "")}">Open</button></div>`)).join("") : "<div class='small-copy'>No matching papers.</div>";
  }

  async function searchArxiv() {
    const query = $("arxivSearch")?.value.trim();
    const target = $("arxivResultsContent");
    if (!query || !target) return;
    target.innerHTML = "<div class='small-copy'>Searching arXiv...</div>";
    const response = await fetch(`/research/arxiv-search?q=${encodeURIComponent(query)}&limit=25&user_id=${encodeURIComponent(state.userId)}`);
    const rows = await response.json().catch(() => []);
    target.innerHTML = (rows || []).length ? rows.map((item) => renderResultCard(item, `
      <div class="button-row compact">
        <button class="ghost-button ingest-arxiv" type="button" data-mode="abstract" data-arxiv-id="${escapeHtml(item.arxiv_id || "")}">Quick ingest</button>
        <button class="primary-button ingest-arxiv" type="button" data-mode="full" data-arxiv-id="${escapeHtml(item.arxiv_id || "")}">Full ingest</button>
      </div>
    `)).join("") : "<div class='small-copy'>No arXiv results.</div>";
  }

  async function searchFederated() {
    const query = $("federatedSearch")?.value.trim();
    const target = $("federatedResultsContent");
    if (!query || !target) return;
    target.innerHTML = "<div class='small-copy'>Searching institutions...</div>";
    const response = await fetch(`/research/federated-search?q=${encodeURIComponent(query)}&limit_per_source=25&page=1&user_id=${encodeURIComponent(state.userId)}`);
    const rows = await response.json().catch(() => []);
    target.innerHTML = (rows || []).length ? rows.map((item) => renderResultCard(item, item.open_access_url || item.pdf_url || item.source_url ? `<div class="button-row compact"><a class="ghost-button" target="_blank" rel="noreferrer" href="${escapeHtml(item.open_access_url || item.pdf_url || item.source_url)}">Open source</a></div>` : "")).join("") : "<div class='small-copy'>No federated results.</div>";
  }

  async function ingestArxiv(arxivId, mode, button) {
    setLoading(button, true, mode === "full" ? "Ingesting..." : "Quick ingest...");
    const response = await fetch(`/research/arxiv-ingest?arxiv_id=${encodeURIComponent(arxivId)}&mode=${encodeURIComponent(mode)}&user_id=${encodeURIComponent(state.userId)}&plan=${encodeURIComponent(state.userPlan)}`, { method: "POST" });
    const data = await response.json().catch(() => ({}));
    setLoading(button, false);
    if (!response.ok) {
      showToast(data.detail || "Ingest failed.");
      return;
    }
    showToast("arXiv paper ingested.");
    if (data.matched_work_id) {
      await openPaper(data.matched_work_id);
    }
  }

  async function openPaper(workId) {
    const response = await fetch(`/research/paper/${encodeURIComponent(workId)}?user_id=${encodeURIComponent(state.userId)}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.message) {
      showToast(data.message || "Paper unavailable.");
      return;
    }
    hydratePaperCard(data.metadata || {}, data.ai_summary || {});
  }

  async function askQuestion() {
    if (!state.currentDocumentId) {
      showToast("Open a paper with a document first.");
      return;
    }
    const question = $("question")?.value.trim();
    if (!question) {
      showToast("Ask something first.");
      return;
    }
    const response = await fetch("/documents/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        document_id: state.currentDocumentId,
        user_id: state.userId,
      }),
    });
    const data = await response.json().catch(() => ({}));
    $("qaPanel").hidden = false;
    $("answer").innerHTML = `<p>${escapeHtml(data.answer || "No answer returned.")}</p>`;
    const evidence = data.evidence || [];
    $("evidence").innerHTML = evidence.length ? evidence.map((item) => `
      <article class="evidence-card">
        <div class="small-copy">${escapeHtml(item.section_guess || "evidence")} · score ${escapeHtml(item.score || "")}</div>
        <div>${escapeHtml(item.text || "")}</div>
      </article>
    `).join("") : "<div class='small-copy'>No evidence returned.</div>";
  }

  async function copyCitation(format) {
    if (!state.currentPaperMeta) {
      showToast("Open a paper first.");
      return;
    }
    const response = await fetch("/product/citations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: state.currentPaperMeta.title || "",
        authors: state.currentPaperMeta.author ? state.currentPaperMeta.author.split(",").map((value) => value.trim()).filter(Boolean) : [],
        publication_year: state.currentPaperMeta.publication_year || state.currentPaperMeta.published || "",
        institution: state.currentPaperMeta.institution || "",
        pdf_url: state.currentPaperMeta.pdf_url || "",
        entry_url: state.currentPaperMeta.entry_url || "",
        source_url: state.currentPaperMeta.entry_url || state.currentPaperMeta.pdf_url || "",
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data[format]) {
      showToast("Citation unavailable.");
      return;
    }
    await navigator.clipboard.writeText(data[format]);
    showToast(`${format.toUpperCase()} copied.`);
  }

  async function savePaperAction(endpoint) {
    if (!state.currentPaperMeta) {
      showToast("Open a paper first.");
      return;
    }
    const response = await guardedProductFetch(`/product/workspace/${encodeURIComponent(state.userId)}/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.currentPaperMeta),
    }, false, "Sign in to update your workspace.");
    if (!response.ok) {
      showToast("Workspace update failed.");
      return;
    }
    if (document.body.dataset.page === "workspace") {
      await loadWorkspacePage();
    }
    showToast("Workspace updated.");
  }

  function renderComparePapers() {
    const el = $("comparePapersList");
    if (!el) return;
    if (!state.comparePapers.length) {
      el.innerHTML = "<div class='small-copy'>No papers selected yet.</div>";
      return;
    }
    el.innerHTML = state.comparePapers.map((paper, index) => `
      <div class="result-card">
        <strong>${escapeHtml(paper.title || "Untitled")}</strong>
        <div class="small-copy">${escapeHtml(paper.work_id || "")}</div>
        <div class="button-row compact">
          <button class="ghost-button remove-compare" type="button" data-index="${index}">Remove</button>
        </div>
      </div>
    `).join("");
  }

  async function runMultiPaperCompare() {
    if (state.comparePapers.length < 2) {
      showToast("Add at least two papers.");
      return;
    }
    const response = await fetch("/research/compare-papers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        work_ids: state.comparePapers.map((item) => item.work_id),
        user_question: $("compareQuestion")?.value.trim() || "",
        user_id: state.userId,
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.error) {
      showToast(data.error || "Comparison failed.");
      return;
    }
    state.lastComparisonPayload = {
      work_ids: state.comparePapers.map((item) => item.work_id),
      paper_titles: state.comparePapers.map((item) => item.title),
      question: $("compareQuestion")?.value.trim() || "",
      summary: data.comparison?.comparison_summary || "",
    };
    $("compareResults").hidden = false;
    $("compareSummary").innerHTML = `<p>${escapeHtml(data.comparison?.comparison_summary || "No summary.")}</p>`;
    $("compareThemes").innerHTML = renderBulletList(data.comparison?.common_themes);
    $("compareDifferences").innerHTML = renderBulletList(data.comparison?.key_differences);
    $("compareMethods").innerHTML = `<p>${escapeHtml(data.comparison?.methods_comparison || "Not available.")}</p>`;
    $("compareResultsText").innerHTML = `<p>${escapeHtml(data.comparison?.results_comparison || "Not available.")}</p>`;
    $("compareLimitations").innerHTML = `<p>${escapeHtml(data.comparison?.limitations_comparison || "Not available.")}</p>`;
    $("compareBestStudents").innerHTML = `<p>${escapeHtml(data.comparison?.best_for_students || "Not available.")}</p>`;
    $("compareBestResearchers").innerHTML = `<p>${escapeHtml(data.comparison?.best_for_researchers || "Not available.")}</p>`;
    $("compareBestPractical").innerHTML = `<p>${escapeHtml(data.comparison?.best_for_practical_use || "Not available.")}</p>`;
    $("compareRecommended").innerHTML = `<p>${escapeHtml(data.comparison?.recommended_paper?.reason || "No recommendation.")}</p>`;
    showToast("Comparison complete.");
  }

  function renderBulletList(items) {
    if (!items || !items.length) {
      return "<div class='small-copy'>Not available.</div>";
    }
    return `<ul class="tight-list">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
  }

  async function saveComparison() {
    if (!state.lastComparisonPayload) {
      showToast("Run a comparison first.");
      return;
    }
    const response = await guardedProductFetch(`/product/workspace/${encodeURIComponent(state.userId)}/comparisons`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: `Comparison of ${state.lastComparisonPayload.paper_titles.length} papers`,
        ...state.lastComparisonPayload,
      }),
    }, false, "Sign in to save comparisons.");
    if (!response.ok) {
      showToast("Comparison save failed.");
      return;
    }
    showToast("Comparison saved.");
    await loadComparisonHistory();
  }

  async function loadComparisonHistory() {
    const el = $("comparisonHistoryList");
    if (!el) return;
    const response = await guardedProductFetch(
      `/product/workspace/${encodeURIComponent(state.userId)}/comparisons`,
      {},
      false,
      "Sign in to load comparison history."
    );
    const data = await response.json().catch(() => ({}));
    const items = data.comparisons || [];
    renderList("comparisonHistoryList", items, "No saved comparisons yet.", (item) => `
      <div class="button-row compact">
        <button class="ghost-button reload-comparison" type="button" data-comparison-id="${escapeHtml(item.id || item.comparison_id || "")}">Reload</button>
        <button class="ghost-button delete-comparison" type="button" data-comparison-id="${escapeHtml(item.id || item.comparison_id || "")}">Delete</button>
      </div>
    `);
    window.__fripComparisonCache = items;
  }

  async function deleteComparison(id) {
    const response = await guardedProductFetch(`/product/workspace/${encodeURIComponent(state.userId)}/comparisons/${encodeURIComponent(id)}`, {
      method: "DELETE",
    }, false, "Sign in to delete saved comparisons.");
    if (!response.ok) {
      showToast("Delete failed.");
      return;
    }
    showToast("Comparison deleted.");
    await loadComparisonHistory();
  }

  function reloadComparison(id) {
    const item = (window.__fripComparisonCache || []).find((row) => (row.id || row.comparison_id) === id);
    if (!item) {
      showToast("Comparison not found.");
      return;
    }
    state.comparePapers = (item.work_ids || []).map((workId, index) => ({
      work_id: workId,
      title: item.paper_titles?.[index] || workId,
    }));
    renderComparePapers();
    if ($("compareQuestion")) $("compareQuestion").value = item.question || "";
    showToast("Comparison reloaded.");
  }

  function bindPricingActions() {
    document.querySelectorAll('a[href^="/auth?plan="]').forEach((link) => {
      link.addEventListener("click", () => {
        const href = new URL(link.href, window.location.origin);
        const plan = href.searchParams.get("plan") || "student";
        localStorage.setItem("frip-selected-plan", plan);
      });
    });

    document.querySelectorAll(".pricing-checkout").forEach((link) => {
      link.addEventListener("click", async (event) => {
        const plan = link.dataset.plan || "student";
        localStorage.setItem("frip-selected-plan", plan);
        if (!(window.Clerk?.user && state.userId && state.userId !== "demo_user")) {
          return;
        }
        event.preventDefault();
        try {
          const response = await guardedProductFetch("/product/billing/checkout-session", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              plan_code: plan,
              clerk_user_id: state.userId,
              email: window.Clerk.user.primaryEmailAddress?.emailAddress || window.Clerk.user.emailAddresses?.[0]?.emailAddress || "",
            }),
          }, true, "Sign in before starting checkout.");
          const data = await response.json().catch(() => ({}));
          if (response.ok && data.success && data.checkout_url) {
            window.location.href = data.checkout_url;
            return;
          }
          showToast(data.detail || "Stripe checkout is not configured yet. Continuing to account setup.");
          window.location.href = link.href;
        } catch (error) {
          console.error(error);
          showToast("Checkout handoff failed. Continuing to account setup.");
          window.location.href = link.href;
        }
      });
    });

    document.querySelectorAll('a[href="/admin-controls"]').forEach((link) => {
      link.addEventListener("click", async (event) => {
        if (!(state.userId && state.userId !== "demo_user")) {
          event.preventDefault();
          showToast("Admin access requires an authenticated admin user.");
          return;
        }
        event.preventDefault();
        const token = await getClerkSessionToken(true);
        if (!token) {
          showToast("We could not verify your Clerk session yet. Try again.");
          return;
        }
        window.location.href = link.href;
      });
    });
  }

  function parseLineList(text) {
    return String(text || "").split("\n").map((line) => line.trim()).filter(Boolean);
  }

  function parseSourceIntervals(text) {
    const mapping = {};
    parseLineList(text).forEach((line) => {
      const [source, rawMinutes] = line.split(":");
      const minutes = Number((rawMinutes || "").trim());
      if (source && Number.isFinite(minutes)) {
        mapping[source.trim()] = minutes;
      }
    });
    return mapping;
  }

  function parseSourceQueries(text) {
    const mapping = {};
    parseLineList(text).forEach((line) => {
      const [source, rawQueries] = line.split("=");
      if (!source || !rawQueries) return;
      const queries = rawQueries.split("|").map((item) => item.trim()).filter(Boolean);
      if (queries.length) {
        mapping[source.trim()] = queries;
      }
    });
    return mapping;
  }

  function formatSourceIntervals(mapping) {
    return Object.entries(mapping || {}).map(([source, minutes]) => `${source}:${minutes}`).join("\n");
  }

  function formatSourceQueries(mapping) {
    return Object.entries(mapping || {}).map(([source, queries]) => `${source}=${(queries || []).join("|")}`).join("\n");
  }

  function renderSchedulerStatus(status) {
    const summary = $("schedulerStatusSummary");
    const sourceJobs = $("schedulerSourceJobs");
    if (summary) {
      summary.innerHTML = `
        <div class="result-card">
          <strong>${status.enabled ? "Enabled" : "Disabled"}</strong>
          <div class="small-copy">Running: ${escapeHtml(status.running)}</div>
          <div class="small-copy">Last success: ${escapeHtml(status.last_success_at || "none")}</div>
          <div class="small-copy">Last error: ${escapeHtml(status.last_error || "none")}</div>
          <div class="small-copy">Tracked runs: ${escapeHtml(status.total_runs ?? 0)}</div>
        </div>
      `;
    }
    if (sourceJobs) {
      const jobs = status.source_jobs || {};
      const keys = Object.keys(jobs);
      sourceJobs.innerHTML = keys.length ? keys.map((source) => `
        <div class="result-card">
          <strong>${escapeHtml(source)}</strong>
          <div class="small-copy">Every ${escapeHtml(jobs[source].interval_minutes)} minutes</div>
          <div class="small-copy">Queries: ${escapeHtml((jobs[source].queries || []).join(" | ") || "shared fallback")}</div>
          <div class="small-copy">Next due: ${escapeHtml(jobs[source].next_due_at || "pending")}</div>
          <div class="small-copy">Last success: ${escapeHtml(jobs[source].last_success_at || "none")}</div>
          <div class="small-copy">Last duration: ${escapeHtml(jobs[source].last_duration_ms ?? "n/a")} ms</div>
          <div class="small-copy">Last records: ${escapeHtml(jobs[source].last_record_count ?? 0)} · Warnings: ${escapeHtml(jobs[source].last_warning_count ?? 0)}</div>
          <div class="small-copy">Indexed total: ${escapeHtml(jobs[source].total_records_indexed ?? 0)} · Failures: ${escapeHtml(jobs[source].total_failure_count ?? 0)}</div>
          <div class="button-row compact">
            <button class="ghost-button run-source-now" type="button" data-source="${escapeHtml(source)}">Run now</button>
          </div>
        </div>
      `).join("") : "<div class='small-copy'>No source jobs configured.</div>";
    }
  }

  function renderSecurityScanStatus(status) {
    const summary = $("securityScanSummary");
    const findings = $("securityScanFindings");
    if (summary) {
      const totals = status.last_summary?.severity_totals || {};
      summary.innerHTML = `
        <div class="result-card">
          <strong>${status.enabled ? "Enabled" : "Disabled"}</strong>
          <div class="small-copy">Running: ${escapeHtml(status.running)}</div>
          <div class="small-copy">Interval: ${escapeHtml(status.interval_hours ?? "n/a")} hour(s)</div>
          <div class="small-copy">Last success: ${escapeHtml(status.last_success_at || "none")}</div>
          <div class="small-copy">Last duration: ${escapeHtml(status.last_duration_ms ?? "n/a")} ms</div>
          <div class="small-copy">Next due: ${escapeHtml(status.next_due_at || "pending")}</div>
          <div class="small-copy">Critical: ${escapeHtml(totals.critical ?? 0)} · High: ${escapeHtml(totals.high ?? 0)} · Medium: ${escapeHtml(totals.medium ?? 0)}</div>
          <div class="small-copy">Total findings seen: ${escapeHtml(status.total_findings ?? 0)}</div>
        </div>
      `;
    }
    if (findings) {
      const rows = status.last_findings || [];
      findings.innerHTML = rows.length ? rows.slice(0, 20).map((item) => `
        <div class="result-card">
          <strong>${escapeHtml(String(item.severity || "info").toUpperCase())}: ${escapeHtml(item.title || "Finding")}</strong>
          <div class="small-copy">${escapeHtml(item.file_path || "")}:${escapeHtml(item.line || "")}</div>
          <div class="small-copy">${escapeHtml(item.detail || "")}</div>
          <div class="small-copy">${escapeHtml(item.snippet || "")}</div>
        </div>
      `).join("") : "<div class='small-copy'>No findings from the latest run.</div>";
    }
  }

  function renderAdminUsers(users) {
    const el = $("adminUsersList");
    if (!el) return;
    if (!users || !users.length) {
      el.innerHTML = "<div class='small-copy'>No matching users found.</div>";
      return;
    }
    el.innerHTML = users.map((user) => `
      <div class="result-card">
        <div class="section-heading">
          <div>
            <strong>${escapeHtml(user.full_name || user.email || user.clerk_user_id || "Unknown user")}</strong>
            <div class="small-copy">${escapeHtml(user.email || user.clerk_user_id || "No email yet")}</div>
            <div class="small-copy">Plan: ${escapeHtml(user.plan || "free")} · Source: ${escapeHtml(user.admin_source || "none")}</div>
          </div>
          <span class="status-pill ${user.is_admin ? "full" : "meta"}">${user.is_admin ? "Admin" : "Member"}</span>
        </div>
        <div class="button-row compact">
          <button class="ghost-button admin-role-toggle" type="button" data-user-id="${escapeHtml(user.clerk_user_id || "")}" data-next-admin="${user.is_admin ? "false" : "true"}">
            ${user.is_admin ? "Revoke admin" : "Make admin"}
          </button>
        </div>
      </div>
    `).join("");
  }

  function renderAdminAudit(events) {
    const el = $("adminAuditList");
    if (!el) return;
    if (!events || !events.length) {
      el.innerHTML = "<div class='small-copy'>No role changes logged yet.</div>";
      return;
    }
    el.innerHTML = events.map((event) => `
      <div class="result-card">
        <strong>${escapeHtml(event.action === "grant_admin" ? "Admin granted" : "Admin revoked")}</strong>
        <div class="small-copy">Target: ${escapeHtml(event.target?.full_name || event.target?.email || event.target_clerk_user_id || "unknown")}</div>
        <div class="small-copy">Actor: ${escapeHtml(event.actor?.full_name || event.actor?.email || event.actor_clerk_user_id || "unknown")}</div>
        <div class="small-copy">When: ${escapeHtml(event.created_at || "unknown")}</div>
        <div class="small-copy">Before: ${escapeHtml(String(Boolean(event.previous_is_admin)))} · After: ${escapeHtml(String(Boolean(event.new_is_admin)))}</div>
        <div class="small-copy">Source: ${escapeHtml(event.admin_source || "none")}</div>
      </div>
    `).join("");
  }

  async function loadSchedulerConfig() {
    const response = await authenticatedFetch("/admin/jobs/config", {}, true);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      showToast(response.status === 401 || response.status === 403
        ? "Admin access required for scheduler controls."
        : "Failed to load scheduler config.");
      return;
    }
    const effective = data.effective || {};
    const statusResponse = await authenticatedFetch("/admin/jobs/status");
    const statusPayload = await statusResponse.json().catch(() => ({}));
    if (!statusResponse.ok) {
      showToast(statusResponse.status === 401 || statusResponse.status === 403
        ? "Admin access required for scheduler status."
        : "Failed to load scheduler status.");
      return;
    }
    const status = statusPayload.open_access_auto_indexer || {};
    const securityStatus = statusPayload.security_auto_scanner || {};
    if ($("schedulerEnabled")) $("schedulerEnabled").checked = Boolean(effective.auto_index_enabled);
    if ($("schedulerPages")) $("schedulerPages").value = effective.auto_index_pages ?? 2;
    if ($("schedulerLimit")) $("schedulerLimit").value = effective.auto_index_limit_per_source ?? 25;
    if ($("schedulerStartupDelay")) $("schedulerStartupDelay").value = effective.auto_index_startup_delay_seconds ?? 30;
    if ($("schedulerQueries")) $("schedulerQueries").value = (effective.auto_index_queries || []).join("\n");
    if ($("schedulerSourceIntervals")) $("schedulerSourceIntervals").value = formatSourceIntervals(effective.auto_index_source_intervals || {});
    if ($("schedulerSourceQueries")) $("schedulerSourceQueries").value = formatSourceQueries(effective.auto_index_source_queries || {});
    renderSchedulerStatus(status);
    renderSecurityScanStatus(securityStatus);
  }

  async function loadAdminUsers() {
    const el = $("adminUsersList");
    if (el) {
      el.innerHTML = "<div class='small-copy'>Loading users...</div>";
    }
    const query = $("adminUserSearch")?.value?.trim() || "";
    const params = new URLSearchParams({ limit: "100" });
    if (query) params.set("search", query);
    const response = await authenticatedFetch(`/admin/roles/users?${params.toString()}`, {}, true);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      showToast(response.status === 401 || response.status === 403
        ? "Admin access required for role management."
        : "Failed to load admin users.");
      if (el) {
        el.innerHTML = "<div class='small-copy'>Could not load users.</div>";
      }
      return;
    }
    renderAdminUsers(data.users || []);
  }

  async function updateAdminUserRole(userId, isAdmin, button) {
    if (!userId) {
      showToast("Missing user id.");
      return;
    }
    setLoading(button, true, isAdmin ? "Promoting..." : "Revoking...");
    const response = await authenticatedFetch(`/admin/roles/users/${encodeURIComponent(userId)}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ is_admin: isAdmin }),
    }, true);
    const data = await response.json().catch(() => ({}));
    setLoading(button, false);
    if (!response.ok) {
      showToast(data.detail || "Role update failed.");
      return;
    }
    showToast(isAdmin ? "Admin access granted." : "Admin access revoked.");
    await loadAdminUsers();
    await loadAdminAudit();
  }

  async function loadAdminAudit() {
    const el = $("adminAuditList");
    if (el) {
      el.innerHTML = "<div class='small-copy'>Loading audit history...</div>";
    }
    const response = await authenticatedFetch("/admin/roles/audit?limit=50", {}, true);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      showToast(response.status === 401 || response.status === 403
        ? "Admin access required for audit history."
        : "Failed to load audit history.");
      if (el) {
        el.innerHTML = "<div class='small-copy'>Could not load audit history.</div>";
      }
      return;
    }
    renderAdminAudit(data.events || []);
  }

  async function saveSchedulerConfig() {
    const payload = {
      auto_index_enabled: Boolean($("schedulerEnabled")?.checked),
      auto_index_pages: Number($("schedulerPages")?.value || 2),
      auto_index_limit_per_source: Number($("schedulerLimit")?.value || 25),
      auto_index_queries: parseLineList($("schedulerQueries")?.value || ""),
      auto_index_startup_delay_seconds: Number($("schedulerStartupDelay")?.value || 30),
      auto_index_source_intervals: parseSourceIntervals($("schedulerSourceIntervals")?.value || ""),
      auto_index_source_queries: parseSourceQueries($("schedulerSourceQueries")?.value || ""),
    };
    const response = await authenticatedFetch("/admin/jobs/config", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }, true);
    if (!response.ok) {
      showToast(response.status === 401 || response.status === 403
        ? "Admin access required to save scheduler settings."
        : "Failed to save scheduler config.");
      return;
    }
    showToast("Scheduler config saved.");
    await loadSchedulerConfig();
  }

  async function runSchedulerSourceNow(source, button) {
    if (!source) {
      showToast("Missing source.");
      return;
    }
    setLoading(button, true, "Running...");
    const response = await authenticatedFetch(`/admin/jobs/run-source/${encodeURIComponent(source)}`, {
      method: "POST",
    }, true);
    const data = await response.json().catch(() => ({}));
    setLoading(button, false);
    if (!response.ok) {
      showToast(data.detail || "Manual run failed.");
      return;
    }
    showToast(`Manual run complete for ${source}.`);
    await loadSchedulerConfig();
  }

  async function runSecurityScanNow(button) {
    setLoading(button, true, "Scanning...");
    const response = await authenticatedFetch("/admin/security/run", {
      method: "POST",
    }, true);
    const data = await response.json().catch(() => ({}));
    setLoading(button, false);
    if (!response.ok) {
      showToast(data.detail || "Security scan failed.");
      return;
    }
    showToast("Security scan complete.");
    renderSecurityScanStatus(data.result || {});
  }

  function bindAdminControlsPage() {
    $("refreshSchedulerConfig")?.addEventListener("click", loadSchedulerConfig);
    $("saveSchedulerConfig")?.addEventListener("click", saveSchedulerConfig);
    $("refreshAdminUsers")?.addEventListener("click", loadAdminUsers);
    $("refreshAdminAudit")?.addEventListener("click", loadAdminAudit);
    $("runSecurityScanNow")?.addEventListener("click", (event) => {
      runSecurityScanNow(event.currentTarget);
    });
    $("searchAdminUsers")?.addEventListener("click", loadAdminUsers);
    $("adminUserSearch")?.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        loadAdminUsers();
      }
    });
    document.addEventListener("click", async (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;
      if (target.matches(".admin-role-toggle")) {
        await updateAdminUserRole(
          target.dataset.userId || "",
          target.dataset.nextAdmin === "true",
          target,
        );
      }
      if (target.matches(".run-source-now")) {
        await runSchedulerSourceNow(target.dataset.source || "", target);
      }
    });
    loadSchedulerConfig().catch((error) => {
      console.error(error);
      showToast("Failed to load admin controls.");
    });
    loadAdminUsers().catch((error) => {
      console.error(error);
      showToast("Failed to load admin users.");
    });
    loadAdminAudit().catch((error) => {
      console.error(error);
      showToast("Failed to load admin audit history.");
    });
  }

  function bindExploreEvents() {
    $("platformSearchButton")?.addEventListener("click", searchPapers);
    $("arxivSearchButton")?.addEventListener("click", searchArxiv);
    $("federatedSearchButton")?.addEventListener("click", searchFederated);
    $("addCurrentPaperToCompare")?.addEventListener("click", () => {
      if (!state.currentPaperMeta) {
        showToast("Open a paper first.");
        return;
      }
      if (state.comparePapers.some((item) => item.work_id === state.currentPaperMeta.work_id)) {
        showToast("Paper already added.");
        return;
      }
      state.comparePapers.push({
        work_id: state.currentPaperMeta.work_id,
        title: state.currentPaperMeta.title,
      });
      renderComparePapers();
    });
    $("clearComparePapers")?.addEventListener("click", () => {
      state.comparePapers = [];
      renderComparePapers();
      if ($("compareResults")) $("compareResults").hidden = true;
    });
    $("runMultiPaperCompare")?.addEventListener("click", runMultiPaperCompare);
    $("saveCurrentComparison")?.addEventListener("click", saveComparison);
    $("askQuestionButton")?.addEventListener("click", askQuestion);
    $("savePaperButton")?.addEventListener("click", () => savePaperAction("save-paper"));
    $("queuePaperButton")?.addEventListener("click", () => savePaperAction("queue-paper"));
    $("favoritePaperButton")?.addEventListener("click", () => savePaperAction("favorite-paper"));
    document.querySelectorAll(".explain-level").forEach((button) => {
      button.addEventListener("click", () => {
        state.explainLevel = button.dataset.level || "college";
        const textarea = $("question");
        if (textarea && textarea.value) {
          textarea.value = `${textarea.value.replace(/ Explain it for a .* audience\./, "")} Explain it for a ${state.explainLevel.replace("_", " ")} audience.`;
        }
      });
    });
    document.querySelectorAll(".filter-chip").forEach((button) => {
      button.addEventListener("click", () => {
        document.querySelectorAll(".filter-chip").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        state.platformFilter = button.dataset.filter || "all";
        if ($("paperSearch")?.value.trim()) searchPapers();
      });
    });

    document.addEventListener("click", async (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;
      if (target.matches(".open-paper")) {
        await openPaper(target.dataset.workId || "");
      }
      if (target.matches(".ingest-arxiv")) {
        await ingestArxiv(target.dataset.arxivId || "", target.dataset.mode || "full", target);
      }
      if (target.matches("[data-citation]")) {
        await copyCitation(target.dataset.citation || "apa");
      }
      if (target.matches(".remove-compare")) {
        const index = Number(target.dataset.index || "0");
        state.comparePapers.splice(index, 1);
        renderComparePapers();
      }
    });

    renderComparePapers();
  }

  function bindWorkspaceEvents() {
    $("saveQuickNote")?.addEventListener("click", saveQuickNote);
    $("saveBuilderDraft")?.addEventListener("click", saveBuilderDraft);
    $("copyBuilderMarkdown")?.addEventListener("click", copyBuilderMarkdown);
    $("copyBuilderHtml")?.addEventListener("click", copyBuilderHtml);
    $("exportBuilderDocx")?.addEventListener("click", () => downloadExport("docx"));
    $("exportBuilderPdf")?.addEventListener("click", () => downloadExport("pdf"));
    $("uploadLocalFileButton")?.addEventListener("click", (event) => uploadLocalFile(event.currentTarget));
    $("uploadUrlButton")?.addEventListener("click", (event) => uploadUrl(event.currentTarget));
    $("refreshComparisonHistory")?.addEventListener("click", loadComparisonHistory);
    document.addEventListener("click", async (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;
      if (target.matches(".uploaded-open")) {
        await openUploadedDocument(target.dataset.documentId || "");
      }
      if (target.matches(".reload-comparison")) {
        reloadComparison(target.dataset.comparisonId || "");
      }
      if (target.matches(".delete-comparison")) {
        await deleteComparison(target.dataset.comparisonId || "");
      }
    });
  }

  function buildCareerMailto(role) {
    const subject = `Application for ${role}`;
    const body = [
      `Hello FRIP team,`,
      ``,
      `I would like to apply for the ${role} role.`,
      ``,
      `I have attached my resume and cover letter.`,
      `Here is a short introduction:`,
      ``,
      `[Add your intro here]`,
      ``,
      `Best,`,
      `[Your name]`,
    ].join("\n");
    return `mailto:info@FRIP.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  }

  function bindCareersPage() {
    document.querySelectorAll(".career-apply").forEach((button) => {
      button.addEventListener("click", () => {
        const role = button.dataset.role || "Frontier role";
        window.location.href = buildCareerMailto(role);
      });
    });
  }

  function initPage() {
    const page = document.body.dataset.page;
    bindPricingActions();
    if (page === "auth") mountAuthView();
    if (page === "explore") bindExploreEvents();
    if (page === "workspace") bindWorkspaceEvents();
    if (page === "careers") bindCareersPage();
    if (page === "admin-controls") bindAdminControlsPage();
    if (page === "workspace") loadWorkspacePage();
  }

  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initPage();
    initClerk();
  });
})();
