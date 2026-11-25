const API_BASE = "http://localhost:8000/api/v1";

export function getToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("skillbridge_token");
  }
  return null;
}

export function setToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("skillbridge_token", token);
  }
}

export function clearToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("skillbridge_token");
  }
}

export interface CustomAiConfig {
  provider: "custom" | "gemini" | "groq" | "ollama" | "deepseek";
  base_url: string;
  model: string;
  api_key: string;
}

export function getCustomAiConfig(): CustomAiConfig | null {
  if (typeof window !== "undefined") {
    try {
      const saved = localStorage.getItem("skillbridge_custom_ai");
      if (saved) return JSON.parse(saved);
    } catch {}
  }
  return null;
}

export function setCustomAiConfig(config: CustomAiConfig) {
  if (typeof window !== "undefined") {
    localStorage.setItem("skillbridge_custom_ai", JSON.stringify(config));
  }
}

async function request(endpoint: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(errorData.detail || `HTTP Error ${res.status}`);
  }

  return res.json();
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request("/auth/login-json", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  getMe: () => request("/auth/me"),

  // Drives
  getDrives: (location?: string, region: string = "india_remote") => {
    const params = new URLSearchParams();
    params.set("region", region || "india_remote");
    if (location && location !== "All") params.set("location", location);
    return request(`/drives?${params.toString()}`);
  },
  getDriveRegionCounts: () => request("/drives/region-counts"),
  getDrive: (id: string) => request(`/drives/${id}`),
  getDriveFormSchema: (id: string, refresh: boolean = false) =>
    request(`/drives/${id}/form-schema${refresh ? "?refresh=true" : ""}`),
  verifyDrive: (id: string) =>
    request(`/drives/${id}/verify`, { method: "POST" }),
  getExtensionDownloadUrl: () => `${API_BASE}/drives/extension/download`,
  fetchLatestDrives: (location?: string) =>
    request(location && location !== "All" ? `/drives/fetch-latest?location=${encodeURIComponent(location)}` : "/drives/fetch-latest", {
      method: "POST",
    }),
  getDriveSyncStatus: () => request("/drives/sync-status"),
  applyDrive: (id: string, payload?: { cover_note?: string; phone?: string; github_url?: string; linkedin_url?: string }) =>
    request(`/drives/${id}/apply`, {
      method: "POST",
      body: payload ? JSON.stringify(payload) : undefined,
    }),
  getDriveApplicants: (id: string) => request(`/drives/${id}/applicants`),
  createDrive: (driveData: any) =>
    request("/drives", {
      method: "POST",
      body: JSON.stringify(driveData),
    }),

  // Placement Hub (Countdown Plans)
  generatePlan: (data: { company_name: string; role_title: string; timeframe: string; drive_id?: string; provider?: string; custom_config?: any }) => {
    const customConfig = data.custom_config || getCustomAiConfig();
    return request("/prep-hub/generate", {
      method: "POST",
      body: JSON.stringify({ ...data, custom_config: customConfig }),
    });
  },
  getMyPlans: () => request("/prep-hub/my-plans"),
  getCompanyPlaybook: (company_name: string, role_title?: string) =>
    request(`/prep-hub/playbook?company_name=${encodeURIComponent(company_name)}${role_title ? `&role_title=${encodeURIComponent(role_title)}` : ""}`),
  askCompanyQuestion: (data: { company_name: string; question: string; role_title?: string; provider?: string; custom_config?: any }) => {
    const customConfig = data.custom_config || getCustomAiConfig();
    return request("/prep-hub/ask-company", {
      method: "POST",
      body: JSON.stringify({ ...data, custom_config: customConfig }),
    });
  },
  toggleTask: (planId: string, taskId: string) =>
    request(`/prep-hub/${planId}/toggle-task`, {
      method: "POST",
      body: JSON.stringify({ task_id: taskId }),
    }),

  // Mock Interview
  startInterview: (company_name: string, role_title: string) =>
    request("/interview/start", {
      method: "POST",
      body: JSON.stringify({ company_name, role_title }),
    }),
  submitTurn: (data: { session_id: string; turn_index: number; question: string; student_transcript: string; provider?: string; custom_config?: any }) => {
    const customConfig = data.custom_config || getCustomAiConfig();
    return request("/interview/turn", {
      method: "POST",
      body: JSON.stringify({ ...data, custom_config: customConfig }),
    });
  },
  completeInterview: (sessionId: string) =>
    request(`/interview/${sessionId}/complete`, {
      method: "POST",
    }),

  // Coding Sandbox Simulation
  executeCode: (language: string, code: string, stdin: string = "") =>
    request("/simulation/execute-code", {
      method: "POST",
      body: JSON.stringify({ language, code, stdin }),
    }),
  getChallenges: () => request("/simulation/challenges"),

  // Resume
  getMyResume: () => request("/resume/my-resume"),
  parseTextResume: (raw_text: string, provider?: string, custom_config?: any) => {
    const customConfig = custom_config || getCustomAiConfig();
    return request("/resume/parse-text", {
      method: "POST",
      body: JSON.stringify({ raw_text, provider, custom_config: customConfig }),
    });
  },

  // Telegram Drive Broadcast
  broadcastDriveTelegram: (driveId: string) =>
    request(`/drives/${driveId}/broadcast-telegram`, {
      method: "POST",
    }),

  // AI Connection Test
  testAiConnection: (provider: string, custom_config?: any) =>
    request("/ai/test-connection", {
      method: "POST",
      body: JSON.stringify({ provider, custom_config }),
    }),

  // Student Profile Settings
  getStudentProfile: () => request("/students/me"),
  updateStudentProfile: (data: any) =>
    request("/students/me", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  // TPO Leaderboard
  getLeaderboard: () => request("/students/leaderboard"),

  // Hermes Cron Subsystem
  getCronStatus: () => request("/cron/status"),
  getCronJobs: () => request("/cron/jobs"),
  getCronJob: (id: string) => request(`/cron/jobs/${id}`),
  createCronJob: (data: {
    name: string;
    cron_expr: string;
    target_location?: string;
    description?: string;
    grace_minutes?: number;
  }) =>
    request("/cron/jobs", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateCronJob: (
    id: string,
    data: {
      name?: string;
      cron_expr?: string;
      target_location?: string;
      description?: string;
      enabled?: boolean;
      grace_minutes?: number;
    }
  ) =>
    request(`/cron/jobs/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  deleteCronJob: (id: string) =>
    request(`/cron/jobs/${id}`, {
      method: "DELETE",
    }),
  runCronJob: (id: string) =>
    request(`/cron/jobs/${id}/run`, {
      method: "POST",
    }),
  getCronJobHistory: (id: string, limit?: number) =>
    request(`/cron/jobs/${id}/history${limit ? `?limit=${limit}` : ""}`),
};

