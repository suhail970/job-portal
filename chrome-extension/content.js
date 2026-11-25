// SkillBridge AI Form Auto-Fill Content Script (Supports Greenhouse, Lever, Ashby, SmartRecruiters, Workday)
(function () {
  if (window.__skillbridgeAutofillInjected) return;
  window.__skillbridgeAutofillInjected = true;

  function detectPlatform() {
    const h = window.location.hostname.toLowerCase();
    if (h.includes("greenhouse.io")) return "Greenhouse";
    if (h.includes("lever.co")) return "Lever";
    if (h.includes("ashbyhq.com")) return "Ashby";
    if (h.includes("smartrecruiters.com")) return "SmartRecruiters";
    if (h.includes("workday")) return "Workday";
    if (h.includes("tcs.com")) return "TCS NextStep";
    if (h.includes("zoho")) return "Zoho Careers";
    return "Corporate Portal";
  }

  // Trigger native React/Vue/Angular input state updates cleanly
  function setNativeValue(element, value) {
    if (!element || value === undefined || value === null || value === "") return false;
    const tag = element.tagName;
    let descriptor = null;
    if (tag === "INPUT") descriptor = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value");
    else if (tag === "TEXTAREA") descriptor = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value");
    else if (tag === "SELECT") descriptor = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value");

    if (descriptor && descriptor.set) {
      descriptor.set.call(element, String(value));
    } else {
      element.value = String(value);
    }

    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
    element.dispatchEvent(new Event("blur", { bubbles: true }));
    return true;
  }

  function extractLabelForElement(el) {
    const parts = [];
    if (el.id) {
      const lbl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (lbl) parts.push(lbl.textContent);
    }
    const parentLabel = el.closest("label");
    if (parentLabel) parts.push(parentLabel.textContent);

    const container = el.closest(".field, .application-question, .form-group, [data-testid], div");
    if (container) {
      const heading = container.querySelector("label, .application-label, span[class*='label']");
      if (heading) parts.push(heading.textContent);
    }

    parts.push(el.getAttribute("aria-label") || "");
    parts.push(el.getAttribute("placeholder") || "");
    parts.push(el.getAttribute("name") || "");
    parts.push(el.id || "");
    return parts.join(" ").replace(/\s+/g, " ").trim().toLowerCase();
  }

  function buildStudentMap(studentSummary, activeSchema) {
    const s = studentSummary || {};
    const fullName = s.full_name || "Aravind Swaminathan";
    const nameParts = fullName.trim().split(/\s+/);
    const firstName = nameParts[0] || "Aravind";
    const lastName = nameParts.length > 1 ? nameParts.slice(1).join(" ") : firstName;

    const map = {
      firstName,
      lastName,
      fullName,
      email: s.email || "",
      phone: s.phone || "",
      linkedin: s.linkedin_url || "",
      github: s.github_url || "",
      portfolio: s.github_url || s.linkedin_url || "",
      college: s.college || "Anna University - CEG Campus",
      department: s.department_name || "Computer Science and Engineering",
      cgpa: s.cgpa ? String(s.cgpa) : "",
      graduationYear: s.graduation_year ? String(s.graduation_year) : "2026",
      location: "Chennai, India",
      byExactFieldName: {},
      byLabelHint: [],
    };

    if (activeSchema && Array.isArray(activeSchema.fields)) {
      for (const f of activeSchema.fields) {
        if (f.suggested_value) {
          if (f.name) map.byExactFieldName[f.name.toLowerCase()] = f.suggested_value;
          if (f.label) map.byLabelHint.push({ label: f.label.toLowerCase(), value: f.suggested_value });
        }
      }
    }
    return map;
  }

  function resolveValueForField(descriptor, elName, studentMap) {
    const cleanName = (elName || "").toLowerCase();
    if (cleanName && studentMap.byExactFieldName[cleanName]) {
      return studentMap.byExactFieldName[cleanName];
    }
    for (const h of studentMap.byLabelHint) {
      if (h.label.length >= 4 && descriptor.includes(h.label)) {
        return h.value;
      }
    }

    if (descriptor.includes("first") && descriptor.includes("name")) return studentMap.firstName;
    if (descriptor.includes("last") && descriptor.includes("name")) return studentMap.lastName;
    if ((descriptor.includes("full") && descriptor.includes("name")) || cleanName === "name") return studentMap.fullName;
    if (descriptor.includes("email")) return studentMap.email;
    if (descriptor.includes("phone") || descriptor.includes("mobile")) return studentMap.phone;
    if (descriptor.includes("linkedin")) return studentMap.linkedin;
    if (descriptor.includes("github") || descriptor.includes("gitlab")) return studentMap.github;
    if (descriptor.includes("portfolio") || descriptor.includes("website")) return studentMap.portfolio;
    if (descriptor.includes("school") || descriptor.includes("university") || descriptor.includes("college")) return studentMap.college;
    if (descriptor.includes("degree") || descriptor.includes("major") || descriptor.includes("discipline")) return studentMap.department;
    if (descriptor.includes("gpa") || descriptor.includes("cgpa")) return studentMap.cgpa;
    if (descriptor.includes("graduation") || descriptor.includes("passing year")) return studentMap.graduationYear;
    if (descriptor.includes("location") || descriptor.includes("city")) return studentMap.location;
    return "";
  }

  function showReviewOverlay(platform, filledItems, manualReviewItems) {
    const existing = document.getElementById("skillbridge-review-bar");
    if (existing) existing.remove();

    const bar = document.createElement("div");
    bar.id = "skillbridge-review-bar";
    bar.style.cssText = [
      "position: fixed",
      "bottom: 18px",
      "right: 18px",
      "z-index: 2147483647",
      "width: 340px",
      "background: #0f172a",
      "color: #f8fafc",
      "border: 1px solid #334155",
      "border-radius: 14px",
      "padding: 14px 16px",
      "font-family: system-ui, -apple-system, sans-serif",
      "font-size: 12px",
      "box-shadow: 0 20px 40px rgba(0,0,0,0.35)",
    ].join(";");

    const esc = (s) => String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const manualListHtml = manualReviewItems.slice(0, 5).map((item) => `<li style="margin:2px 0;color:#fde68a;">• ${esc(item)}</li>`).join("");

    bar.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <strong style="font-size:13px;color:#34d399;">✓ SkillBridge Auto-Fill (${esc(platform)})</strong>
        <button id="sb-close-bar" style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:14px;">✕</button>
      </div>
      <div style="color:#cbd5e1;margin-bottom:8px;">
        Filled <strong>${filledItems.length}</strong> fields cleanly. <strong>Review all fields carefully before you click Submit.</strong>
      </div>
      ${
        manualReviewItems.length > 0
          ? `<div style="background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.35);border-radius:8px;padding:8px;margin-bottom:8px;">
               <div style="font-weight:700;color:#fbbf24;margin-bottom:4px;">⚠ Requires Your Manual Input (${manualReviewItems.length}):</div>
               <ul style="margin:0;padding-left:14px;list-style:none;">${manualListHtml}</ul>
             </div>`
          : ""
      }
      <div style="display:flex;gap:8px;justify-content:flex-end;">
        <button id="sb-clear-highlights" style="padding:5px 10px;border-radius:6px;border:1px solid #475569;background:#1e293b;color:#e2e8f0;cursor:pointer;font-size:11px;">Clear Highlights</button>
      </div>
    `;

    document.body.appendChild(bar);
    document.getElementById("sb-close-bar").onclick = () => bar.remove();
    document.getElementById("sb-clear-highlights").onclick = () => {
      document.querySelectorAll("[data-sb-highlighted]").forEach((el) => {
        el.style.outline = "";
        el.removeAttribute("data-sb-highlighted");
      });
      bar.remove();
    };
  }

  function runAutofill(payload) {
    const platform = detectPlatform();
    const studentMap = buildStudentMap(payload.student_summary, payload.drive_schema);
    const inputs = Array.from(
      document.querySelectorAll("input:not([type='hidden']):not([type='submit']):not([type='button']), textarea, select")
    );

    const filled = [];
    const manualReview = [];

    for (const el of inputs) {
      if (el.offsetParent === null && el.type !== "file") continue; // skip invisible
      const descriptor = extractLabelForElement(el);

      if (el.type === "file") {
        el.style.outline = "2px solid #f59e0b";
        el.setAttribute("data-sb-highlighted", "review");
        manualReview.push("Attach Resume PDF (" + (payload.student_summary?.resume_filename || "file upload") + ")");
        continue;
      }

      if (el.tagName === "SELECT" || el.type === "checkbox" || el.type === "radio") {
        if (el.required || descriptor.includes("authorized") || descriptor.includes("sponsor")) {
          el.style.outline = "2px solid #f59e0b";
          el.setAttribute("data-sb-highlighted", "review");
          manualReview.push((descriptor.slice(0, 42) || "Dropdown/Checkbox"));
        }
        continue;
      }

      const value = resolveValueForField(descriptor, el.name || el.id, studentMap);
      if (value) {
        setNativeValue(el, value);
        el.style.outline = "2px solid #10b981";
        el.setAttribute("data-sb-highlighted", "filled");
        filled.push(el.name || descriptor.slice(0, 30) || "field");
      } else if (el.required || el.getAttribute("aria-required") === "true") {
        el.style.outline = "2px solid #f59e0b";
        el.setAttribute("data-sb-highlighted", "review");
        manualReview.push(descriptor.slice(0, 45) || "Required field");
      }
    }

    showReviewOverlay(platform, filled, manualReview);
    return { platform, filledCount: filled.length, filled, manualReview };
  }

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg?.action === "GET_PAGE_INFO") {
      sendResponse({ platform: detectPlatform(), url: window.location.href });
      return true;
    }
    if (msg?.action === "AUTOFILL_FORM") {
      const result = runAutofill(msg.payload || {});
      sendResponse({ ok: true, result });
      return true;
    }
  });
})();
