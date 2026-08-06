const state = {
  data: null,
  activeState: "baseline",
  selectedQuestion: 0,
  tourTimer: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const metricDefinitions = [
  ["retrieval_hit_rate", "Retrieval hit rate", 1],
  ["mean_token_f1", "Mean token F1", 1],
  ["judge_accuracy", "Judge accuracy", 1],
  ["mean_judge_score", "Mean judge score", 5],
];

function percent(value, max = 1) {
  const numeric = Number(value || 0);
  return Math.max(0, Math.min(100, (numeric / max) * 100));
}

function metricValue(value, max = 1) {
  const numeric = Number(value || 0);
  return max === 5 ? numeric.toFixed(1) : `${(numeric * 100).toFixed(0)}%`;
}

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`;
}

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2400);
}

function renderOverview() {
  const { overview, states, project, generated_at: generatedAt } = state.data;
  $("#owner-line").textContent = `${project.owner} · ${project.role}`;
  $("#generated-time").textContent = `Synced ${new Date(generatedAt).toLocaleTimeString("vi-VN")}`;
  $("#stat-raw").textContent = overview.raw_records;
  $("#stat-clean").textContent = overview.clean_records;
  $("#stat-eval").textContent = overview.evaluation_questions;
  $("#hero-score").textContent = metricValue(states.baseline.metrics.retrieval_hit_rate);
  $("#hero-quality").textContent = states.baseline.quality.status || "—";
  $("#hero-freshness").textContent = states.baseline.freshness.status || "—";

  const allGood = states.baseline.quality.status === "PASS" && states.repaired.quality.status === "PASS";
  const pill = $("#system-pill");
  pill.querySelector("span").textContent = allGood ? "Evidence complete" : "Attention required";
  pill.style.color = allGood ? "var(--mint)" : "var(--orange)";
}

function selectPipelineNode(index) {
  const item = state.data.pipeline[index];
  $$(".pipeline-node").forEach((node, nodeIndex) => node.classList.toggle("active", nodeIndex === index));
  $("#detail-index").textContent = String(index + 1).padStart(2, "0");
  $("#detail-title").textContent = item.label;
  $("#detail-copy").textContent = item.detail;
  $("#detail-value").textContent = item.value;
  $("#detail-unit").textContent = item.unit;
}

function renderPipeline() {
  const track = $("#pipeline-track");
  track.innerHTML = state.data.pipeline
    .map(
      (item, index) => `
        <button class="pipeline-node${index === 0 ? " active" : ""}" type="button" data-index="${index}">
          <span class="node-number">${String(index + 1).padStart(2, "0")} / ${item.eyebrow}</span>
          <h3>${item.label}</h3>
          <p>${item.unit}</p>
          <strong class="node-value">${item.value}</strong>
        </button>`,
    )
    .join("");
  $$(".pipeline-node").forEach((node) => {
    node.addEventListener("click", () => selectPipelineNode(Number(node.dataset.index)));
  });
  selectPipelineNode(0);
}

function qualityDetail(check) {
  const observed = check.observed || {};
  if (check.name === "completeness") return `${observed.summary_under_100_rows || 0} short summaries`;
  if (check.name === "uniqueness") return `${observed.duplicate_paper_id_rows || 0} duplicate rows`;
  return `${observed.stale_rows || 0} stale rows`;
}

function renderState(stateName) {
  state.activeState = stateName;
  const current = state.data.states[stateName];
  const quality = current.quality || {};
  const freshness = current.freshness || {};
  const tone = current.tone || "healthy";

  $$(".state-button").forEach((button) => button.classList.toggle("active", button.dataset.state === stateName));
  $("#state-title").textContent = `${current.label} state`;
  const badge = $("#state-badge");
  badge.textContent = tone === "danger" ? "DEGRADED" : tone === "recovered" ? "RECOVERED" : "HEALTHY";
  badge.className = `state-badge ${tone}`;

  $("#metric-list").innerHTML = metricDefinitions
    .map(([key, label, max]) => {
      const value = current.metrics[key] ?? 0;
      return `
        <article class="metric-card ${tone}">
          <header><span>${label}</span><small>/${max}</small></header>
          <strong>${metricValue(value, max)}</strong>
          <div class="metric-track"><i style="--score: ${percent(value, max)}%"></i></div>
        </article>`;
    })
    .join("");

  const checks = quality.checks || [];
  $("#quality-score").textContent = quality.status || "—";
  $("#quality-score").style.color = quality.status === "PASS" ? "var(--mint)" : "var(--red)";
  $("#quality-list").innerHTML = checks
    .map(
      (check) => `
        <div class="quality-row ${check.passed ? "pass" : "fail"}">
          <div>
            <span class="quality-icon">${check.passed ? "✓" : "!"}</span>
            <div><strong>${check.name}</strong><small>${qualityDetail(check)}</small></div>
          </div>
          <span class="quality-status">${check.status}</span>
        </div>`,
    )
    .join("");
  $("#freshness-window").textContent = `${freshness.freshness_threshold_days || 0} days threshold`;
  $("#freshness-oldest").textContent = `Oldest ${freshness.oldest_published || "—"}`;
  $("#freshness-stale").textContent = `${freshness.stale_rows || 0} stale`;
}

function renderComparison() {
  const keys = ["baseline", "corrupted", "repaired"];
  $("#comparison-chart").innerHTML = metricDefinitions
    .map(([metricKey, label, max]) => {
      const bars = keys
        .map((key) => {
          const item = state.data.states[key];
          const value = item.metrics[metricKey] ?? 0;
          return `
            <div class="chart-bar ${key}">
              <i style="--score: ${percent(value, max)}%"></i>
              <span><b>${item.label.slice(0, 1)}</b><strong>${metricValue(value, max)}</strong></span>
            </div>`;
        })
        .join("");
      return `<div class="chart-group"><span>${label}</span><div class="chart-bars">${bars}</div></div>`;
    })
    .join("");
}

function renderIncidents() {
  const incidents = state.data.corruptions;
  $("#event-count").textContent = `${state.data.overview.corruption_events} events`;
  $("#incident-list").innerHTML = incidents
    .map(
      (item, index) => `
        <div class="incident-item">
          <span class="incident-mark">${String(index + 1).padStart(2, "0")}</span>
          <div><strong>${item.label}</strong><small>${item.count} affected operation</small></div>
        </div>`,
    )
    .join("");
}

function renderLineage() {
  const item = state.data.lineage;
  $("#lineage-doi").textContent = `DOI ${item.paper_id}`;
  const steps = [
    ["01 / SOURCE", "Crossref item", item.source_title],
    ["02 / RAW", "PaperRecord", item.raw_summary_preview],
    ["03 / CLEAN", "Retrieval document", item.clean_summary_preview],
    ["04 / EVAL", "Grounded question", item.question],
  ];
  $("#lineage-flow").innerHTML = steps
    .map(([number, title, copy]) => `<article class="lineage-step"><span>${number}</span><h3>${title}</h3><p>${copy}</p></article>`)
    .join("");

  const select = $("#question-select");
  select.innerHTML = state.data.questions
    .map((question, index) => `<option value="${index}">${question.id} · ${question.paper_id}</option>`)
    .join("");
  select.addEventListener("change", () => {
    state.selectedQuestion = Number(select.value);
    renderQuestion();
  });
  renderQuestion();

  const paper = state.data.papers[0] || {};
  $("#paper-title").textContent = paper.title || "No paper available";
  $("#paper-summary").textContent = paper.summary || "";
  $("#paper-authors").textContent = paper.authors || "Unknown authors";
  $("#paper-date").textContent = `${paper.published || "—"} · ${paper.age_days ?? "—"} days old`;
}

function renderQuestion() {
  const question = state.data.questions[state.selectedQuestion] || {};
  $("#selected-question").textContent = question.question || "No question available";
  $("#ground-truth-copy").textContent = question.ground_truth || "";
  $("#ground-truth-id").textContent = question.paper_id || "";
  $("#ground-truth").hidden = true;
  $("#reveal-answer").textContent = "Reveal ground truth";
}

function renderArtifacts() {
  $("#artifact-body").innerHTML = state.data.artifacts
    .map(
      (item) => `
        <tr>
          <td><strong>${item.label}</strong></td>
          <td><span class="artifact-kind">${item.kind}</span></td>
          <td><span class="artifact-path">${item.path}</span></td>
          <td>${formatBytes(item.bytes)}</td>
          <td><span class="artifact-status">${item.exists ? "AVAILABLE" : "MISSING"}</span></td>
        </tr>`,
    )
    .join("");
}

function updateNav() {
  const sections = $$("section[id]");
  const links = $$(".nav-link");
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        links.forEach((link) => link.classList.toggle("active", link.getAttribute("href") === `#${entry.target.id}`));
      });
    },
    { threshold: 0.35 },
  );
  sections.forEach((section) => observer.observe(section));
}

function startTour() {
  if (state.tourTimer) {
    window.clearInterval(state.tourTimer);
    state.tourTimer = null;
    $$(".tour-focus").forEach((element) => element.classList.remove("tour-focus"));
    showToast("Demo tour stopped");
    return;
  }
  const stops = [
    ["#overview", "Bắt đầu với bằng chứng baseline sạch"],
    ["#pipeline", "Theo dõi dữ liệu qua từng contract"],
    ["#impact", "Chuyển sang Corrupted để thấy impact"],
    ["#lineage", "Truy một câu trả lời về tận Crossref"],
    ["#artifacts", "Kết thúc bằng artifact thật trên đĩa"],
  ];
  let index = 0;
  const move = () => {
    $$(".tour-focus").forEach((element) => element.classList.remove("tour-focus"));
    const [selector, message] = stops[index];
    const element = $(selector);
    element.scrollIntoView({ behavior: "smooth", block: "start" });
    element.classList.add("tour-focus");
    if (selector === "#impact") renderState("corrupted");
    showToast(message);
    index = (index + 1) % stops.length;
  };
  move();
  state.tourTimer = window.setInterval(move, 5200);
}

async function loadDashboard(showMessage = false) {
  const response = await fetch("/api/dashboard", { cache: "no-store" });
  if (!response.ok) throw new Error(`Dashboard API returned ${response.status}`);
  state.data = await response.json();
  renderOverview();
  renderPipeline();
  renderState(state.activeState);
  renderComparison();
  renderIncidents();
  renderLineage();
  renderArtifacts();
  if (showMessage) showToast("Artifacts refreshed from disk");
}

function bindEvents() {
  $$(".state-button").forEach((button) => button.addEventListener("click", () => renderState(button.dataset.state)));
  $("#refresh-button").addEventListener("click", () => loadDashboard(true).catch(handleError));
  $("#tour-button").addEventListener("click", startTour);
  $("#reveal-answer").addEventListener("click", () => {
    const answer = $("#ground-truth");
    answer.hidden = !answer.hidden;
    $("#reveal-answer").textContent = answer.hidden ? "Reveal ground truth" : "Hide ground truth";
  });
}

function handleError(error) {
  console.error(error);
  $("#system-pill span").textContent = "Artifact load failed";
  $("#system-pill").style.color = "var(--red)";
  showToast(error.message);
}

bindEvents();
updateNav();
loadDashboard().catch(handleError);
