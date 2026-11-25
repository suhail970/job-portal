const DEFAULT_API = "http://localhost:8000/api/v1";

function escHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderFields(studentSummary, activeSchema) {
  const container = document.getElementById("fields-container");
  const reviewCard = document.getElementById("review-card");
  const jobNameEl = document.getElementById("job-name");
  container.innerHTML = "";

  const fieldsToEdit = (activeSchema && Array.isArray(activeSchema.fields) && activeSchema.fields.length > 0)
    ? activeSchema.fields
    : [
        { name: "full_name", label: "Full Name", suggested_value: studentSummary.full_name || "" },
        { name: "email", label: "Email", suggested_value: studentSummary.email || "" },
        { name: "phone", label: "Phone", suggested_value: studentSummary.phone || "" },
        { name: "college", label: "College", suggested_value: studentSummary.college || "Anna University - CEG Campus" },
        { name: "cgpa", label: "CGPA", suggested_value: studentSummary.cgpa ? String(studentSummary.cgpa) : "" },
        { name: "linkedin", label: "LinkedIn", suggested_value: studentSummary.linkedin_url || "" },
        { name: "github", label: "GitHub", suggested_value: studentSummary.github_url || "" },
      ];

  jobNameEl.textContent = activeSchema?.company_name ? `${activeSchema.company_name}` : "Student Profile";
  fieldsToEdit.forEach((f, idx) => {
    if (f.type === "file") return;
    const row = document.createElement("div");
    row.className = "field-row";
    row.innerHTML = `
      <label class="field-label">
        <span>${escHtml(f.label || f.name)}</span>
        ${f.needs_review ? '<span style="color:#d97706;">⚠ Review</span>' : ""}
      </label>
      <input class="field-input" data-idx="${idx}" data-name="${escHtml(f.name || "")}" data-label="${escHtml(f.label || "")}" value="${escHtml(f.suggested_value || "")}" />
    `;
    container.appendChild(row);
  });

  reviewCard.style.display = "block";
}

async function fetchProfileFromApi(token, apiBase) {
  const res = await fetch(`${apiBase}/students/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Session expired");
  const data = await res.json();
  return {
    full_name: data.full_name,
    email: data.email,
    phone: data.profile?.phone_number || "",
    roll_number: data.profile?.roll_number || "",
    cgpa: data.profile?.cgpa || "",
    graduation_year: data.profile?.graduation_year || 2026,
    department_name: data.department_name || "CSE",
    college: "Anna University - CEG Campus",
    linkedin_url: data.profile?.linkedin_url || "",
    github_url: data.profile?.github_url || "",
  };
}

async function initPopup() {
  const statusEl = document.getElementById("status-msg");
  const studentLine = document.getElementById("student-line");
  const authBox = document.getElementById("auth-box");
  const badge = document.getElementById("platform-badge");

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) {
    chrome.tabs.sendMessage(tab.id, { action: "GET_PAGE_INFO" }, (res) => {
      if (!chrome.runtime.lastError && res?.platform) {
        badge.textContent = res.platform;
      }
    });
  }

  chrome.storage.local.get(
    ["skillbridge_token", "skillbridge_api_base", "skillbridge_student_summary", "skillbridge_active_schema"],
    async (data) => {
      const apiBase = data.skillbridge_api_base || DEFAULT_API;
      let summary = data.skillbridge_student_summary;
      const token = data.skillbridge_token;

      if (!summary && token) {
        try {
          summary = await fetchProfileFromApi(token, apiBase);
          chrome.storage.local.set({ skillbridge_student_summary: summary });
        } catch {}
      }

      if (!summary) {
        studentLine.textContent = "Not synced yet — sign in below or click Sync in SkillBridge tab";
        authBox.style.display = "block";
      } else {
        authBox.style.display = "none";
        studentLine.textContent = `${summary.full_name} • CGPA ${summary.cgpa || "-"} • Ready`;
        renderFields(summary, data.skillbridge_active_schema);
      }

      document.getElementById("login-btn").onclick = async () => {
        const email = document.getElementById("login-email").value.trim();
        const password = document.getElementById("login-pass").value;
        try {
          const r = await fetch(`${apiBase}/auth/login-json`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
          });
          if (!r.ok) throw new Error("Invalid credentials");
          const loginData = await r.json();
          summary = await fetchProfileFromApi(loginData.access_token, apiBase);
          chrome.storage.local.set({
            skillbridge_token: loginData.access_token,
            skillbridge_api_base: apiBase,
            skillbridge_student_summary: summary,
          });
          authBox.style.display = "none";
          studentLine.textContent = `${summary.full_name} • CGPA ${summary.cgpa || "-"} • Ready`;
          renderFields(summary, data.skillbridge_active_schema);
        } catch (err) {
          statusEl.className = "notice";
          statusEl.textContent = err.message;
          statusEl.style.display = "block";
        }
      };

      document.getElementById("refresh-btn").onclick = async () => {
        if (!token) return;
        try {
          summary = await fetchProfileFromApi(token, apiBase);
          chrome.storage.local.set({ skillbridge_student_summary: summary });
          renderFields(summary, data.skillbridge_active_schema);
        } catch {}
      };

      document.getElementById("autofill-btn").onclick = async () => {
        if (!summary || !tab?.id) return;
        // Collect user-reviewed edited inputs from popup
        const editedFields = [];
        document.querySelectorAll("#fields-container .field-input").forEach((inp) => {
          editedFields.push({
            name: inp.getAttribute("data-name"),
            label: inp.getAttribute("data-label"),
            suggested_value: inp.value,
          });
        });

        const payload = {
          student_summary: summary,
          drive_schema: { ...(data.skillbridge_active_schema || {}), fields: editedFields },
        };

        // Ensure content.js is present even on custom corporate career domains via activeTab
        try {
          await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
        } catch {}

        chrome.tabs.sendMessage(tab.id, { action: "AUTOFILL_FORM", payload }, (resp) => {
          if (chrome.runtime.lastError || !resp?.ok) {
            statusEl.className = "notice";
            statusEl.textContent = "Cannot access this tab (open an external job form first).";
            statusEl.style.display = "block";
            return;
          }
          const r = resp.result;
          statusEl.className = "status-ok";
          statusEl.textContent = `✓ Filled ${r.filledCount} inputs on ${r.platform}. ${r.manualReview.length} fields need review on the page.`;
          statusEl.style.display = "block";
        });
      };
    }
  );
}

initPopup();
