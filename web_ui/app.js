// =========================================================================
// DEEP RESEARX // CLIENT CONTROLLER & INTERACTIVE ANNOTATION CANVAS
// =========================================================================

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const queryInput = document.getElementById("researchQueryInput");
  const startResearchBtn = document.getElementById("startResearchBtn");
  const emptyState = document.getElementById("emptyState");
  const markdownOutput = document.getElementById("markdownOutput");
  const pipelineStepper = document.getElementById("pipelineStepper");
  const modelSelector = document.getElementById("modelSelector");
  const copyMarkdownBtn = document.getElementById("copyMarkdownBtn");
  const downloadMarkdownBtn = document.getElementById("downloadMarkdownBtn");
  const clearWorkspaceBtn = document.getElementById("clearWorkspaceBtn");
  const quickTags = document.querySelectorAll(".quick-tag");

  // Selection & Comment Elements
  const selectionTooltip = document.getElementById("selectionTooltip");
  const addCommentBtn = document.getElementById("addCommentFromSelectionBtn");
  const askSelectionBtn = document.getElementById("askAboutSelectionBtn");
  const commentsSidebar = document.getElementById("commentsSidebar");
  const toggleCommentsBtn = document.getElementById("toggleCommentPanelBtn");
  const closeCommentsBtn = document.getElementById("closeCommentsBtn");
  const commentsList = document.getElementById("commentsList");
  const commentCountBadge = document.getElementById("commentCount");

  // Chat Elements
  const chatTimeline = document.getElementById("chatTimeline");
  const chatInput = document.getElementById("chatInputText");
  const sendChatBtn = document.getElementById("sendChatBtn");
  const groundingToggle = document.getElementById("groundingToggle");
  const attachFileBtn = document.getElementById("attachFileBtn");
  const imageFileInput = document.getElementById("imageFileInput");
  const attachmentPreviewBar = document.getElementById("attachmentPreviewBar");
  const attachedImagePreview = document.getElementById("attachedImagePreview");
  const attachedImageName = document.getElementById("attachedImageName");
  const removeAttachmentBtn = document.getElementById("removeAttachmentBtn");

  // State
  let currentRawMarkdown = "";
  let userComments = [];
  let currentSelectionRange = null;
  let selectedTextSnapshot = "";
  let currentAttachedBase64 = null;
  let chatHistory = [];

  // Stepper Elements
  const stepPlan = document.getElementById("stepPlan");
  const stepScrape = document.getElementById("stepScrape");
  const stepMatrix = document.getElementById("stepMatrix");
  const stepSynthesize = document.getElementById("stepSynthesize");

  // Quick Preset Tags
  quickTags.forEach(btn => {
    btn.addEventListener("click", () => {
      queryInput.value = btn.dataset.query;
      executeResearch(queryInput.value);
    });
  });

  // Research Execution Handler
  startResearchBtn.addEventListener("click", () => {
    const q = queryInput.value.trim();
    if (q) executeResearch(q);
  });

  queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const q = queryInput.value.trim();
      if (q) executeResearch(q);
    }
  });

  async function executeResearch(topic) {
    // Reset View
    emptyState.style.display = "none";
    markdownOutput.style.display = "block";
    markdownOutput.innerHTML = `<div class="loading-state">Initializing Autonomous Multi-Agent Loop for: <strong>${escapeHtml(topic)}</strong>...</div>`;
    pipelineStepper.style.display = "flex";
    currentRawMarkdown = "";
    resetStepper();

    // Disable input while running
    startResearchBtn.disabled = true;
    startResearchBtn.querySelector(".btn-text").textContent = "Researching...";
    startResearchBtn.querySelector(".spinner").style.display = "inline-block";

    setStepActive(stepPlan);

    try {
      const response = await fetch("/api/deep_research/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: topic,
          model: modelSelector.value
        })
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.replace(/^data:\s*/, "").trim();
            if (dataStr === "[DONE]") break;

            try {
              const event = JSON.parse(dataStr);
              handlePipelineEvent(event);
            } catch (e) {
              console.error("Failed to parse SSE JSON:", e, line);
            }
          }
        }
      }
    } catch (err) {
      console.error("Research failed:", err);
      markdownOutput.innerHTML = `<div class="error-msg">❌ Research Failed: ${err.message}. Please verify local Ollama engine is active.</div>`;
    } finally {
      startResearchBtn.disabled = false;
      startResearchBtn.querySelector(".btn-text").textContent = "Execute Research";
      startResearchBtn.querySelector(".spinner").style.display = "none";
      setStepDone(stepSynthesize);
    }
  }

  function handlePipelineEvent(evt) {
    if (evt.type === "plan") {
      setStepDone(stepPlan);
      setStepActive(stepScrape);
      document.getElementById("stepPlanDetail").textContent = `${evt.sub_questions.length} search angles generated`;
    } else if (evt.type === "scraping") {
      setStepActive(stepScrape);
      document.getElementById("stepScrapeDetail").textContent = `Retrieved ${evt.sources_count} sources across ${evt.domains.join(', ')}`;
    } else if (evt.type === "matrix") {
      setStepDone(stepScrape);
      setStepActive(stepMatrix);
      document.getElementById("stepMatrixDetail").textContent = `${evt.metric_count || 12} metrics & case studies extracted`;
    } else if (evt.type === "synthesis_start") {
      setStepDone(stepMatrix);
      setStepActive(stepSynthesize);
    } else if (evt.type === "token") {
      currentRawMarkdown += evt.token;
      renderMarkdown(currentRawMarkdown);
    } else if (evt.type === "complete") {
      setStepDone(stepSynthesize);
      currentRawMarkdown = evt.report;
      renderMarkdown(currentRawMarkdown);
    }
  }

  function renderMarkdown(md) {
    // Clean thinking tags if present
    const cleaned = md.replace(/<think>[\s\S]*?<\/think>/g, "").trim();
    const rawHtml = marked.parse(cleaned);
    markdownOutput.innerHTML = DOMPurify.sanitize(rawHtml);
  }

  function resetStepper() {
    [stepPlan, stepScrape, stepMatrix, stepSynthesize].forEach(s => {
      s.className = "step-item";
    });
  }

  function setStepActive(step) {
    step.className = "step-item active";
  }

  function setStepDone(step) {
    step.className = "step-item done";
  }

  // =========================================================================
  // INTERACTIVE TEXT SELECTION & COMMENTING SYSTEM
  // =========================================================================

  markdownOutput.addEventListener("mouseup", (e) => {
    const selection = window.getSelection();
    const text = selection.toString().trim();

    if (text.length > 5) {
      selectedTextSnapshot = text;
      const range = selection.getRangeAt(0);
      currentSelectionRange = range.cloneRange();
      const rect = range.getBoundingClientRect();

      selectionTooltip.style.top = `${window.scrollY + rect.top}px`;
      selectionTooltip.style.left = `${window.scrollX + rect.left + rect.width / 2}px`;
      selectionTooltip.style.display = "flex";
    } else {
      selectionTooltip.style.display = "none";
    }
  });

  document.addEventListener("mousedown", (e) => {
    if (!selectionTooltip.contains(e.target) && e.target !== markdownOutput) {
      selectionTooltip.style.display = "none";
    }
  });

  addCommentBtn.addEventListener("click", () => {
    selectionTooltip.style.display = "none";
    const commentText = prompt(`Add Comment on: "${selectedTextSnapshot.slice(0, 40)}..."`);
    if (commentText && commentText.trim()) {
      addComment(selectedTextSnapshot, commentText.trim());
    }
  });

  askSelectionBtn.addEventListener("click", () => {
    selectionTooltip.style.display = "none";
    chatInput.value = `Regarding this excerpt from the research:\n> "${selectedTextSnapshot}"\n\nCan you explain or evaluate this further?`;
    chatInput.focus();
  });

  function addComment(quote, comment) {
    const id = Date.now();
    const item = { id, quote, comment, timestamp: new Date().toLocaleTimeString() };
    userComments.push(item);
    updateCommentsUI();
    openCommentsSidebar();
  }

  function deleteComment(id) {
    userComments = userComments.filter(c => c.id !== id);
    updateCommentsUI();
  }

  function updateCommentsUI() {
    commentCountBadge.textContent = userComments.length;
    if (userComments.length === 0) {
      commentsList.innerHTML = `<div class="no-comments-msg">Highlight any text on the research dossier to attach comments and annotations.</div>`;
      return;
    }

    commentsList.innerHTML = userComments.map(c => `
      <div class="comment-card" data-id="${c.id}">
        <div class="comment-quote">"${escapeHtml(c.quote)}"</div>
        <div class="comment-text">${escapeHtml(c.comment)}</div>
        <div class="comment-actions">
          <span style="font-size: 0.7rem; color: #64748b;">${c.timestamp}</span>
          <button class="comment-del-btn" onclick="window.removeCommentById(${c.id})">Delete</button>
        </div>
      </div>
    `).join("");
  }

  window.removeCommentById = deleteComment;

  toggleCommentsBtn.addEventListener("click", () => {
    commentsSidebar.classList.toggle("open");
  });

  closeCommentsBtn.addEventListener("click", () => {
    commentsSidebar.classList.remove("open");
  });

  function openCommentsSidebar() {
    commentsSidebar.classList.add("open");
  }

  // =========================================================================
  // DIRECT MODEL Q&A & MULTIMODAL CHAT
  // =========================================================================

  sendChatBtn.addEventListener("click", handleSendChat);
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendChat();
    }
  });

  attachFileBtn.addEventListener("click", () => imageFileInput.click());
  imageFileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        currentAttachedBase64 = evt.target.result;
        attachedImagePreview.src = currentAttachedBase64;
        attachedImageName.textContent = file.name;
        attachmentPreviewBar.style.display = "flex";
      };
      reader.readAsDataURL(file);
    }
  });

  removeAttachmentBtn.addEventListener("click", () => {
    currentAttachedBase64 = null;
    imageFileInput.value = "";
    attachmentPreviewBar.style.display = "none";
  });

  async function handleSendChat() {
    const text = chatInput.value.trim();
    if (!text && !currentAttachedBase64) return;

    chatInput.value = "";
    const userMsgObj = { role: "user", content: text, image: currentAttachedBase64 };
    appendChatMessage("user", text, currentAttachedBase64);

    // Prepare context
    let promptContext = text;
    if (groundingToggle.checked && currentRawMarkdown) {
      promptContext = `[GROUNDING RESEARCH DOSSIER CONTEXT]:\n${currentRawMarkdown.slice(0, 4000)}\n\n[USER QUESTION]:\n${text}`;
    }

    // Reset attachment
    const sendingImage = currentAttachedBase64;
    currentAttachedBase64 = null;
    attachmentPreviewBar.style.display = "none";
    imageFileInput.value = "";

    // Assistant placeholder
    const assistantMsgNode = appendChatMessage("assistant", "Thinking...");

    try {
      const resp = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: promptContext,
          model: modelSelector.value,
          image: sendingImage
        })
      });

      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

      const reader = resp.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let accumulated = "";
      assistantMsgNode.innerHTML = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        accumulated += chunk;
        const cleaned = accumulated.replace(/<think>[\s\S]*?<\/think>/g, "").trim();
        assistantMsgNode.innerHTML = DOMPurify.sanitize(marked.parse(cleaned));
        chatTimeline.scrollTop = chatTimeline.scrollHeight;
      }
    } catch (e) {
      assistantMsgNode.innerHTML = `<span style="color: #f43f5e;">Error: ${e.message}</span>`;
    }
  }

  function appendChatMessage(role, text, imageSrc = null) {
    const div = document.createElement("div");
    div.className = `chat-msg ${role}`;
    
    let imgHtml = "";
    if (imageSrc) {
      imgHtml = `<div style="margin-bottom: 8px;"><img src="${imageSrc}" style="max-width: 180px; max-height: 120px; border-radius: 6px;" /></div>`;
    }

    div.innerHTML = `
      <div class="msg-avatar">${role === "user" ? "👤" : "🤖"}</div>
      <div class="msg-body">${imgHtml}${escapeHtml(text)}</div>
    `;

    chatTimeline.appendChild(div);
    chatTimeline.scrollTop = chatTimeline.scrollHeight;
    return div.querySelector(".msg-body");
  }

  // Export Tools
  copyMarkdownBtn.addEventListener("click", () => {
    if (!currentRawMarkdown) return alert("No research generated yet.");
    navigator.clipboard.writeText(currentRawMarkdown);
    copyMarkdownBtn.textContent = "✅ Copied!";
    setTimeout(() => copyMarkdownBtn.textContent = "📋 Copy MD", 2000);
  });

  downloadMarkdownBtn.addEventListener("click", () => {
    if (!currentRawMarkdown) return alert("No research generated yet.");
    const blob = new Blob([currentRawMarkdown], { type: "text/markdown" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `research_dossier_${Date.now()}.md`;
    a.click();
  });

  clearWorkspaceBtn.addEventListener("click", () => {
    currentRawMarkdown = "";
    userComments = [];
    updateCommentsUI();
    emptyState.style.display = "flex";
    markdownOutput.style.display = "none";
    pipelineStepper.style.display = "none";
    queryInput.value = "";
  });

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }
});
