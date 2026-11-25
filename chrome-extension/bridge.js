// SkillBridge Web App <-> Chrome Extension Bridge (runs on localhost:3000)
(function () {
  function syncTokenFromLocalStorage() {
    try {
      const token = window.localStorage.getItem("skillbridge_token");
      if (token && chrome?.storage?.local) {
        chrome.storage.local.set({ skillbridge_token: token, skillbridge_api_base: "http://localhost:8000/api/v1" });
      }
    } catch {}
  }

  syncTokenFromLocalStorage();

  window.addEventListener("message", (event) => {
    if (event.source !== window || !event.data) return;
    if (event.data.type === "SKILLBRIDGE_EXT_SYNC") {
      const payload = event.data.payload || {};
      chrome.storage.local.set(
        {
          skillbridge_token: payload.token || window.localStorage.getItem("skillbridge_token") || "",
          skillbridge_api_base: payload.api_base || "http://localhost:8000/api/v1",
          skillbridge_student_summary: payload.student_summary || null,
          skillbridge_active_schema: payload.drive_schema || null,
          skillbridge_synced_at: new Date().toISOString(),
        },
        () => {
          window.postMessage(
            { type: "SKILLBRIDGE_EXT_SYNC_ACK", ok: true, synced_at: new Date().toISOString() },
            "*"
          );
        }
      );
    }
  });
})();

