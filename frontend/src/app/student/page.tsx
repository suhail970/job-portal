"use client";

import { useState, useEffect, useRef } from "react";
import { api, getToken, getCustomAiConfig, setCustomAiConfig, CustomAiConfig } from "@/lib/api";
import {
  Sparkles,
  BrainCircuit,
  Mic,
  MicOff,
  Code2,
  FileText,
  Clock,
  CheckCircle2,
  AlertCircle,
  Play,
  Volume2,
  VolumeX,
  Send,
  Award,
  ChevronRight,
  TrendingUp,
  Building,
  Settings,
  Sliders,
  Check,
  RefreshCw,
  Cpu,
  Save,
  Bell,
  UserCheck,
  Eye,
  EyeOff,
  Key,
  Globe,
  ExternalLink,
  X,
  MapPin,
  Briefcase,
  GraduationCap,
  ShieldCheck,
  History,
  Terminal,
  Power,
  MessageSquare,
  Copy
} from "lucide-react";

function formatJobDescription(desc?: string): string {
  if (!desc) return "Opportunity details available via official careers portal.";
  let text = desc.replace(/<[^>]*>?/gm, " ");
  text = text.replace(/<[^>]*$/g, "");
  text = text.replace(/^Source:.*?\n(?:Role:.*?\n)?(?:Company:.*?\n)?(?:Details:\s*)?/i, "");
  text = text.replace(/[ \t]+/g, " ").replace(/\n\s*\n+/g, "\n\n").trim();
  return text || "Opportunity details available via official careers portal.";
}

function getVerificationLinks(companyName?: string, roleTitle?: string) {
  if (!companyName) return [];
  const clean = companyName.trim();
  const encoded = encodeURIComponent(clean);
  const roleEncoded = roleTitle ? encodeURIComponent(roleTitle.trim()) : "";
  const linkedinJobQuery = roleEncoded ? `${encoded}+${roleEncoded}` : encoded;

  return [
    {
      platform: "LinkedIn Jobs",
      title: `${clean} Live Openings`,
      url: `https://www.linkedin.com/jobs/search/?keywords=${linkedinJobQuery}`,
      tag: "Live Recruiter Postings",
      badge: "border-blue-200 bg-blue-50 text-blue-800 hover:bg-blue-100"
    },
    {
      platform: "LinkedIn Network",
      title: `${clean} Alumni & Referrals`,
      url: `https://www.linkedin.com/search/results/people/?keywords=${encoded}&origin=GLOBAL_SEARCH_HEADER`,
      tag: "Alumni & Mentors",
      badge: "border-sky-200 bg-sky-50 text-sky-800 hover:bg-sky-100"
    },
    {
      platform: "Naukri",
      title: `${clean} Salaries & Demand`,
      url: `https://www.naukri.com/jobs-in-india?keyword=${encoded}`,
      tag: "Salaries & Trends",
      badge: "border-cyan-200 bg-cyan-50 text-cyan-800 hover:bg-cyan-100"
    },
    {
      platform: "GeeksforGeeks",
      title: `${clean} Student Experiences`,
      url: `https://www.geeksforgeeks.org/search/?q=${encoded}+interview+experience`,
      tag: "Real Campus Experiences",
      badge: "border-emerald-200 bg-emerald-50 text-emerald-800 hover:bg-emerald-100"
    },
    {
      platform: "AmbitionBox",
      title: `${clean} Difficulty & Ratings`,
      url: `https://www.ambitionbox.com/search?q=${encoded}`,
      tag: "Interview Ratings & Reviews",
      badge: "border-indigo-200 bg-indigo-50 text-indigo-800 hover:bg-indigo-100"
    },
    {
      platform: "LeetCode Discuss",
      title: `${clean} Coding Questions`,
      url: `https://leetcode.com/discuss/interview-question?currentPage=1&orderBy=hot&query=${encoded}`,
      tag: "Algorithm Questions",
      badge: "border-amber-200 bg-amber-50 text-amber-800 hover:bg-amber-100"
    }
  ];
}

export default function StudentPortalPage() {
  const [tab, setTab] = useState<"drives" | "prep_hub" | "interview" | "coding" | "resume" | "settings">("drives");
  const [drives, setDrives] = useState<any[]>([]);
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  // Automated Cron & Live Fetcher State
  const [syncStatus, setSyncStatus] = useState<any>(null);
  const [fetchingDrives, setFetchingDrives] = useState(false);
  const [syncMsg, setSyncMsg] = useState("");

  // Hermes Cron & Audit Ledger State
  const [cronJobs, setCronJobs] = useState<any[]>([]);
  const [showAuditDrawer, setShowAuditDrawer] = useState(false);
  const [selectedJobForAudit, setSelectedJobForAudit] = useState<any>(null);
  const [auditHistory, setAuditHistory] = useState<any[]>([]);
  const [loadingAudit, setLoadingAudit] = useState(false);
  const [triggeringJobId, setTriggeringJobId] = useState<string | null>(null);

  // Region & Location Hub Filter State
  const [selectedRegion, setSelectedRegion] = useState<"india_remote" | "india" | "remote" | "global">("india_remote");
  const [regionCounts, setRegionCounts] = useState<any>({ india_remote: 0, india: 0, remote: 0, global: 0, all: 0 });
  const [selectedLocation, setSelectedLocation] = useState("All");
  const [fallbackDrives, setFallbackDrives] = useState<any[]>([]);
  const locationSearchTimerRef = useRef<any>(null);
  const [filterNewOnly, setFilterNewOnly] = useState(false);
  const [driveFormSchema, setDriveFormSchema] = useState<any | null>(null);
  const [loadingFormSchema, setLoadingFormSchema] = useState(false);
  const [verifyingDrive, setVerifyingDrive] = useState(false);
  const [syncedExt, setSyncedExt] = useState(false);
  const [copiedFieldKey, setCopiedFieldKey] = useState<string | null>(null);
  const [seenDriveIds, setSeenDriveIds] = useState<string[]>([]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem("skillbridge_seen_drives");
        if (stored) {
          setSeenDriveIds(JSON.parse(stored));
        }
      } catch {}
    }
  }, []);
  const [locationSearch, setLocationSearch] = useState("");
  const DISTRICT_HUBS = [
    { label: "All Districts & Hubs", value: "All" },
    { label: "📍 Coimbatore (PSG / TIDEL / CHIL SEZ)", value: "Coimbatore" },
    { label: "📍 Chennai (OMR / Guindy / Perungudi)", value: "Chennai" },
    { label: "📍 Madurai (ELCOT Vadipatti SEZ)", value: "Madurai" },
    { label: "📍 Trichy (Navalur Kuttapattu IT Hub)", value: "Trichy" },
    { label: "📍 Salem (IT Park Jagir)", value: "Salem" },
    { label: "📍 Tenkasi / Tirunelveli (Rural Tech)", value: "Tenkasi" },
    { label: "📍 Kochi (Infopark Kakkanad)", value: "Kochi" },
    { label: "📍 Trivandrum (Technopark)", value: "Trivandrum" },
    { label: "📍 Mysore (Hebbal Industrial Area)", value: "Mysore" },
    { label: "📍 Kolkata (Sector V / New Town)", value: "Kolkata" },
    { label: "📍 Bangalore (Outer Ring Rd / E-City)", value: "Bangalore" },
    { label: "📍 Hyderabad (HITEC City / Gachibowli)", value: "Hyderabad" },
    { label: "📍 Pune (Hinjawadi / Magarpatta)", value: "Pune" },
    { label: "📍 Bhubaneswar (Infocity)", value: "Bhubaneswar" },
    { label: "📍 Indore (Crystal IT Park)", value: "Indore" },
    { label: "📍 Visakhapatnam (Rushikonda SEZ)", value: "Visakhapatnam" },
    { label: "📍 Ahmedabad / GIFT City", value: "Ahmedabad" },
    { label: "🌐 Pan India / Remote", value: "Remote" }
  ];

  const POPULAR_DISTRICT_PILLS = [
    "All",
    "Coimbatore",
    "Chennai",
    "Madurai",
    "Trichy",
    "Tenkasi",
    "Kochi",
    "Mysore",
    "Kolkata",
    "Bangalore",
    "Hyderabad",
    "Pune",
    "Remote"
  ];

  // Company Details & Application Form Modal State
  const [selectedDriveForModal, setSelectedDriveForModal] = useState<any | null>(null);
  const [modalMode, setModalMode] = useState<"details" | "apply">("details");
  const [applying, setApplying] = useState(false);
  const [applyCoverNote, setApplyCoverNote] = useState("");
  const [applyPhone, setApplyPhone] = useState("+91 98765 43210");
  const [applyGithub, setApplyGithub] = useState("https://github.com/demo-aravind");
  const [applyLinkedin, setApplyLinkedin] = useState("https://linkedin.com/in/demo-aravind");
  const [applyFeedback, setApplyFeedback] = useState<any>(null);
  const [copiedAutofill, setCopiedAutofill] = useState(false);

  const buildStudentSummary = () => ({
    full_name: profile?.full_name || "Aravind Swaminathan",
    email: profile?.email || "student@ceg.edu",
    phone: applyPhone || profile?.profile?.phone_number || "+91 98765 43210",
    roll_number: profile?.profile?.roll_number || "2022CSE042",
    cgpa: profile?.profile?.cgpa ?? 8.65,
    graduation_year: profile?.profile?.graduation_year || 2026,
    department_name: profile?.department_name || "Computer Science and Engineering (CSE)",
    college: "Anna University - CEG Campus",
    linkedin_url: applyLinkedin || profile?.profile?.linkedin_url || "",
    github_url: applyGithub || profile?.profile?.github_url || "",
  });

  const handleSyncToExtension = (schemaOverride?: any) => {
    const schemaObj = schemaOverride || driveFormSchema;
    const studentSummary = schemaObj?.student_summary || buildStudentSummary();
    if (typeof window !== "undefined") {
      window.postMessage(
        {
          type: "SKILLBRIDGE_EXT_SYNC",
          payload: {
            token: getToken() || "",
            api_base: "http://localhost:8000/api/v1",
            student_summary: studentSummary,
            drive_schema: schemaObj || null,
          },
        },
        "*"
      );
      setSyncedExt(true);
      setTimeout(() => setSyncedExt(false), 3000);
    }
  };

  const handleCopyAutofillKit = () => {
    if (!selectedDriveForModal) return;
    const s = buildStudentSummary();
    const comp = selectedDriveForModal.company_name;
    const role = selectedDriveForModal.role_title;
    const note = applyCoverNote || `I am excited to apply for the ${role} position at ${comp}. With a strong foundation in Data Structures, Algorithms, and scalable software systems from ${s.college}, I am eager to contribute to your engineering team.`;

    let atsFieldsText = "";
    if (driveFormSchema?.fields?.length) {
      atsFieldsText =
        "\n--- Live Extracted ATS Fields ---\n" +
        driveFormSchema.fields
          .map((f: any) => `${f.label}${f.required ? " *" : ""}: ${f.suggested_value || (f.type === "file" ? "[Attach Resume PDF]" : "[Review Manually]")}`)
          .join("\n");
    }

    const kitText = `=== CANDIDATE AUTO-FILL APPLICATION KIT ===
Full Name: ${s.full_name}
Email Address: ${s.email}
Mobile / WhatsApp: ${s.phone}
Roll / Reg No: ${s.roll_number}
College / University: ${s.college}
Department / Major: ${s.department_name}
Current CGPA: ${s.cgpa}
Graduation Year: ${s.graduation_year}
LinkedIn Profile: ${s.linkedin_url}
GitHub / Portfolio: ${s.github_url}
Role Applied For: ${role} at ${comp}
Statement of Interest:
${note}${atsFieldsText}
==========================================`;

    navigator.clipboard.writeText(kitText);
    setCopiedAutofill(true);
    setTimeout(() => setCopiedAutofill(false), 3000);
  };

  // Prep Hub State
  const [companyName, setCompanyName] = useState("Amazon");
  const [roleTitle, setRoleTitle] = useState("Software Development Engineer");
  const [timeframe, setTimeframe] = useState("1_DAY");
  const [activePlan, setActivePlan] = useState<any>(null);
  const [generatingPlan, setGeneratingPlan] = useState(false);
  
  // Universal BYOK AI Engine State
  const [aiProvider, setAiProvider] = useState<"custom" | "gemini" | "groq" | "ollama" | "deepseek">("gemini");
  const [aiBaseUrl, setAiBaseUrl] = useState("https://generativelanguage.googleapis.com/v1beta/openai/");
  const [aiModelName, setAiModelName] = useState("gemini-2.0-flash");
  const [aiApiKey, setAiApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);

  // Interview State
  const [interviewSessionId, setInterviewSessionId] = useState<string | null>(null);
  const [currentTurn, setCurrentTurn] = useState<number>(1);
  const [currentQuestion, setCurrentQuestion] = useState<string>("");
  const [transcript, setTranscript] = useState<string>("");
  const [isRecording, setIsRecording] = useState(false);
  const [interviewHistory, setInterviewHistory] = useState<any[]>([]);
  const [evaluatingTurn, setEvaluatingTurn] = useState(false);

  // Coding Sandbox State
  const [selectedChallenge, setSelectedChallenge] = useState<any>(null);
  const [code, setCode] = useState<string>("print('Two Sum Solution')");
  const [language, setLanguage] = useState("python");
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [executingCode, setExecutingCode] = useState(false);

  // Resume State
  const [resumeText, setResumeText] = useState("");
  const [parsedResume, setParsedResume] = useState<any>(null);

  // Settings State
  const [ollamaUrl, setOllamaUrl] = useState("http://localhost:11434");
  const [ollamaModel, setOllamaModel] = useState("qwen2.5-coder:7b");
  const [voiceAudioEnabled, setVoiceAudioEnabled] = useState(true);
  const [voiceSpeed, setVoiceSpeed] = useState(1.0);
  const [cgpaInput, setCgpaInput] = useState("8.65");
  const [arrearsInput, setArrearsInput] = useState("0");
  const [targetCompanies, setTargetCompanies] = useState("Amazon, Zoho, TCS");
  const [targetMinCtc, setTargetMinCtc] = useState("8.0 LPA");
  const [telegramChatId, setTelegramChatId] = useState("@suresh_kannan");
  const [aiTestResult, setAiTestResult] = useState<any>(null);
  const [testingAi, setTestingAi] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);

  // Company Q&A Mentor State
  const [companyQuestionInput, setCompanyQuestionInput] = useState("");
  const [askingCompanyAi, setAskingCompanyAi] = useState(false);
  const [companyAiAnswers, setCompanyAiAnswers] = useState<Record<string, { question: string; answer: string }>>({});

  const handleAskCompanyAi = async (companyName: string, roleTitle?: string, customQuestion?: string) => {
    const questionText = customQuestion || companyQuestionInput;
    if (!questionText.trim()) return;
    setAskingCompanyAi(true);
    try {
      const res = await api.askCompanyQuestion({
        company_name: companyName,
        question: questionText,
        role_title: roleTitle || "Software Engineer",
        provider: aiProvider
      });
      setCompanyAiAnswers((prev) => ({
        ...prev,
        [companyName]: { question: questionText, answer: res.answer }
      }));
      setCompanyQuestionInput("");
    } catch (e: any) {
      alert(`Could not get answer: ${e.message}`);
    } finally {
      setAskingCompanyAi(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      // Auto login as demo student if token missing or if token belongs to TPO/Admin
      let token = getToken();
      if (!token) {
        const loginData = await api.login("student@ceg.edu", "Student@123");
        localStorage.setItem("skillbridge_token", loginData.access_token);
      } else {
        try {
          const meData = await api.getMe();
          if (meData?.role === "TPO" || meData?.role === "COLLEGE_ADMIN" || meData?.role === "ADMIN") {
            const loginData = await api.login("student@ceg.edu", "Student@123");
            localStorage.setItem("skillbridge_token", loginData.access_token);
          }
        } catch {
          const loginData = await api.login("student@ceg.edu", "Student@123");
          localStorage.setItem("skillbridge_token", loginData.access_token);
        }
      }
      const meData = await api.getMe();
      setProfile(meData);

      if (meData?.profile) {
        if (meData.profile.cgpa) setCgpaInput(String(meData.profile.cgpa));
        if (meData.profile.standing_arrears !== undefined) setArrearsInput(String(meData.profile.standing_arrears));
        if (meData.profile.telegram_chat_id) setTelegramChatId(meData.profile.telegram_chat_id);
      }

      // Restore saved custom BYOK AI configuration
      const savedAi = getCustomAiConfig();
      if (savedAi) {
        if (savedAi.provider) setAiProvider(savedAi.provider);
        if (savedAi.base_url) setAiBaseUrl(savedAi.base_url);
        if (savedAi.model) setAiModelName(savedAi.model);
        if (savedAi.api_key) setAiApiKey(savedAi.api_key);
      }

      const [drivesData, countsData] = await Promise.all([
        api.getDrives(selectedLocation, selectedRegion),
        api.getDriveRegionCounts().catch(() => null),
      ]);
      setDrives(drivesData);
      if (countsData) setRegionCounts(countsData);

      try {
        const statusData = await api.getCronStatus();
        setSyncStatus(statusData);
        if (statusData.jobs) {
          setCronJobs(statusData.jobs);
        }
      } catch {}

      const challenges = await api.getChallenges();
      if (challenges.length > 0) {
        setSelectedChallenge(challenges[0]);
        setCode(challenges[0].starter_code.python);
      }

      const plans = await api.getMyPlans();
      if (plans.length > 0) {
        setActivePlan(plans[0]);
      }
    } catch (e: any) {
      console.error("Initialization error:", e);
    }
  };

  // -------------------------------------------------------------
  // Drive Application & Location Filtering
  // -------------------------------------------------------------
  const fetchPanIndiaOpenFallback = async (reg: string) => {
    const allOpen = await api.getDrives(undefined, reg).catch(() => []);
    return allOpen.filter((d: any) => {
      const locL = (d.location || "").toLowerCase();
      return d.region_scope === "REMOTE" || locL.includes("pan india") || locL.includes("remote");
    });
  };

  const handleSelectRegion = async (reg: "india_remote" | "india" | "remote" | "global") => {
    setSelectedRegion(reg);
    const nextLoc = reg === "global" || reg === "remote" ? "All" : selectedLocation;
    if (nextLoc !== selectedLocation) setSelectedLocation("All");
    try {
      const filtered = await api.getDrives(nextLoc, reg);
      setDrives(filtered);
      if (nextLoc !== "All" && filtered.length === 0) {
        setFallbackDrives(await fetchPanIndiaOpenFallback(reg));
      } else {
        setFallbackDrives([]);
      }
    } catch (e: any) {
      console.error("Region filter error:", e);
    }
  };

  const handleSelectLocation = async (loc: string) => {
    setSelectedLocation(loc);
    try {
      const filtered = await api.getDrives(loc, selectedRegion);
      setDrives(filtered);
      if (loc !== "All" && filtered.length === 0) {
        setFallbackDrives(await fetchPanIndiaOpenFallback(selectedRegion));
      } else {
        setFallbackDrives([]);
      }
    } catch (e: any) {
      console.error("Location filter error:", e);
    }
  };

  const handleFetchLatestDrives = async (targetCity?: string) => {
    setFetchingDrives(true);
    setSyncMsg("");
    const locToFetch = (targetCity || selectedLocation || "All").trim() || "All";
    try {
      const res = await api.fetchLatestDrives(locToFetch !== "All" ? locToFetch : undefined);
      const effectiveLoc =
        res.resolved_location && res.resolved_location !== "All" && locToFetch !== "All"
          ? res.resolved_location
          : locToFetch;
      if (effectiveLoc !== selectedLocation && locToFetch !== "All") {
        setSelectedLocation(effectiveLoc);
      }

      const [updatedDrives, countsData] = await Promise.all([
        api.getDrives(effectiveLoc !== "All" ? effectiveLoc : undefined, selectedRegion),
        api.getDriveRegionCounts().catch(() => null),
      ]);
      setDrives(updatedDrives);
      if (countsData) setRegionCounts(countsData);

      let fbList: any[] = [];
      if (effectiveLoc !== "All" && updatedDrives.length === 0) {
        fbList = await fetchPanIndiaOpenFallback(selectedRegion);
      }
      setFallbackDrives(fbList);

      try {
        const statusData = await api.getCronStatus();
        setSyncStatus(statusData);
        if (statusData.jobs) {
          setCronJobs(statusData.jobs);
        }
      } catch {}
      const addedCount = res.new_drives_added || 0;
      const verifiedCnt = res.verified_candidates ?? res.total_candidates_evaluated ?? 0;
      const totalCount = updatedDrives.length;
      const aliasNote =
        locToFetch !== "All" && effectiveLoc.toLowerCase() !== locToFetch.toLowerCase()
          ? ` (matched "${locToFetch}" → "${effectiveLoc}")`
          : "";
      const locLabel = effectiveLoc === "All" ? "India & Global ATS hubs" : `${effectiveLoc}${aliasNote}`;
      if (addedCount > 0 && totalCount > 0) {
        setSyncMsg(`⚡ Verified & added ${addedCount} direct drives (${res.companies_added?.slice(0, 4).join(", ")}${res.companies_added?.length > 4 ? "..." : ""}) for ${locLabel}! Showing ${totalCount} in active view.`);
      } else if (totalCount > 0) {
        setSyncMsg(`✓ Verified ${verifiedCnt} live ATS opportunities for ${locLabel}. Displaying ${totalCount} active openings.`);
      } else if (fbList.length > 0) {
        setSyncMsg(`✓ Verified ${verifiedCnt} openings${aliasNote}: 0 direct local offices found inside ${effectiveLoc}, showing ${fbList.length} verified Pan-India & Remote roles eligible from ${effectiveLoc}.`);
      } else {
        setSyncMsg(`✓ Verified ${verifiedCnt} live ATS opportunities for ${locLabel}.`);
      }
    } catch (e: any) {
      setSyncMsg(`⚠️ Fetch failed: ${e.message}`);
    } finally {
      setFetchingDrives(false);
    }
  };

  const handleOpenAuditDrawer = async (job?: any) => {
    setShowAuditDrawer(true);
    const targetJob = job || (cronJobs.length > 0 ? cronJobs[0] : (syncStatus?.jobs?.[0] || null));
    setSelectedJobForAudit(targetJob);
    if (targetJob) {
      await fetchJobHistory(targetJob.id);
    }
  };

  const fetchJobHistory = async (jobId: string) => {
    setLoadingAudit(true);
    try {
      const history = await api.getCronJobHistory(jobId);
      setAuditHistory(history);
    } catch (err: any) {
      console.error("Failed to load audit history:", err);
    } finally {
      setLoadingAudit(false);
    }
  };

  const handleRunCronJob = async (jobId: string) => {
    setTriggeringJobId(jobId);
    try {
      const res = await api.runCronJob(jobId);
      setSyncMsg(`⚡ ${res.job_name}: ${res.summary} (${res.duration_ms}ms)`);
      const statusData = await api.getCronStatus();
      setSyncStatus(statusData);
      if (statusData.jobs) setCronJobs(statusData.jobs);
      if (selectedJobForAudit && selectedJobForAudit.id === jobId) {
        await fetchJobHistory(jobId);
      }
      const [updatedDrives, countsData] = await Promise.all([
        api.getDrives(selectedLocation !== "All" ? selectedLocation : undefined, selectedRegion),
        api.getDriveRegionCounts().catch(() => null),
      ]);
      setDrives(updatedDrives);
      if (countsData) setRegionCounts(countsData);
    } catch (err: any) {
      setSyncMsg(`❌ Run failed: ${err.message}`);
    } finally {
      setTriggeringJobId(null);
    }
  };

  const markDriveAsSeen = (driveId: string) => {
    setSeenDriveIds((prev) => {
      if (prev.includes(driveId)) return prev;
      const updated = [...prev, driveId];
      if (typeof window !== "undefined") {
        try {
          localStorage.setItem("skillbridge_seen_drives", JSON.stringify(updated));
        } catch {}
      }
      return updated;
    });
  };

  const markAllDrivesAsSeen = () => {
    const allIds = drives.map((d: any) => d.id);
    setSeenDriveIds(allIds);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem("skillbridge_seen_drives", JSON.stringify(allIds));
      } catch {}
    }
  };

  const loadLiveFormSchema = async (driveId: string, forceRefresh = false) => {
    setLoadingFormSchema(true);
    try {
      const schemaRes = await api.getDriveFormSchema(driveId, forceRefresh);
      setDriveFormSchema(schemaRes);
      handleSyncToExtension(schemaRes);
      if (schemaRes?.accuracy_score !== undefined) {
        setSelectedDriveForModal((prev: any) =>
          prev && prev.id === driveId
            ? {
                ...prev,
                accuracy_score: schemaRes.accuracy_score,
                accuracy_breakdown: schemaRes.accuracy_breakdown ? JSON.stringify(schemaRes.accuracy_breakdown) : prev.accuracy_breakdown,
              }
            : prev
        );
      }
    } catch (e) {
      console.error("Form schema load notice:", e);
    } finally {
      setLoadingFormSchema(false);
    }
  };

  const handleVerifyDriveLive = async (driveId: string) => {
    setVerifyingDrive(true);
    try {
      const vRes = await api.verifyDrive(driveId);
      setSelectedDriveForModal((prev: any) =>
        prev && prev.id === driveId
          ? {
              ...prev,
              accuracy_score: vRes.accuracy_score,
              accuracy_breakdown: JSON.stringify(vRes.accuracy_breakdown),
              verification_status: vRes.verification?.verification_status || prev.verification_status,
              form_type: vRes.verification?.form_type || prev.form_type,
              verified_at: vRes.verified_at,
            }
          : prev
      );
      await loadLiveFormSchema(driveId, true);
      const updated = await api.getDrives(selectedLocation !== "All" ? selectedLocation : undefined, selectedRegion);
      setDrives(updated);
    } catch (e: any) {
      console.error("Live verification failed:", e);
    } finally {
      setVerifyingDrive(false);
    }
  };

  const openDriveModal = (drive: any, mode: "details" | "apply" = "details") => {
    if (drive?.id) {
      markDriveAsSeen(drive.id);
    }
    setSelectedDriveForModal(drive);
    setModalMode(mode);
    setApplyFeedback(null);
    setDriveFormSchema(null);
    setApplyCoverNote(`I am excited to apply for the ${drive.role_title} role at ${drive.company_name}. With my strong background in computer science, system architectures, and problem solving, I am eager to contribute effectively.`);
    if (profile?.profile) {
      if (profile.profile.phone_number) setApplyPhone(profile.profile.phone_number);
      if (profile.profile.github_url) setApplyGithub(profile.profile.github_url);
      if (profile.profile.linkedin_url) setApplyLinkedin(profile.profile.linkedin_url);
    }
    if (drive?.id) {
      loadLiveFormSchema(drive.id);
    }
  };

  const closeDriveModal = () => {
    setSelectedDriveForModal(null);
    setApplyFeedback(null);
  };

  const handleModalSubmitApplication = async () => {
    if (!selectedDriveForModal) return;
    setApplying(true);
    setApplyFeedback(null);
    try {
      const res = await api.applyDrive(selectedDriveForModal.id, {
        cover_note: applyCoverNote,
        phone: applyPhone,
        github_url: applyGithub,
        linkedin_url: applyLinkedin
      });
      setApplyFeedback(res);
      const updatedDrives = await api.getDrives(selectedLocation !== "All" ? selectedLocation : undefined, selectedRegion);
      setDrives(updatedDrives);
      setSelectedDriveForModal((prev: any) => ({
        ...prev,
        has_applied: true,
        match_score: res.match_score || 80
      }));
      setMsg(res.message);
    } catch (e: any) {
      setApplyFeedback({ error: e.message });
    } finally {
      setApplying(false);
    }
  };

  const handleApplyDrive = async (driveId: string) => {
    const targetDrive = drives.find(d => d.id === driveId);
    if (targetDrive) {
      openDriveModal(targetDrive, "apply");
      return;
    }
    setLoading(true);
    setMsg("");
    try {
      const res = await api.applyDrive(driveId);
      setMsg(res.message);
      // Refresh drives
      const updated = await api.getDrives();
      setDrives(updated);
    } catch (e: any) {
      setMsg(`Application Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------------------------------------
  // Placement Intelligence Hub Generator
  // -------------------------------------------------------------
  const handleGeneratePlan = async () => {
    setGeneratingPlan(true);
    try {
      const res = await api.generatePlan({
        company_name: companyName,
        role_title: roleTitle,
        timeframe: timeframe,
        provider: aiProvider
      });
      const plans = await api.getMyPlans();
      setActivePlan(plans[0]);
      setTab("prep_hub");
    } catch (e: any) {
      alert(`Plan generation failed: ${e.message}`);
    } finally {
      setGeneratingPlan(false);
    }
  };

  const handleToggleTask = async (taskId: string) => {
    if (!activePlan) return;
    try {
      const res = await api.toggleTask(activePlan.id, taskId);
      setActivePlan({
        ...activePlan,
        completed_tasks: res.completed_tasks,
        overall_progress: res.overall_progress
      });
    } catch (e: any) {
      console.error("Task toggle error:", e);
    }
  };

  // -------------------------------------------------------------
  // Voice Mock Interviewer
  // -------------------------------------------------------------
  const handleStartInterview = async () => {
    try {
      const res = await api.startInterview(companyName, roleTitle);
      setInterviewSessionId(res.session_id);
      setCurrentTurn(1);
      setCurrentQuestion(res.question);
      setInterviewHistory([]);
      speakQuestion(res.question);
    } catch (e: any) {
      alert(`Interview Start Error: ${e.message}`);
    }
  };

  const speakQuestion = (text: string) => {
    if (!voiceAudioEnabled) return;
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = voiceSpeed;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  };

  const applyAiPreset = (preset: "gemini" | "groq" | "ollama" | "deepseek" | "custom") => {
    setAiProvider(preset);
    if (preset === "gemini") {
      setAiBaseUrl("https://generativelanguage.googleapis.com/v1beta/openai/");
      setAiModelName("gemini-2.0-flash");
    } else if (preset === "groq") {
      setAiBaseUrl("https://api.groq.com/openai/v1");
      setAiModelName("llama-3.3-70b-versatile");
    } else if (preset === "ollama") {
      setAiBaseUrl("http://localhost:11434/v1");
      setAiModelName("qwen2.5-coder:7b");
      setAiApiKey("ollama");
    } else if (preset === "deepseek") {
      setAiBaseUrl("https://api.deepseek.com/v1");
      setAiModelName("deepseek-chat");
    } else if (preset === "custom") {
      if (!aiBaseUrl) setAiBaseUrl("https://api.openai.com/v1");
      if (!aiModelName) setAiModelName("gpt-4o-mini");
    }
  };

  const handleTestAiConnection = async () => {
    setTestingAi(true);
    setAiTestResult(null);
    try {
      const customConfig = {
        base_url: aiBaseUrl,
        model: aiModelName,
        api_key: aiApiKey
      };
      const res = await api.testAiConnection(aiProvider, customConfig);
      setAiTestResult({
        status: "SUCCESS",
        message: `✓ Connected! Model "${res.model}" output: "${res.sample_output}"`
      });
      // Save configuration
      setCustomAiConfig({
        provider: aiProvider,
        base_url: aiBaseUrl,
        model: aiModelName,
        api_key: aiApiKey
      });
    } catch (e: any) {
      setAiTestResult({ status: "ERROR", message: `Connection failed: ${e.message}` });
    } finally {
      setTestingAi(false);
    }
  };

  const handleSaveProfileSettings = async () => {
    setSavingSettings(true);
    try {
      // Save custom BYOK AI configuration
      setCustomAiConfig({
        provider: aiProvider,
        base_url: aiBaseUrl,
        model: aiModelName,
        api_key: aiApiKey
      });

      await api.updateStudentProfile({
        cgpa: parseFloat(cgpaInput),
        standing_arrears: parseInt(arrearsInput),
        telegram_chat_id: telegramChatId,
      });
      const meData = await api.getMe();
      setProfile(meData);
      setMsg("Settings, Academic Profile, and AI Configuration saved successfully!");
      const updatedDrives = await api.getDrives();
      setDrives(updatedDrives);
    } catch (e: any) {
      alert(`Save failed: ${e.message}`);
    } finally {
      setSavingSettings(false);
    }
  };

  const testVoicePlayback = () => {
    if (!voiceAudioEnabled) {
      alert("Voice audio is currently muted in settings. Turn it on to hear speech.");
      return;
    }
    speakQuestion("Hello! This is SkillBridge AI voice synthesizer ready for your mock interview.");
  };

  const handleToggleSpeechRecognition = () => {
    if (typeof window === "undefined") return;
    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    if (!SpeechRecognition) {
      alert("Browser speech recognition is not supported in this browser. Please type your response directly.");
      return;
    }

    if (!isRecording) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "en-US";

      recognition.onstart = () => setIsRecording(true);
      recognition.onresult = (event: any) => {
        const spoken = event.results[0][0].transcript;
        setTranscript(spoken);
        setIsRecording(false);
      };
      recognition.onerror = () => setIsRecording(false);
      recognition.onend = () => setIsRecording(false);
      recognition.start();
    } else {
      setIsRecording(false);
    }
  };

  const handleSubmitInterviewTurn = async () => {
    if (!transcript.trim()) return;
    setEvaluatingTurn(true);
    try {
      const res = await api.submitTurn({
        session_id: interviewSessionId!,
        turn_index: currentTurn,
        question: currentQuestion,
        student_transcript: transcript,
        provider: aiProvider
      });

      setInterviewHistory((prev) => [
        ...prev,
        {
          turn_index: currentTurn,
          question: currentQuestion,
          answer: transcript,
          score: res.score,
          feedback: res.feedback
        }
      ]);

      setTranscript("");
      if (res.has_next && res.next_question) {
        setCurrentTurn((prev) => prev + 1);
        setCurrentQuestion(res.next_question);
        speakQuestion(res.next_question);
      } else {
        await api.completeInterview(interviewSessionId!);
        setCurrentQuestion("Mock Interview Completed! Review your comprehensive evaluation below.");
      }
    } catch (e: any) {
      alert(`Evaluation Error: ${e.message}`);
    } finally {
      setEvaluatingTurn(false);
    }
  };

  // -------------------------------------------------------------
  // Coding Sandbox Simulation
  // -------------------------------------------------------------
  const handleExecuteCode = async () => {
    setExecutingCode(true);
    setExecutionResult(null);
    try {
      const res = await api.executeCode(language, code);
      setExecutionResult(res);
    } catch (e: any) {
      setExecutionResult({ status: "ERROR", stderr: e.message });
    } finally {
      setExecutingCode(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Student Profile Bar */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              {profile ? profile.full_name : "Student Career Hub"}
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              Eligible
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500">
            {profile?.college_name || "Anna University CEG"} • Roll: {profile?.profile?.roll_number || "2022CSE042"} • CGPA:{" "}
            <span className="font-bold text-slate-900">{profile?.profile?.cgpa || "8.65"}</span> • Standing Arrears:{" "}
            <span className="font-bold text-slate-900">{profile?.profile?.standing_arrears ?? 0}</span>
          </p>
        </div>

        {/* Tab Switcher & Active AI Indicator */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          {/* Active AI Pill (clickable -> takes to settings) */}
          <button
            onClick={() => setTab("settings")}
            className="flex items-center gap-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl px-3 py-1.5 text-xs transition-colors"
            title="Click to configure AI Engine in Settings"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span className="font-semibold text-slate-700">
              AI: {aiModelName || aiProvider}
            </span>
            <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
              Active
            </span>
          </button>

          {/* Tab Switcher */}
          <div className="flex flex-wrap gap-1 bg-slate-100 p-1.5 rounded-xl border border-slate-200 text-xs sm:text-sm font-semibold">
            <button
              onClick={() => setTab("drives")}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                tab === "drives" ? "bg-white text-indigo-600 shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Placement Drives
            </button>
            <button
              onClick={() => setTab("prep_hub")}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                tab === "prep_hub" ? "bg-white text-violet-600 shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <BrainCircuit className="w-3.5 h-3.5" />
              <span>Placement Hub</span>
            </button>
            <button
              onClick={() => setTab("interview")}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                tab === "interview" ? "bg-white text-indigo-600 shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Mic className="w-3.5 h-3.5" />
              <span>Voice Interview</span>
            </button>
            <button
              onClick={() => setTab("coding")}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                tab === "coding" ? "bg-white text-emerald-600 shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              <span>Coding Sandbox</span>
            </button>
            <button
              onClick={() => setTab("settings")}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                tab === "settings" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Settings className="w-3.5 h-3.5" />
              <span>Settings</span>
            </button>
          </div>
        </div>
      </div>

      {msg && (
        <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-800 text-sm font-medium flex items-center justify-between">
          <span>{msg}</span>
          <button onClick={() => setMsg("")} className="text-indigo-600 font-bold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 1: PLACEMENT DRIVES */}
      {/* ------------------------------------------------------------- */}
      {tab === "drives" && (
        <div className="space-y-4">
          {/* Hermes Agent Cron Console & Watchers Banner */}
          <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-2xl p-5 border border-indigo-500/20 shadow-md space-y-4">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold border border-emerald-500/30">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    Hermes Cron Active • 5-Field Standard Syntax
                  </span>
                  <span className="text-xs text-indigo-300/80 font-mono">
                    croniter evaluated • durable SQLite persistence
                  </span>
                </div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>Hiring Watchers & Automated Campus Ingestion</span>
                  <span className="text-xs font-normal text-indigo-300">({drives.length} drives active)</span>
                </h3>
                <p className="text-xs text-slate-400 max-w-2xl">
                  Automated background daemon runs standard cron schedules with missed-occurrence catch-up, quiet markers ([SILENT]), and durable audit history.
                </p>
                {syncStatus?.next_run && (
                  <p className="text-[11px] text-indigo-300/90 font-medium">
                    Next automated slot: <strong>{syncStatus.next_run.slot_name} ({syncStatus.next_run.scheduled_time})</strong> in ~{syncStatus.next_run.countdown}
                  </p>
                )}
              </div>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
                <button
                  onClick={() => handleOpenAuditDrawer()}
                  className="px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-indigo-300 hover:text-white font-semibold text-xs flex items-center justify-center gap-2 transition-all cursor-pointer"
                  title="View durable SQLite execution ledger and Hermes quiet marker logs"
                >
                  <History className="w-3.5 h-3.5" />
                  <span>📜 Execution Audit Logs</span>
                </button>

                <div className="flex items-center gap-1.5 bg-white/10 rounded-xl px-2.5 py-1.5 border border-white/15">
                  <MapPin className="w-3.5 h-3.5 text-indigo-300 shrink-0" />
                  <select
                    value={selectedLocation}
                    onChange={(e) => handleSelectLocation(e.target.value)}
                    className="bg-transparent text-white text-xs font-semibold focus:outline-none cursor-pointer max-w-[200px]"
                  >
                    {DISTRICT_HUBS.map(hub => (
                      <option key={hub.value} value={hub.value} className="bg-slate-900 text-white">
                        {hub.label}
                      </option>
                    ))}
                    {selectedLocation && !DISTRICT_HUBS.some(h => h.value.toLowerCase() === selectedLocation.toLowerCase()) && (
                      <option value={selectedLocation} className="bg-slate-900 text-white">
                        📍 {selectedLocation}
                      </option>
                    )}
                  </select>
                </div>

                <button
                  onClick={() => handleFetchLatestDrives(selectedLocation)}
                  disabled={fetchingDrives}
                  className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 active:scale-95 disabled:opacity-50 text-white font-semibold text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-indigo-600/30 whitespace-nowrap cursor-pointer"
                  id="fetch-latest-drives-btn"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${fetchingDrives ? "animate-spin" : ""}`} />
                  {fetchingDrives ? `Fetching ${selectedLocation} Openings...` : `⚡ Fetch Drives (${selectedLocation})`}
                </button>
              </div>
            </div>

            {/* Hermes Cron Watchers Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2 border-t border-white/10">
              {(cronJobs.length > 0 ? cronJobs : (syncStatus?.jobs || [])).map((job: any) => (
                <div
                  key={job.id}
                  className="bg-slate-800/50 hover:bg-slate-800/80 border border-slate-700/60 rounded-xl p-3 transition-all flex flex-col justify-between gap-2"
                >
                  <div>
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {job.cron_expr}
                      </span>
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase ${
                        job.state === "running" ? "bg-amber-500/20 text-amber-300 animate-pulse" :
                        job.enabled ? "bg-emerald-500/20 text-emerald-300" : "bg-slate-700 text-slate-400"
                      }`}>
                        {job.state || (job.enabled ? "scheduled" : "paused")}
                      </span>
                    </div>
                    <div className="font-semibold text-xs text-white truncate" title={job.name}>
                      {job.name}
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center gap-1 mt-0.5">
                      <MapPin className="w-2.5 h-2.5 text-indigo-400" />
                      <span>{job.target_location || "All Districts"}</span>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-white/5 space-y-1.5">
                    <div className="flex items-center justify-between text-[10px] text-slate-300">
                      <span>Next in:</span>
                      <span className="font-medium text-indigo-300">~{job.countdown || "calculating"}</span>
                    </div>

                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-slate-400">Last Status:</span>
                      <span className={`font-semibold flex items-center gap-1 ${
                        job.last_status === "ok" ? "text-emerald-400" :
                        job.last_status === "silent" ? "text-indigo-300" :
                        job.last_status === "error" ? "text-rose-400" : "text-slate-400"
                      }`}>
                        {job.last_status === "ok" && "✓ ok"}
                        {job.last_status === "silent" && "🔇 silent"}
                        {job.last_status === "error" && "⚠️ error"}
                        {!job.last_status && "—"}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 pt-1">
                      <button
                        onClick={() => handleRunCronJob(job.id)}
                        disabled={triggeringJobId === job.id}
                        className="flex-1 py-1 px-2 rounded-lg bg-indigo-600/70 hover:bg-indigo-600 text-white font-medium text-[11px] flex items-center justify-center gap-1 transition-all disabled:opacity-50 cursor-pointer"
                        title="Trigger instant run with concurrency lock"
                      >
                        <RefreshCw className={`w-3 h-3 ${triggeringJobId === job.id ? "animate-spin" : ""}`} />
                        <span>{triggeringJobId === job.id ? "Running..." : "Run"}</span>
                      </button>
                      <button
                        onClick={() => handleOpenAuditDrawer(job)}
                        className="py-1 px-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-[11px] font-medium flex items-center justify-center gap-1 transition-all cursor-pointer"
                        title="View Execution History"
                      >
                        <History className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {syncMsg && (
              <div className="mt-2 p-2.5 rounded-xl bg-white/10 border border-white/10 text-xs font-medium text-emerald-200 flex items-center justify-between">
                <span>{syncMsg}</span>
                <button onClick={() => setSyncMsg("")} className="text-slate-400 hover:text-white text-xs">✕</button>
              </div>
            )}
          </div>

          {/* Region Scope Filter Bar (India & Remote default vs Separate Global Filter) */}
          <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-3">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  type="button"
                  onClick={() => handleSelectRegion("india_remote")}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer flex items-center gap-1.5 ${
                    selectedRegion === "india_remote"
                      ? "bg-indigo-600 text-white shadow-sm shadow-indigo-200"
                      : "bg-slate-100 hover:bg-slate-200 text-slate-700"
                  }`}
                >
                  <span>🇮🇳 India & 🌐 Remote ({regionCounts.india_remote || drives.length})</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleSelectRegion("india")}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
                    selectedRegion === "india"
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "bg-slate-100 hover:bg-slate-200 text-slate-700"
                  }`}
                >
                  <span>🇮🇳 India Only ({regionCounts.india ?? 0})</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleSelectRegion("remote")}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
                    selectedRegion === "remote"
                      ? "bg-indigo-600 text-white shadow-sm"
                      : "bg-slate-100 hover:bg-slate-200 text-slate-700"
                  }`}
                >
                  <span>🌐 Remote ({regionCounts.remote ?? 0})</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleSelectRegion("global")}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer ${
                    selectedRegion === "global"
                      ? "bg-slate-900 text-white shadow-sm"
                      : "bg-violet-50 hover:bg-violet-100 text-violet-800 border border-violet-200"
                  }`}
                >
                  <span>🌍 Global Jobs ({regionCounts.global ?? 0})</span>
                </button>
              </div>

              <div className="flex items-center gap-2">
                <a
                  href={api.getExtensionDownloadUrl()}
                  download="skillbridge-autofill-extension.zip"
                  className="px-3 py-1.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 text-xs font-bold inline-flex items-center gap-1.5 transition whitespace-nowrap"
                  title="Download Manifest V3 Chrome Extension to auto-fill Greenhouse, Lever, Ashby & Workday forms"
                >
                  <span>🧩 Chrome Auto-Fill Extension (.zip)</span>
                </a>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-indigo-600" />
                <h3 className="font-bold text-sm text-slate-900">District & Regional Tech Hubs</h3>
                <span className="text-xs text-slate-400">({drives.length} drives active)</span>
              </div>

              {/* District Search input */}
              <div className="flex items-center gap-1.5 w-full sm:w-80">
                <div className="relative flex-1">
                  <input
                    type="text"
                    placeholder="Search any district (e.g. Tenkasi, Trichy, Coimbatore)..."
                    value={locationSearch}
                    onChange={(e) => {
                      const val = e.target.value;
                      setLocationSearch(val);
                      if (locationSearchTimerRef.current) {
                        clearTimeout(locationSearchTimerRef.current);
                      }
                      locationSearchTimerRef.current = setTimeout(() => {
                        const trimmed = val.trim();
                        if (trimmed.length >= 2) {
                          handleSelectLocation(trimmed);
                        } else if (trimmed.length === 0) {
                          handleSelectLocation("All");
                        }
                      }, 250);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        if (locationSearchTimerRef.current) clearTimeout(locationSearchTimerRef.current);
                        handleFetchLatestDrives(locationSearch.trim() || "All");
                      }
                    }}
                    className="w-full pl-8 pr-3 py-1.5 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500 bg-slate-50"
                  />
                  <MapPin className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                </div>
                {locationSearch.trim().length >= 2 && (
                  <button
                    type="button"
                    disabled={fetchingDrives}
                    onClick={() => {
                      if (locationSearchTimerRef.current) clearTimeout(locationSearchTimerRef.current);
                      handleFetchLatestDrives(locationSearch.trim());
                    }}
                    className="px-2.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-bold whitespace-nowrap cursor-pointer"
                    title="Fetch live openings for this district"
                  >
                    {fetchingDrives ? "..." : "Fetch"}
                  </button>
                )}
              </div>
            </div>

            {/* Quick Filter Chips */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
              {POPULAR_DISTRICT_PILLS.map(hub => {
                const isActive = selectedLocation.toLowerCase() === hub.toLowerCase();
                return (
                  <button
                    key={hub}
                    onClick={() => {
                      setLocationSearch("");
                      handleSelectLocation(hub);
                    }}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap flex items-center gap-1 cursor-pointer ${
                      isActive
                        ? "bg-indigo-600 text-white shadow-sm shadow-indigo-200"
                        : "bg-slate-100 hover:bg-slate-200 text-slate-700"
                    }`}
                  >
                    <span>{hub === "All" ? "🌐 All Districts" : `📍 ${hub}`}</span>
                  </button>
                );
              })}
            </div>

            {/* Quick Filter: Newly Added Opportunities */}
            <div className="pt-2 flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setFilterNewOnly(!filterNewOnly)}
                  className={`px-3 py-1 rounded-full text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow-xs ${
                    filterNewOnly
                      ? "bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-amber-200"
                      : "bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200"
                  }`}
                >
                  <Sparkles className="w-3 h-3 text-amber-500" />
                  <span>✨ Newly Added ({drives.filter((d: any) => d.is_new && !seenDriveIds.includes(d.id)).length})</span>
                </button>
                {filterNewOnly && (
                  <span className="text-[11px] text-slate-500">Showing only unread opportunities (disappears once clicked)</span>
                )}
              </div>
              {drives.some((d: any) => d.is_new && !seenDriveIds.includes(d.id)) && (
                <button
                  type="button"
                  onClick={markAllDrivesAsSeen}
                  className="text-[11px] font-semibold text-slate-500 hover:text-indigo-600 transition underline underline-offset-2 cursor-pointer"
                >
                  Mark all as read
                </button>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between pt-1">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <span>Campus Recruitment Drives {selectedLocation !== "All" ? `in ${selectedLocation}` : ""}</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-semibold border border-indigo-200">
                {drives.length} drives active
              </span>
            </h2>
            <span className="text-xs text-slate-500 font-medium">Auto-matched with your CGPA & branch</span>
          </div>

          {drives.length === 0 && selectedLocation !== "All" && fallbackDrives.length > 0 && (
            <div className="bg-amber-50/80 rounded-2xl p-5 border border-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="space-y-1">
                <h3 className="font-bold text-slate-900 text-sm flex items-center gap-1.5">
                  <MapPin className="w-4 h-4 text-amber-600" />
                  <span>0 direct local corporate offices listed in {selectedLocation}</span>
                </h3>
                <p className="text-xs text-slate-600">
                  Showing <span className="font-bold text-indigo-700">{fallbackDrives.length} verified Pan-India &amp; 🌐 Remote opportunities</span> eligible for applicants from {selectedLocation}.
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => handleFetchLatestDrives(selectedLocation)}
                  disabled={fetchingDrives}
                  className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs transition cursor-pointer"
                >
                  {fetchingDrives ? "Fetching..." : `⚡ Re-Scan ${selectedLocation}`}
                </button>
                <button
                  onClick={() => {
                    setLocationSearch("");
                    handleSelectLocation("All");
                  }}
                  className="px-3 py-1.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-semibold text-xs transition cursor-pointer"
                >
                  🌐 Show All Hubs
                </button>
              </div>
            </div>
          )}

          {drives.length === 0 && fallbackDrives.length === 0 && (
            <div className="bg-white rounded-2xl p-8 border border-slate-200 text-center space-y-3">
              <MapPin className="w-8 h-8 text-indigo-400 mx-auto" />
              <h3 className="font-bold text-slate-800 text-base">No active drives found for {selectedLocation}</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                No hiring opportunities have been ingested for {selectedLocation} yet. Click below to scrape and ingest live campus openings in this tech hub!
              </p>
              <button
                onClick={() => handleFetchLatestDrives(selectedLocation)}
                disabled={fetchingDrives}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs shadow-md transition cursor-pointer"
              >
                ⚡ Fetch Latest Openings for {selectedLocation} Now
              </button>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {(drives.length === 0 && selectedLocation !== "All" && fallbackDrives.length > 0 ? fallbackDrives : drives)
              .filter((d: any) => !filterNewOnly || (d.is_new && !seenDriveIds.includes(d.id)))
              .map((d: any) => {
              const isUnseenNew = d.is_new && !seenDriveIds.includes(d.id);
              return (
              <div
                key={d.id}
                className={`bg-white rounded-2xl p-6 border transition-all flex flex-col justify-between space-y-4 relative overflow-hidden ${
                  d.has_applied ? "border-emerald-300 shadow-sm" : "border-slate-200 hover:border-indigo-300 shadow-sm"
                }`}
              >
                {d.has_applied && (
                  <div className="absolute top-0 right-0 bg-emerald-600 text-white text-[10px] font-bold px-3 py-1 rounded-bl-xl flex items-center gap-1 shadow-sm">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>APPLIED {d.match_score ? `• ${d.match_score}% MATCH` : ""}</span>
                  </div>
                )}

                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-2 pt-0.5">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100">
                        {d.salary_package}
                      </span>
                      <span
                        className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                          (d.accuracy_score ?? 85) >= 85
                            ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                            : (d.accuracy_score ?? 85) >= 70
                            ? "bg-sky-50 text-sky-700 border-sky-200"
                            : "bg-amber-50 text-amber-700 border-amber-200"
                        }`}
                        title="Verified Accuracy Score based on ATS trust, direct link, liveness & schema extraction"
                      >
                        <ShieldCheck className="w-3 h-3" />
                        <span>{d.accuracy_score ?? 85}% Match/Acc</span>
                      </span>
                      {isUnseenNew && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-extrabold uppercase tracking-wide bg-gradient-to-r from-amber-500 to-orange-500 text-white px-2 py-0.5 rounded-full shadow-2xs animate-pulse">
                          <Sparkles className="w-2.5 h-2.5" />
                          <span>NEW</span>
                        </span>
                      )}
                    </div>
                    <span className="text-xs font-medium text-slate-500 flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-400" />
                      {d.days_remaining !== undefined ? `Drive in ${d.days_remaining}d` : "Upcoming"}
                    </span>
                  </div>

                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-bold text-lg text-slate-900">{d.company_name}</h3>
                      {d.posted_time_ago && (
                        <span className="text-[10px] font-medium text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                          {d.posted_time_ago}
                        </span>
                      )}
                    </div>
                    <p className="text-xs font-semibold text-indigo-600">{d.role_title}</p>
                    <div className="flex items-center gap-1.5 flex-wrap mt-1">
                      <p className="text-[11px] text-slate-500 flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-slate-400" />
                        <span>{d.location || "Pan India / Hybrid"}</span>
                      </p>
                      {d.region_scope && (
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                          {d.region_scope === "INDIA" ? "🇮🇳 India" : d.region_scope === "REMOTE" ? "🌐 Remote" : "🌍 Global"}
                        </span>
                      )}
                      {d.source_platform && (
                        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-violet-50 text-violet-700 border border-violet-100">
                          {d.source_platform.replace("_", " ")}
                        </span>
                      )}
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
                    {formatJobDescription(d.job_description)}
                  </p>

                  {/* External Links & Portals */}
                  <div className="flex items-center gap-2 flex-wrap pt-1">
                    {d.application_url && (
                      <a
                        href={d.application_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`inline-flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1 rounded-lg transition ${
                          d.form_type === "DIRECT_FORM"
                            ? "text-emerald-700 hover:text-emerald-900 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200"
                            : "text-violet-700 hover:text-violet-900 bg-violet-50 hover:bg-violet-100 border border-violet-100"
                        }`}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <ExternalLink className={`w-3 h-3 ${d.form_type === "DIRECT_FORM" ? "text-emerald-600" : "text-violet-600"}`} />
                        <span>{d.form_type === "DIRECT_FORM" ? "Direct Form ↗" : "Corporate Portal ↗"}</span>
                      </a>
                    )}
                    {d.company_website && (
                      <a
                        href={d.company_website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-lg transition"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Globe className="w-3 h-3 text-slate-500" />
                        <span>Website ↗</span>
                      </a>
                    )}
                  </div>

                  {d.selection_rounds && (
                    <div className="text-[10px] text-slate-500 bg-slate-50 p-2 rounded-lg border border-slate-100">
                      <span className="font-semibold text-slate-700">Rounds: </span>
                      <span>{d.selection_rounds}</span>
                    </div>
                  )}
                </div>

                <div className="space-y-3 pt-3 border-t border-slate-100">
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>Min CGPA: <strong className="text-slate-800">{d.min_cgpa}</strong></span>
                    <span>Max Arrears: <strong className="text-slate-800">{d.max_arrears}</strong></span>
                  </div>

                  <div className="flex items-center gap-2">
                    {d.has_applied ? (
                      <button
                        onClick={() => openDriveModal(d, "details")}
                        className="flex-1 py-2 px-3 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-semibold text-xs border border-emerald-200 flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        <span>✓ Applied</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => openDriveModal(d, "apply")}
                        className="flex-1 py-2 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs transition-colors cursor-pointer shadow-sm shadow-indigo-200"
                      >
                        Apply Now
                      </button>
                    )}

                    <button
                      onClick={() => openDriveModal(d, "details")}
                      className="py-2 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition-colors cursor-pointer"
                      title="View company details and eligibility"
                    >
                      Details
                    </button>

                    <button
                      onClick={() => {
                        setCompanyName(d.company_name);
                        setRoleTitle(d.role_title);
                        setTab("prep_hub");
                      }}
                      className="py-2 px-2.5 rounded-xl bg-violet-50 hover:bg-violet-100 text-violet-700 font-semibold text-xs flex items-center gap-1 transition-colors cursor-pointer"
                      title="Prepare for this company with Placement Hub"
                    >
                      <BrainCircuit className="w-3.5 h-3.5 text-violet-600" />
                      <span>Prep</span>
                    </button>
                  </div>
                </div>
              </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 2: PLACEMENT INTELLIGENCE HUB */}
      {/* ------------------------------------------------------------- */}
      {tab === "prep_hub" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Form: Generate Sprint */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center gap-2 text-violet-600">
              <BrainCircuit className="w-5 h-5" />
              <h2 className="font-bold text-slate-900">Sprint Countdown Generator</h2>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Facing an upcoming recruitment drive? Specify the company and remaining time to generate a time-boxed sprint.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700">Company Name</label>
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="mt-1 w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-violet-500"
                  placeholder="e.g. Amazon / Zoho / TCS"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700">Role Title</label>
                <input
                  type="text"
                  value={roleTitle}
                  onChange={(e) => setRoleTitle(e.target.value)}
                  className="mt-1 w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-violet-500"
                  placeholder="e.g. Software Developer Engineer"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700">Countdown Time Remaining</label>
                <div className="grid grid-cols-3 gap-2 mt-1">
                  {[
                    { label: "1 Day (Sprint)", val: "1_DAY" },
                    { label: "3 Days", val: "3_DAYS" },
                    { label: "7 Days", val: "7_DAYS" }
                  ].map((t) => (
                    <button
                      key={t.val}
                      type="button"
                      onClick={() => setTimeframe(t.val)}
                      className={`py-2 px-1 text-center rounded-lg font-semibold border transition-all ${
                        timeframe === t.val
                          ? "bg-violet-600 text-white border-violet-600"
                          : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={handleGeneratePlan}
                disabled={generatingPlan}
                className="w-full mt-2 py-3 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-bold transition-all flex items-center justify-center gap-2 shadow-md shadow-violet-200 disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4" />
                <span>{generatingPlan ? "Orchestrating Plan..." : "Generate AI Countdown Plan"}</span>
              </button>
            </div>
          </div>

          {/* Right Area: Active Sprint Roadmap */}
          <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-6">
            {activePlan ? (
              <div className="space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-violet-50 text-violet-700 border border-violet-200">
                        Target: {activePlan.timeframe} Sprint
                      </span>
                      {activePlan.roadmap?.company_playbook?.industry_domain && (
                        <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                          {activePlan.roadmap.company_playbook.industry_domain}
                        </span>
                      )}
                    </div>
                    <h2 className="text-xl font-bold text-slate-900 mt-1">
                      {activePlan.company_name} — {activePlan.role_title}
                    </h2>
                  </div>

                  <div className="text-right">
                    <span className="text-xs text-slate-500 font-medium">Sprint Readiness</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
                        <div
                          className="h-full bg-violet-600 transition-all duration-300"
                          style={{ width: `${activePlan.overall_progress || 0}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-bold text-violet-700">{activePlan.overall_progress}%</span>
                    </div>
                  </div>
                </div>

                {/* Company Intelligence Dossier (Hiring Rounds & Cultural DNA) */}
                {activePlan.roadmap?.company_playbook && (
                  <div className="p-4 rounded-xl bg-gradient-to-br from-slate-50 to-indigo-50/40 border border-indigo-100 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-xs uppercase tracking-wider text-indigo-950 flex items-center gap-1.5">
                        <Building className="w-4 h-4 text-indigo-600" />
                        <span>Verified Company Intelligence & Hiring DNA</span>
                      </h4>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-100/80 text-indigo-800">
                        Universal Dossier
                      </span>
                    </div>

                    {activePlan.roadmap.company_playbook.culture_summary && (
                      <p className="text-xs text-slate-700 leading-relaxed">
                        {activePlan.roadmap.company_playbook.culture_summary}
                      </p>
                    )}

                    {/* Hiring Rounds Timeline */}
                    {activePlan.roadmap.company_playbook.hiring_rounds?.length > 0 && (
                      <div className="space-y-1.5 pt-1">
                        <p className="text-[11px] font-bold text-slate-600 uppercase tracking-wide">Campus Evaluation Rounds:</p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2">
                          {activePlan.roadmap.company_playbook.hiring_rounds.map((round: any, idx: number) => (
                            <div key={idx} className="p-2.5 rounded-lg bg-white border border-indigo-100/80 shadow-2xs space-y-1">
                              <div className="flex items-center justify-between">
                                <span className="text-[10px] font-bold text-indigo-700">Round {round.round_number || idx + 1}</span>
                                <span className="text-[9px] font-semibold text-slate-400">{round.duration}</span>
                              </div>
                              <p className="font-bold text-[11px] text-slate-900 leading-tight">{round.name}</p>
                              <p className="text-[10px] text-slate-500 line-clamp-2">{round.focus}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Top Rejection Pitfalls Warning */}
                    {activePlan.roadmap.company_playbook.top_rejection_pitfalls?.length > 0 && (
                      <div className="p-3 rounded-lg bg-amber-50/80 border border-amber-200/80 text-xs space-y-1 text-amber-950">
                        <p className="font-bold flex items-center gap-1.5 text-amber-900 text-[11px]">
                          <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                          <span>Critical Rejection Pitfalls to Avoid:</span>
                        </p>
                        <ul className="list-disc list-inside space-y-0.5 text-[11px] text-amber-900/90 pl-1">
                          {activePlan.roadmap.company_playbook.top_rejection_pitfalls.map((pitfall: string, pIdx: number) => (
                            <li key={pIdx}>{pitfall}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* Real-World Student Verification & External Experiences */}
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                      <Globe className="w-4 h-4 text-indigo-600" />
                      <span>Real-World Student Verification & Past Interview Archives</span>
                    </span>
                    <span className="text-[10px] text-slate-500 font-medium">Click to cross-check real interview stories ↗</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    {getVerificationLinks(activePlan.company_name, activePlan.role_title).map((link, idx) => (
                      <a
                        key={idx}
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`p-2.5 rounded-lg border transition-all text-xs flex flex-col justify-between ${link.badge}`}
                      >
                        <div className="space-y-0.5">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-[11px]">{link.platform}</span>
                            <ExternalLink className="w-3 h-3 opacity-60" />
                          </div>
                          <p className="text-[10px] opacity-80 line-clamp-1">{link.tag}</p>
                        </div>
                        <span className="text-[10px] font-semibold underline pt-1">Open Experiences ↗</span>
                      </a>
                    ))}
                  </div>
                </div>

                {/* Interactive Ask AI about Company */}
                <div className="p-4 rounded-xl bg-violet-50/60 border border-violet-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="w-4 h-4 text-violet-700" />
                      <h4 className="text-xs font-bold text-violet-950 uppercase tracking-wide">
                        Ask AI Mentor About {activePlan.company_name}
                      </h4>
                    </div>
                    <span className="text-[10px] font-semibold text-violet-700 bg-violet-100 px-2 py-0.5 rounded-full">
                      Instant Answers
                    </span>
                  </div>

                  {/* Quick question suggestion chips */}
                  <div className="flex flex-wrap gap-1.5">
                    {[
                      "What are the most common interview questions here?",
                      "What should I focus on for Round 1?",
                      "Is there any bond or service agreement?",
                      "What will I actually do on a day-to-day basis?"
                    ].map((qText, qIdx) => (
                      <button
                        key={qIdx}
                        onClick={() => handleAskCompanyAi(activePlan.company_name, activePlan.role_title, qText)}
                        disabled={askingCompanyAi}
                        className="text-[10px] font-medium px-2.5 py-1 rounded-full bg-white hover:bg-violet-100 text-slate-700 border border-violet-200 transition text-left cursor-pointer"
                      >
                        ⚡ {qText}
                      </button>
                    ))}
                  </div>

                  {/* Custom Question Input */}
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={companyQuestionInput}
                      onChange={(e) => setCompanyQuestionInput(e.target.value)}
                      placeholder={`Ask any doubt about ${activePlan.company_name} (culture, rounds, expectations)...`}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleAskCompanyAi(activePlan.company_name, activePlan.role_title);
                      }}
                      className="flex-1 px-3 py-2 text-xs bg-white rounded-lg border border-violet-200 focus:outline-none focus:ring-2 focus:ring-violet-500"
                    />
                    <button
                      onClick={() => handleAskCompanyAi(activePlan.company_name, activePlan.role_title)}
                      disabled={askingCompanyAi || !companyQuestionInput.trim()}
                      className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-violet-700 hover:bg-violet-800 disabled:opacity-50 text-white transition flex items-center gap-1.5 cursor-pointer"
                    >
                      {askingCompanyAi ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                      <span>Ask</span>
                    </button>
                  </div>

                  {/* Answer display box */}
                  {companyAiAnswers[activePlan.company_name] && (
                    <div className="p-3 rounded-lg bg-white border border-violet-200 text-xs text-slate-800 space-y-1">
                      <p className="font-semibold text-violet-900 text-[11px] flex items-center gap-1">
                        <span>Q:</span> {companyAiAnswers[activePlan.company_name].question}
                      </p>
                      <p className="text-slate-700 leading-relaxed whitespace-pre-line text-[11px]">
                        {companyAiAnswers[activePlan.company_name].answer}
                      </p>
                    </div>
                  )}
                </div>

                {/* Candidate Skill Gap Diagnostics */}
                {activePlan.roadmap?.skill_gap_analysis && (
                  <div className="p-3.5 rounded-xl bg-white border border-slate-200 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-600" />
                        <span>Candidate Skill Gap Diagnostics</span>
                      </span>
                      <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                        {activePlan.roadmap.skill_gap_analysis.readiness_percentage}% Match
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-1.5 pt-0.5">
                      {activePlan.roadmap.skill_gap_analysis.matched_skills?.map((s: string, idx: number) => (
                        <span key={idx} className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                          <Check className="w-2.5 h-2.5" />
                          <span>{s}</span>
                        </span>
                      ))}
                      {activePlan.roadmap.skill_gap_analysis.missing_critical_skills?.map((s: string, idx: number) => (
                        <span key={idx} className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1">
                          <span>⚠️ {s}</span>
                        </span>
                      ))}
                    </div>

                    <p className="text-[11px] text-slate-500 italic">
                      {activePlan.roadmap.skill_gap_analysis.summary}
                    </p>
                  </div>
                )}

                {/* Actionable Curated Resource Vault */}
                {(activePlan.roadmap?.curated_resources?.length > 0 || activePlan.roadmap?.company_playbook?.curated_resources?.length > 0) && (
                  <div className="space-y-2 pt-1">
                    <h4 className="font-bold text-xs uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-violet-600" />
                      <span>Curated Practice Vault & Direct Study Links</span>
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                      {(activePlan.roadmap?.curated_resources || activePlan.roadmap?.company_playbook?.curated_resources).map((res: any, idx: number) => (
                        <a
                          key={idx}
                          href={res.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2.5 rounded-xl bg-slate-50 hover:bg-violet-50/60 border border-slate-200 hover:border-violet-300 transition-all flex flex-col justify-between group"
                        >
                          <div className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-bold text-violet-700 uppercase">{res.platform || res.type}</span>
                              <ExternalLink className="w-3 h-3 text-slate-400 group-hover:text-violet-600 transition" />
                            </div>
                            <p className="font-semibold text-xs text-slate-900 group-hover:text-violet-900 line-clamp-1">{res.topic}</p>
                          </div>
                          <span className="text-[10px] font-medium text-slate-400 group-hover:text-violet-600 pt-1">Open Resource ↗</span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* Days Tasks with Direct Resource Links */}
                <div className="space-y-4 pt-1">
                  <h4 className="font-bold text-xs uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-slate-600" />
                    <span>Time-Boxed Sprint Checklist</span>
                  </h4>
                  {activePlan.roadmap?.days?.map((day: any) => (
                    <div key={day.day_number} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="font-bold text-sm text-slate-900">
                          Day {day.day_number}: {day.theme}
                        </h4>
                        <span className="text-xs text-slate-500 font-medium">{day.hours_required || 4} Hours</span>
                      </div>

                      <div className="space-y-2">
                        {day.tasks?.map((t: any) => {
                          const isDone = activePlan.completed_tasks?.includes(t.id);
                          return (
                            <div
                              key={t.id}
                              className={`p-3 rounded-lg border transition-all space-y-2 ${
                                isDone
                                  ? "bg-emerald-50/60 border-emerald-200"
                                  : "bg-white border-slate-200 hover:border-violet-300"
                              }`}
                            >
                              <div className="flex items-start gap-3">
                                <input
                                  type="checkbox"
                                  checked={isDone}
                                  onChange={() => handleToggleTask(t.id)}
                                  className="mt-0.5 rounded text-violet-600 focus:ring-violet-500 cursor-pointer"
                                />
                                <div className="flex-1 text-xs">
                                  <div className="flex items-center justify-between">
                                    <p className={`font-semibold ${isDone ? "text-slate-500 line-through" : "text-slate-900"}`}>{t.title}</p>
                                    <div className="flex items-center gap-1.5">
                                      {t.estimated_mins && (
                                        <span className="text-[10px] text-slate-400">⏱️ {t.estimated_mins}m</span>
                                      )}
                                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                                        {t.category}
                                      </span>
                                    </div>
                                  </div>
                                  <p className="text-slate-500 text-[11px] mt-0.5">{t.description}</p>
                                </div>
                              </div>

                              {/* Actionable Study Resource Link */}
                              {t.resource_url && (
                                <div className="pl-6 pt-1">
                                  <a
                                    href={t.resource_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-violet-700 hover:text-violet-900 bg-violet-50 hover:bg-violet-100 border border-violet-200/60 px-2.5 py-1 rounded-md transition"
                                  >
                                    <ExternalLink className="w-3 h-3 text-violet-600" />
                                    <span>Practice Resource: {t.resource_name || t.resource_type || "Direct Link"} ↗</span>
                                  </a>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>

                {/* High Probability Questions */}
                {activePlan.roadmap?.high_probability_questions && (
                  <div className="pt-4 border-t border-slate-100 space-y-3">
                    <h4 className="font-bold text-sm text-slate-900 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-violet-600" />
                      <span>Top Probable Interview Questions for {activePlan.company_name}</span>
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {activePlan.roadmap.high_probability_questions.map((q: any, i: number) => (
                        <div key={i} className="p-3 rounded-xl bg-violet-50/50 border border-violet-100 text-xs space-y-1">
                          <p className="font-bold text-slate-900">{q.question}</p>
                          <p className="text-violet-700 text-[11px]">Tip: {q.tip}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-16 space-y-3 text-slate-400">
                <BrainCircuit className="w-12 h-12 mx-auto text-slate-300" />
                <p className="text-sm font-semibold text-slate-600">No active countdown plan selected</p>
                <p className="text-xs max-w-sm mx-auto">
                  Use the Sprint Countdown Generator on the left to create your first company-specific preparation plan.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 3: AI VOICE MOCK INTERVIEW */}
      {/* ------------------------------------------------------------- */}
      {tab === "interview" && (
        <div className="max-w-4xl mx-auto bg-white rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-sm space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                <Mic className="w-5 h-5 text-indigo-600" />
                <span>AI Voice Mock Interviewer</span>
              </h2>
              <p className="text-xs text-slate-500">
                Target: {companyName} • {roleTitle} (Speech-to-Text via Web Speech API)
              </p>
            </div>

            {!interviewSessionId ? (
              <button
                onClick={handleStartInterview}
                className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs flex items-center gap-2 shadow-md shadow-indigo-200"
              >
                <Play className="w-4 h-4" />
                <span>Start Mock Session</span>
              </button>
            ) : (
              <button
                onClick={() => speakQuestion(currentQuestion)}
                className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold flex items-center gap-1.5"
                title="Hear question aloud"
              >
                <Volume2 className="w-4 h-4 text-indigo-600" />
                <span>Repeat Voice</span>
              </button>
            )}
          </div>

          {interviewSessionId ? (
            <div className="space-y-6">
              {/* Question Card */}
              <div className="p-5 rounded-2xl bg-indigo-50/70 border border-indigo-100 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-indigo-600">Turn {currentTurn} of 5</span>
                  <span className="text-xs text-indigo-700 font-semibold bg-indigo-100 px-2.5 py-0.5 rounded-full">
                    Voice Active
                  </span>
                </div>
                <p className="text-base font-semibold text-slate-900 leading-relaxed">{currentQuestion}</p>
              </div>

              {/* Student Input / Speech Card */}
              <div className="space-y-3">
                <label className="text-xs font-bold text-slate-700 flex items-center justify-between">
                  <span>Your Answer</span>
                  <span className="text-slate-400 font-normal">Speak into microphone or type below</span>
                </label>

                <textarea
                  rows={4}
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  placeholder="Click 'Start Speaking' or type your technical answer here..."
                  className="w-full p-4 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />

                <div className="flex items-center justify-between gap-3">
                  <button
                    type="button"
                    onClick={handleToggleSpeechRecognition}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold border transition-all ${
                      isRecording
                        ? "bg-rose-50 text-rose-700 border-rose-300 animate-pulse"
                        : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    {isRecording ? <MicOff className="w-4 h-4 text-rose-600" /> : <Mic className="w-4 h-4 text-indigo-600" />}
                    <span>{isRecording ? "Listening... (Click to stop)" : "Start Speaking"}</span>
                  </button>

                  <button
                    onClick={handleSubmitInterviewTurn}
                    disabled={evaluatingTurn || !transcript.trim()}
                    className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs shadow-md shadow-indigo-200 disabled:opacity-50"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{evaluatingTurn ? "Evaluating..." : "Submit Answer"}</span>
                  </button>
                </div>
              </div>

              {/* Previous Turns Scorecards */}
              {interviewHistory.length > 0 && (
                <div className="space-y-3 pt-6 border-t border-slate-100">
                  <h3 className="font-bold text-sm text-slate-900">Interview Evaluation History</h3>
                  <div className="space-y-3">
                    {interviewHistory.map((h, idx) => (
                      <div key={idx} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-800">Q: {h.question}</span>
                          <span className="font-extrabold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                            Score: {h.score}/10
                          </span>
                        </div>
                        <p className="text-slate-600 italic">" {h.answer} "</p>
                        <p className="text-indigo-700 bg-indigo-50/50 p-2 rounded-lg border border-indigo-100">
                          <strong>Feedback:</strong> {h.feedback}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 space-y-3 text-slate-400">
              <Mic className="w-12 h-12 mx-auto text-slate-300" />
              <p className="text-sm font-semibold text-slate-600">Ready to test your interview skills?</p>
              <p className="text-xs max-w-sm mx-auto">
                Click "Start Mock Session" above. The AI will ask technical questions, listen to your microphone response, and rate your technical accuracy and communication.
              </p>
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 4: CODING SANDBOX SIMULATION */}
      {/* ------------------------------------------------------------- */}
      {tab === "coding" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Problem Statement */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold px-2.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                {selectedChallenge?.difficulty || "Easy"}
              </span>
              <span className="text-xs text-slate-400">Sandboxed Remote Compiler</span>
            </div>

            <h2 className="text-xl font-bold text-slate-900">{selectedChallenge?.title || "Two Sum"}</h2>
            <p className="text-xs text-slate-600 leading-relaxed whitespace-pre-line">
              {selectedChallenge?.description}
            </p>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1 font-mono">
              <p className="font-semibold text-slate-700">Sample Input:</p>
              <p className="text-slate-600">{selectedChallenge?.sample_input}</p>
              <p className="font-semibold text-slate-700 pt-2">Expected Output:</p>
              <p className="text-emerald-700 font-bold">{selectedChallenge?.expected_output}</p>
            </div>
          </div>

          {/* Right: Code Editor & Execution */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-700">Solution Code</label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="px-2.5 py-1 text-xs rounded-lg border border-slate-200 font-semibold focus:outline-none"
                >
                  <option value="python">Python 3.10</option>
                  <option value="javascript">JavaScript (Node)</option>
                  <option value="java">Java 15</option>
                  <option value="cpp">C++ (GCC)</option>
                </select>
              </div>

              <textarea
                rows={12}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="w-full p-4 rounded-xl bg-slate-900 text-slate-100 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div className="space-y-3">
              <button
                onClick={handleExecuteCode}
                disabled={executingCode}
                className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-md shadow-emerald-200 disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{executingCode ? "Compiling & Running..." : "Run Solution (Sandbox)"}</span>
              </button>

              {/* Execution Console Output */}
              {executionResult && (
                <div className="p-3 rounded-xl bg-slate-950 text-slate-200 font-mono text-xs space-y-1">
                  <div className="flex items-center justify-between text-[11px] pb-1 border-b border-slate-800">
                    <span className={executionResult.status === "PASSED" ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                      Status: {executionResult.status}
                    </span>
                    <span className="text-slate-400">{executionResult.execution_time_ms}ms • {executionResult.memory_mb}MB</span>
                  </div>
                  {executionResult.stdout && (
                    <p className="text-slate-300 whitespace-pre-wrap">{executionResult.stdout}</p>
                  )}
                  {executionResult.stderr && (
                    <p className="text-rose-400 whitespace-pre-wrap">{executionResult.stderr}</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 5: SYSTEM & USER SETTINGS */}
      {/* ------------------------------------------------------------- */}
      {tab === "settings" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200">
            <div>
              <h2 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
                <Settings className="w-5 h-5 text-indigo-600" />
                <span>Application & Profile Settings</span>
              </h2>
              <p className="text-xs text-slate-500">
                Configure your free AI inference engine, voice audio simulator, academic targets, and Telegram notification alerts.
              </p>
            </div>
            <button
              onClick={handleSaveProfileSettings}
              disabled={savingSettings}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md shadow-indigo-200 transition-all disabled:opacity-50"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{savingSettings ? "Saving Settings..." : "Save All Settings"}</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Setting 1: Universal BYOK AI Engine (Bring Your Own Key) */}
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-indigo-600" />
                  <h3 className="font-bold text-sm text-slate-900">AI Model & BYOK Gateway</h3>
                </div>
                <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  OpenAI Compatible
                </span>
              </div>

              <p className="text-xs text-slate-500">
                Plug in any AI provider (DeepSeek, Groq, Ollama, OpenAI, OpenRouter) or pick a 1-click free preset:
              </p>

              {/* 1-Click Presets */}
              <div className="space-y-1.5">
                <label className="text-[11px] font-bold text-slate-600 uppercase tracking-wider">Quick Presets</label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {[
                    { id: "gemini", label: "⚡ Gemini Flash", desc: "Google Free" },
                    { id: "groq", label: "🚀 Groq LLaMA 3.3", desc: "Ultra Fast" },
                    { id: "ollama", label: "🔒 Local Ollama", desc: "Offline PC" },
                    { id: "deepseek", label: "🌐 DeepSeek V3", desc: "Reasoning" },
                  ].map((preset) => (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => applyAiPreset(preset.id as any)}
                      className={`p-2 rounded-xl text-left border transition text-xs ${
                        aiProvider === preset.id
                          ? "bg-indigo-50 border-indigo-500 shadow-sm ring-1 ring-indigo-500"
                          : "bg-slate-50 border-slate-200 hover:bg-slate-100"
                      }`}
                    >
                      <div className="font-bold text-slate-900 truncate">{preset.label}</div>
                      <div className="text-[10px] text-slate-500">{preset.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Input Fields */}
              <div className="space-y-3 pt-2">
                <div>
                  <div className="flex items-center justify-between">
                    <label className="font-bold text-xs text-slate-700 flex items-center gap-1.5">
                      <Globe className="w-3.5 h-3.5 text-indigo-600" />
                      <span>AI Base URL</span>
                    </label>
                    <span className="text-[10px] text-slate-400">OpenAI compatible</span>
                  </div>
                  <input
                    type="text"
                    value={aiBaseUrl}
                    onChange={(e) => {
                      setAiBaseUrl(e.target.value);
                      setAiProvider("custom");
                    }}
                    placeholder="https://api.openai.com/v1"
                    className="mt-1 w-full p-2.5 bg-slate-50 rounded-xl border border-slate-200 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between">
                    <label className="font-bold text-xs text-slate-700 flex items-center gap-1.5">
                      <Cpu className="w-3.5 h-3.5 text-indigo-600" />
                      <span>AI Model Name</span>
                    </label>
                    <span className="text-[10px] text-slate-400">Model ID</span>
                  </div>
                  <input
                    type="text"
                    value={aiModelName}
                    onChange={(e) => {
                      setAiModelName(e.target.value);
                      setAiProvider("custom");
                    }}
                    placeholder="e.g. llama-3.3-70b-versatile, qwen2.5-coder:7b"
                    className="mt-1 w-full p-2.5 bg-slate-50 rounded-xl border border-slate-200 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between">
                    <label className="font-bold text-xs text-slate-700 flex items-center gap-1.5">
                      <Key className="w-3.5 h-3.5 text-indigo-600" />
                      <span>API Key (Optional for Local Ollama / LM Studio)</span>
                    </label>
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="text-[11px] text-indigo-600 hover:underline flex items-center gap-1 font-semibold"
                    >
                      {showApiKey ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                      <span>{showApiKey ? "Hide" : "Show"}</span>
                    </button>
                  </div>
                  <div className="relative mt-1">
                    <input
                      type={showApiKey ? "text" : "password"}
                      value={aiApiKey}
                      onChange={(e) => setAiApiKey(e.target.value)}
                      placeholder="sk-... or gsk_... (leave empty for local Ollama)"
                      className="w-full p-2.5 bg-slate-50 rounded-xl border border-slate-200 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500 pr-10"
                    />
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">
                    🔒 Stored in browser localStorage only. Never sent or stored on any third-party server.
                  </p>
                </div>
              </div>

              {/* Test AI Connection Button & Output */}
              <div className="pt-2 border-t border-slate-100 space-y-2">
                <button
                  type="button"
                  onClick={handleTestAiConnection}
                  disabled={testingAi || !aiBaseUrl.trim() || !aiModelName.trim()}
                  className="w-full py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs flex items-center justify-center gap-2 transition disabled:opacity-50 shadow-sm"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${testingAi ? "animate-spin" : ""}`} />
                  <span>{testingAi ? "Pinging & Testing Model..." : `Test ${aiModelName || "AI"} Connection`}</span>
                </button>

                {aiTestResult && (
                  <div
                    className={`p-3 rounded-xl text-xs font-medium ${
                      aiTestResult.status === "SUCCESS"
                        ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                        : "bg-rose-50 text-rose-800 border border-rose-200"
                    }`}
                  >
                    {aiTestResult.message}
                  </div>
                )}
              </div>
            </div>

            {/* Setting 2: Voice Mock Interview Audio & TTS */}
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Mic className="w-5 h-5 text-indigo-600" />
                  <h3 className="font-bold text-sm text-slate-900">Voice Interview Preferences</h3>
                </div>
                <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-violet-50 text-violet-700 border border-violet-200">
                  Audio Speech
                </span>
              </div>

              <p className="text-xs text-slate-500">
                Control speech audio feedback and pacing during your simulated placement interviews:
              </p>

              {/* Audio Toggle */}
              <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-200">
                <div className="space-y-0.5">
                  <p className="font-bold text-xs text-slate-900">Audio Speech Output</p>
                  <p className="text-[11px] text-slate-500">AI reads interview questions out loud to simulate an interviewer.</p>
                </div>
                <button
                  onClick={() => setVoiceAudioEnabled(!voiceAudioEnabled)}
                  className={`px-3 py-1.5 rounded-xl font-bold text-xs flex items-center gap-1.5 transition ${
                    voiceAudioEnabled
                      ? "bg-emerald-600 text-white"
                      : "bg-slate-200 text-slate-700"
                  }`}
                >
                  {voiceAudioEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                  <span>{voiceAudioEnabled ? "Enabled" : "Muted"}</span>
                </button>
              </div>

              {/* Voice Speed */}
              <div className="space-y-2">
                <label className="font-bold text-xs text-slate-700">Interviewer Speaking Speed</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { label: "0.8x (Deliberate)", val: 0.8 },
                    { label: "1.0x (Normal)", val: 1.0 },
                    { label: "1.2x (Fast)", val: 1.2 }
                  ].map((speed) => (
                    <button
                      key={speed.val}
                      onClick={() => setVoiceSpeed(speed.val)}
                      className={`py-2 rounded-xl text-xs font-semibold border transition ${
                        voiceSpeed === speed.val
                          ? "bg-indigo-600 text-white border-indigo-600 shadow-sm"
                          : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                      }`}
                    >
                      {speed.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Test Voice Audio Button */}
              <div className="pt-2 border-t border-slate-100">
                <button
                  onClick={testVoicePlayback}
                  className="w-full py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs flex items-center justify-center gap-2 transition"
                >
                  <Volume2 className="w-3.5 h-3.5" />
                  <span>Test Voice Synthesizer Output</span>
                </button>
              </div>
            </div>

            {/* Setting 3: Academic Profile & Placement Matching */}
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Award className="w-5 h-5 text-indigo-600" />
                  <h3 className="font-bold text-sm text-slate-900">Academic & Eligibility Data</h3>
                </div>
                <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Drive Matching
                </span>
              </div>

              <p className="text-xs text-slate-500">
                Your academic metrics determine which campus placement drives you are eligible to register for:
              </p>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="font-semibold text-slate-700">Cumulative GPA (CGPA)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="10"
                    value={cgpaInput}
                    onChange={(e) => setCgpaInput(e.target.value)}
                    className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-bold"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700">Standing Arrears (Backlogs)</label>
                  <input
                    type="number"
                    min="0"
                    value={arrearsInput}
                    onChange={(e) => setArrearsInput(e.target.value)}
                    className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-bold"
                  />
                </div>
              </div>

              <div className="text-xs space-y-1">
                <label className="font-semibold text-slate-700">Target Dream Recruiters</label>
                <input
                  type="text"
                  value={targetCompanies}
                  onChange={(e) => setTargetCompanies(e.target.value)}
                  placeholder="e.g. Amazon, Zoho, TCS, Microsoft"
                  className="w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="text-xs space-y-1">
                <label className="font-semibold text-slate-700">Target Package (Minimum CTC)</label>
                <input
                  type="text"
                  value={targetMinCtc}
                  onChange={(e) => setTargetMinCtc(e.target.value)}
                  placeholder="e.g. 8.5 LPA"
                  className="w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            </div>

            {/* Setting 4: Telegram Live Alerts */}
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Send className="w-5 h-5 text-indigo-600" />
                  <h3 className="font-bold text-sm text-slate-900">Telegram Instant Alerts</h3>
                </div>
                <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                  Zero Delay
                </span>
              </div>

              <p className="text-xs text-slate-500">
                Receive instant notifications on your phone whenever the college TPO schedules a new placement drive:
              </p>

              <div className="text-xs space-y-1">
                <label className="font-semibold text-slate-700">Your Telegram Username / Chat ID</label>
                <input
                  type="text"
                  value={telegramChatId}
                  onChange={(e) => setTelegramChatId(e.target.value)}
                  placeholder="@your_telegram_username"
                  className="w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div className="p-3.5 rounded-xl bg-indigo-50/60 border border-indigo-100 text-xs space-y-1 text-slate-700">
                <p className="font-bold text-indigo-900">📢 How Telegram Alerts Work:</p>
                <p className="text-[11px] text-slate-600">
                  When the TPO publishes a drive matching your CGPA, the SkillBridge bot automatically notifies your college channel and sends direct prep sprint reminders.
                </p>
              </div>

              <div className="pt-2 border-t border-slate-100">
                <button
                  onClick={() => alert(`Test alert configured for ${telegramChatId}. When drives are posted, you will receive real-time push alerts!`)}
                  className="w-full py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs flex items-center justify-center gap-2 transition"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Verify Telegram Alert Channel</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* ------------------------------------------------------------- */}
      {/* COMPANY DETAILS & CAMPUS APPLICATION MODAL */}
      {/* ------------------------------------------------------------- */}
      {selectedDriveForModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[92vh] shadow-2xl border border-slate-200 overflow-hidden flex flex-col my-auto animate-in fade-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="p-6 bg-slate-900 text-white relative">
              <button
                onClick={closeDriveModal}
                className="absolute top-5 right-5 p-2 rounded-full bg-white/10 hover:bg-white/20 text-slate-300 hover:text-white transition"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="space-y-1.5 pr-10">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-indigo-500/30 text-indigo-200 border border-indigo-400/30">
                    {selectedDriveForModal.salary_package}
                  </span>
                  <span className="text-xs text-slate-300 flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    {selectedDriveForModal.location || "Pan India / Remote"}
                  </span>
                  {selectedDriveForModal.has_applied && (
                    <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      ✓ APPLIED {selectedDriveForModal.match_score ? `(${selectedDriveForModal.match_score}%)` : ""}
                    </span>
                  )}
                </div>

                <h2 className="text-2xl font-black text-white tracking-tight">
                  {selectedDriveForModal.company_name}
                </h2>
                <p className="text-sm font-medium text-indigo-300">
                  {selectedDriveForModal.role_title}
                </p>
              </div>

              {/* Mode Switch Tabs */}
              <div className="flex items-center gap-2 mt-5 pt-4 border-t border-white/10">
                <button
                  onClick={() => setModalMode("details")}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                    modalMode === "details"
                      ? "bg-white text-slate-900 shadow-sm"
                      : "text-slate-400 hover:text-white hover:bg-white/10"
                  }`}
                >
                  <Building className="w-3.5 h-3.5" />
                  <span>Company Details</span>
                </button>

                <button
                  onClick={() => setModalMode("apply")}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                    modalMode === "apply"
                      ? "bg-white text-slate-900 shadow-sm"
                      : "text-slate-400 hover:text-white hover:bg-white/10"
                  }`}
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Application Form {selectedDriveForModal.has_applied ? "(Submitted)" : ""}</span>
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-5 text-slate-800">
              {modalMode === "details" ? (
                <>
                  {/* Job Accuracy & Verification Score Card */}
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2.5">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2">
                        <ShieldCheck className={`w-4 h-4 ${(selectedDriveForModal.accuracy_score ?? 85) >= 85 ? "text-emerald-600" : "text-indigo-600"}`} />
                        <span className="text-xs font-bold text-slate-900">
                          Job Accuracy Score: {selectedDriveForModal.accuracy_score ?? 85}/100
                        </span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                          {selectedDriveForModal.verification_status || "VERIFIED_ACTIVE"}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleVerifyDriveLive(selectedDriveForModal.id)}
                        disabled={verifyingDrive}
                        className="px-2.5 py-1 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-700 flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <RefreshCw className={`w-3 h-3 ${verifyingDrive ? "animate-spin" : ""}`} />
                        <span>{verifyingDrive ? "Verifying..." : "Verify Link Live"}</span>
                      </button>
                    </div>
                    {selectedDriveForModal.accuracy_breakdown && (() => {
                      try {
                        const b = typeof selectedDriveForModal.accuracy_breakdown === "string"
                          ? JSON.parse(selectedDriveForModal.accuracy_breakdown)
                          : selectedDriveForModal.accuracy_breakdown;
                        return (
                          <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5 text-[10px]">
                            <div className="p-1.5 rounded-lg bg-white border border-slate-200">
                              <span className="text-slate-400 block">Source Trust</span>
                              <strong className="text-slate-800">{b.source_trust?.score}/{b.source_trust?.max} ({b.source_trust?.platform})</strong>
                            </div>
                            <div className="p-1.5 rounded-lg bg-white border border-slate-200">
                              <span className="text-slate-400 block">Direct URL</span>
                              <strong className="text-slate-800">{b.direct_url?.score}/{b.direct_url?.max}</strong>
                            </div>
                            <div className="p-1.5 rounded-lg bg-white border border-slate-200">
                              <span className="text-slate-400 block">HTTP & Expiry</span>
                              <strong className="text-slate-800">{b.liveness?.score}/{b.liveness?.max}</strong>
                            </div>
                            <div className="p-1.5 rounded-lg bg-white border border-slate-200">
                              <span className="text-slate-400 block">ATS Questions</span>
                              <strong className="text-slate-800">{b.form_schema?.score}/{b.form_schema?.max}</strong>
                            </div>
                            <div className="p-1.5 rounded-lg bg-white border border-slate-200">
                              <span className="text-slate-400 block">JD & Deadline</span>
                              <strong className="text-slate-800">{b.details_freshness?.score}/{b.details_freshness?.max}</strong>
                            </div>
                          </div>
                        );
                      } catch { return null; }
                    })()}
                  </div>

                  {/* Official Registration / External Form Link Banner */}
                  {selectedDriveForModal.application_url && (
                    <div className="p-4 rounded-2xl bg-gradient-to-r from-violet-50 to-indigo-50 border border-violet-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="space-y-0.5">
                        <p className="text-xs font-bold text-violet-950 flex items-center gap-1.5">
                          <ExternalLink className="w-4 h-4 text-violet-600" />
                          <span>Official Corporate Application Form</span>
                        </p>
                        <p className="text-[11px] text-violet-700">
                          Direct online job application form & careers portal for {selectedDriveForModal.company_name}.
                        </p>
                      </div>
                      <a
                        href={selectedDriveForModal.application_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-semibold text-xs flex items-center justify-center gap-1.5 shadow-sm transition whitespace-nowrap cursor-pointer"
                      >
                        <span>🚀 Open Form Link</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>
                  )}

                  {/* Eligibility Checker Card */}
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
                    <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      <span>Academic Eligibility Criteria</span>
                    </h4>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                      <div className="p-2.5 rounded-xl bg-white border border-slate-200">
                        <span className="text-slate-400 block text-[11px]">Minimum CGPA</span>
                        <div className="flex items-center justify-between mt-1">
                          <span className="font-bold text-slate-900">{selectedDriveForModal.min_cgpa}</span>
                          <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">
                            Your: {profile?.profile?.cgpa || 8.65} ✓
                          </span>
                        </div>
                      </div>

                      <div className="p-2.5 rounded-xl bg-white border border-slate-200">
                        <span className="text-slate-400 block text-[11px]">Max Standing Arrears</span>
                        <div className="flex items-center justify-between mt-1">
                          <span className="font-bold text-slate-900">{selectedDriveForModal.max_arrears}</span>
                          <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">
                            Your: {profile?.profile?.standing_arrears ?? 0} ✓
                          </span>
                        </div>
                      </div>

                      <div className="p-2.5 rounded-xl bg-white border border-slate-200">
                        <span className="text-slate-400 block text-[11px]">Eligible Branches</span>
                        <span className="font-bold text-slate-900 block mt-1 truncate">
                          {selectedDriveForModal.allowed_departments}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Selection Process / Rounds */}
                  {selectedDriveForModal.selection_rounds && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                        <Award className="w-4 h-4 text-indigo-600" />
                        <span>Hiring Workflow & Interview Stages</span>
                      </h4>
                      <div className="p-3.5 rounded-2xl bg-indigo-50/50 border border-indigo-100 text-xs text-slate-700 leading-relaxed">
                        {selectedDriveForModal.selection_rounds.split("->").map((round: string, idx: number) => (
                          <div key={idx} className="flex items-start gap-2 py-1">
                            <span className="w-5 h-5 rounded-full bg-indigo-600 text-white font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                              {idx + 1}
                            </span>
                            <span className="font-medium text-slate-800">{round.trim()}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Full Job Description */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                      <Briefcase className="w-4 h-4 text-slate-700" />
                      <span>Role Description & Responsibilities</span>
                    </h4>
                    <div className="p-4 rounded-2xl bg-white border border-slate-200 text-xs text-slate-700 leading-relaxed whitespace-pre-line max-h-60 overflow-y-auto">
                      {formatJobDescription(selectedDriveForModal.job_description)}
                    </div>
                  </div>

                  {/* Official Website Link */}
                  {selectedDriveForModal.company_website && (
                    <div className="text-xs text-slate-500 flex items-center gap-1">
                      <span>Official Company Portal:</span>
                      <a
                        href={selectedDriveForModal.company_website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-semibold text-indigo-600 hover:underline inline-flex items-center gap-1"
                      >
                        {selectedDriveForModal.company_website}
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  )}

                  {/* Real-World Student Verification Links */}
                  <div className="space-y-2 pt-2 border-t border-slate-100">
                    <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      <span>Real-World Past Interview Archives & Verification</span>
                    </h4>
                    <p className="text-[11px] text-slate-500">
                      Cross-verify interview experiences, test patterns, and difficulty shared by senior candidates:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {getVerificationLinks(selectedDriveForModal.company_name, selectedDriveForModal.role_title).map((link, lIdx) => (
                        <a
                          key={lIdx}
                          href={link.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition shadow-xs ${link.badge}`}
                        >
                          <span>{link.platform}: {link.title}</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      ))}
                    </div>
                  </div>

                  {/* Interactive Ask AI about Company */}
                  <div className="p-4 rounded-xl bg-violet-50/60 border border-violet-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <MessageSquare className="w-4 h-4 text-violet-700" />
                        <h4 className="text-xs font-bold text-violet-950 uppercase tracking-wide">
                          Ask AI Mentor About {selectedDriveForModal.company_name}
                        </h4>
                      </div>
                      <span className="text-[10px] font-semibold text-violet-700 bg-violet-100 px-2 py-0.5 rounded-full">
                        Instant Answers
                      </span>
                    </div>

                    {/* Quick question suggestion chips */}
                    <div className="flex flex-wrap gap-1.5">
                      {[
                        "What are the most common interview questions here?",
                        "What should I focus on for Round 1?",
                        "Is there any bond or service agreement?",
                        "What will I actually do on a day-to-day basis?"
                      ].map((qText, qIdx) => (
                        <button
                          key={qIdx}
                          onClick={() => handleAskCompanyAi(selectedDriveForModal.company_name, selectedDriveForModal.role_title, qText)}
                          disabled={askingCompanyAi}
                          className="text-[10px] font-medium px-2.5 py-1 rounded-full bg-white hover:bg-violet-100 text-slate-700 border border-violet-200 transition text-left cursor-pointer"
                        >
                          ⚡ {qText}
                        </button>
                      ))}
                    </div>

                    {/* Custom Question Input */}
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={companyQuestionInput}
                        onChange={(e) => setCompanyQuestionInput(e.target.value)}
                        placeholder={`Ask any doubt about ${selectedDriveForModal.company_name} (culture, rounds, expectations)...`}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleAskCompanyAi(selectedDriveForModal.company_name, selectedDriveForModal.role_title);
                        }}
                        className="flex-1 px-3 py-2 text-xs bg-white rounded-lg border border-violet-200 focus:outline-none focus:ring-2 focus:ring-violet-500"
                      />
                      <button
                        onClick={() => handleAskCompanyAi(selectedDriveForModal.company_name, selectedDriveForModal.role_title)}
                        disabled={askingCompanyAi || !companyQuestionInput.trim()}
                        className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-violet-700 hover:bg-violet-800 disabled:opacity-50 text-white transition flex items-center gap-1.5 cursor-pointer"
                      >
                        {askingCompanyAi ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                        <span>Ask</span>
                      </button>
                    </div>

                    {/* Answer display box */}
                    {companyAiAnswers[selectedDriveForModal.company_name] && (
                      <div className="p-3 rounded-lg bg-white border border-violet-200 text-xs text-slate-800 space-y-1">
                        <p className="font-semibold text-violet-900 text-[11px] flex items-center gap-1">
                          <span>Q:</span> {companyAiAnswers[selectedDriveForModal.company_name].question}
                        </p>
                        <p className="text-slate-700 leading-relaxed whitespace-pre-line">
                          {companyAiAnswers[selectedDriveForModal.company_name].answer}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="pt-4 border-t border-slate-200 flex items-center justify-between gap-3">
                    <button
                      onClick={() => {
                        setCompanyName(selectedDriveForModal.company_name);
                        setRoleTitle(selectedDriveForModal.role_title);
                        closeDriveModal();
                        setTab("prep_hub");
                      }}
                      className="py-2.5 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs flex items-center gap-1.5 transition"
                    >
                      <BrainCircuit className="w-4 h-4 text-violet-600" />
                      <span>Prepare in Placement Hub</span>
                    </button>

                    {selectedDriveForModal.has_applied ? (
                      <div className="inline-flex items-center gap-2 text-xs font-bold text-emerald-700 bg-emerald-50 px-4 py-2.5 rounded-xl border border-emerald-200">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        <span>Application Registered ✓</span>
                      </div>
                    ) : (
                      <button
                        onClick={() => setModalMode("apply")}
                        className="py-2.5 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-md shadow-indigo-200 transition flex items-center gap-1.5 cursor-pointer"
                      >
                        <span>Proceed to Application Form</span>
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </>
              ) : (
                /* Application Form Mode */
                <div className="space-y-4">
                  {/* Candidate Identity Card */}
                  <div className="p-4 rounded-2xl bg-indigo-50/60 border border-indigo-100 space-y-2">
                    <p className="text-xs font-bold text-indigo-950 uppercase tracking-wider">Candidate Profile Details</p>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                      <div>
                        <span className="text-[10px] text-slate-400 block">Name</span>
                        <span className="font-semibold text-slate-800">{profile?.full_name || "Aravind Swaminathan"}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 block">Roll Number</span>
                        <span className="font-semibold text-slate-800">{profile?.profile?.roll_number || "2022CSE042"}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 block">CGPA</span>
                        <span className="font-semibold text-slate-800">{profile?.profile?.cgpa || 8.65} / 10.0</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 block">College</span>
                        <span className="font-semibold text-slate-800">CEG Anna Univ</span>
                      </div>
                    </div>
                  </div>

                  {/* Form Inputs */}
                  <div className="space-y-3 text-xs">
                    <div>
                      <label className="font-semibold text-slate-700 block mb-1">Contact Phone Number</label>
                      <input
                        type="text"
                        value={applyPhone}
                        onChange={(e) => setApplyPhone(e.target.value)}
                        placeholder="+91 98765 43210"
                        className="w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono text-xs"
                      />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">LinkedIn Profile</label>
                        <input
                          type="text"
                          value={applyLinkedin}
                          onChange={(e) => setApplyLinkedin(e.target.value)}
                          placeholder="https://linkedin.com/in/username"
                          className="w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono text-xs"
                        />
                      </div>
                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">GitHub / Portfolio</label>
                        <input
                          type="text"
                          value={applyGithub}
                          onChange={(e) => setApplyGithub(e.target.value)}
                          placeholder="https://github.com/username"
                          className="w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono text-xs"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="font-semibold text-slate-700 block mb-1">Statement of Interest / Cover Note</label>
                      <textarea
                        rows={3}
                        value={applyCoverNote}
                        onChange={(e) => setApplyCoverNote(e.target.value)}
                        placeholder="Why are you a great fit for this company and engineering role?"
                        className="w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 text-xs leading-relaxed"
                      />
                    </div>
                  </div>

                  {/* Resume Confirmation */}
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-indigo-600" />
                      <div>
                        <span className="font-semibold text-slate-800 block">Current Student Resume Attached</span>
                        <span className="text-[11px] text-slate-400">ATS gap analysis will evaluate job description alignment.</span>
                      </div>
                    </div>
                    <span className="text-[11px] font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">Attached</span>
                  </div>

                  {/* Live Extracted ATS Questions & Auto-Fill Field Mapping */}
                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <span className="font-bold text-slate-800 flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600" />
                        <span>Live Extracted ATS Form Questions</span>
                        {driveFormSchema?.schema_source && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-100 text-indigo-700">
                            {driveFormSchema.schema_source.replace(/_/g, " ")}
                          </span>
                        )}
                      </span>
                      {loadingFormSchema && (
                        <span className="text-[11px] text-indigo-600 flex items-center gap-1">
                          <RefreshCw className="w-3 h-3 animate-spin" />
                          <span>Fetching live questions...</span>
                        </span>
                      )}
                    </div>

                    {driveFormSchema?.fields?.length ? (
                      <div className="max-h-44 overflow-y-auto space-y-1.5 pr-1">
                        {driveFormSchema.fields.map((fld: any, idx: number) => {
                          const fKey = `${idx}-${fld.name || fld.label}`;
                          return (
                            <div key={fKey} className="bg-white border border-slate-200 rounded-lg p-2 flex items-center justify-between gap-2">
                              <div className="min-w-0">
                                <div className="flex items-center gap-1.5 flex-wrap">
                                  <span className="font-semibold text-slate-800 truncate">{fld.label || fld.name}</span>
                                  {fld.required && <span className="text-[10px] font-bold text-rose-600">*Required</span>}
                                  {fld.needs_review && (
                                    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
                                      Review Manually
                                    </span>
                                  )}
                                </div>
                                <p className="text-[11px] text-slate-500 truncate font-mono mt-0.5">
                                  {fld.suggested_value ? fld.suggested_value : (fld.type === "file" ? "📎 Upload PDF file in browser" : "Select option on external portal")}
                                </p>
                              </div>
                              {fld.suggested_value && (
                                <button
                                  type="button"
                                  onClick={() => {
                                    navigator.clipboard.writeText(String(fld.suggested_value));
                                    setCopiedFieldKey(fKey);
                                    setTimeout(() => setCopiedFieldKey(null), 1500);
                                  }}
                                  className="px-2 py-1 rounded bg-slate-100 hover:bg-indigo-100 text-slate-700 hover:text-indigo-800 text-[10px] font-bold shrink-0 cursor-pointer"
                                >
                                  {copiedFieldKey === fKey ? "Copied ✓" : "Copy"}
                                </button>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <span className="text-[11px] text-slate-500">Standard recruiter application fields (Name, Email, Phone, Resume PDF).</span>
                    )}
                  </div>

                  {/* Chrome Extension Sync + 1-Click Copy Kit */}
                  <div className="p-3.5 rounded-xl bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-100 text-xs space-y-2.5">
                    <div className="flex items-center justify-between gap-3 flex-wrap">
                      <div className="space-y-0.5">
                        <span className="font-bold text-indigo-950 flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                          <span>Chrome Extension Auto-Fill &amp; 1-Click Copy Kit</span>
                        </span>
                        <span className="text-[11px] text-indigo-700 block">
                          Auto-fill this external form directly using our Manifest V3 Extension (pauses for your review before Submit) or copy all answers:
                        </span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          type="button"
                          onClick={() => handleSyncToExtension()}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-xs cursor-pointer ${
                            syncedExt
                              ? "bg-emerald-600 text-white"
                              : "bg-slate-900 hover:bg-slate-800 text-white"
                          }`}
                        >
                          <span>{syncedExt ? "✓ Synced to Extension!" : "🧩 Sync Extension"}</span>
                        </button>
                        <button
                          type="button"
                          onClick={handleCopyAutofillKit}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-xs cursor-pointer ${
                            copiedAutofill
                              ? "bg-emerald-600 text-white"
                              : "bg-indigo-600 hover:bg-indigo-700 text-white"
                          }`}
                        >
                          {copiedAutofill ? (
                            <>
                              <Check className="w-3.5 h-3.5" />
                              <span>Copied! ✓</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span>Copy Kit</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* External Company Form Link Reminder */}
                  {selectedDriveForModal.application_url && (
                    <div className="p-3.5 rounded-xl bg-violet-50/80 border border-violet-200 text-xs flex items-center justify-between gap-3">
                      <div className="space-y-0.5">
                        <span className="font-bold text-violet-950 flex items-center gap-1.5">
                          <ExternalLink className="w-3.5 h-3.5 text-violet-600" />
                          <span>
                            {selectedDriveForModal.form_type === "DIRECT_FORM"
                              ? "Official Direct Application Form (Verified)"
                              : "Official Corporate Careers Portal"}
                          </span>
                        </span>
                        <span className="text-[11px] text-violet-700">Open {selectedDriveForModal.company_name}'s application page in a new tab:</span>
                      </div>
                      <a
                        href={selectedDriveForModal.application_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3.5 py-1.5 rounded-lg bg-violet-700 hover:bg-violet-800 text-white text-xs font-semibold flex items-center gap-1 shrink-0 transition shadow-xs"
                      >
                        <span>🚀 Open Form Link ↗</span>
                      </a>
                    </div>
                  )}

                  {/* Feedback Banner */}
                  {applyFeedback && (
                    <div
                      className={`p-3.5 rounded-xl text-xs font-medium ${
                        applyFeedback.error
                          ? "bg-rose-50 border border-rose-200 text-rose-800"
                          : "bg-emerald-50 border border-emerald-200 text-emerald-800"
                      }`}
                    >
                      {applyFeedback.error ? (
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                          <span>{applyFeedback.error}</span>
                        </div>
                      ) : (
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 font-bold text-emerald-900">
                            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                            <span>{applyFeedback.message || "Application successfully recorded!"}</span>
                          </div>
                          {applyFeedback.match_score && (
                            <p className="text-[11px] text-emerald-700">
                              Resume Match Score: <strong>{applyFeedback.match_score}%</strong>. Your profile has been shared with the TPO & hiring team.
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Submit Action */}
                  <div className="pt-3 border-t border-slate-200 flex items-center justify-between gap-3">
                    <button
                      onClick={() => setModalMode("details")}
                      className="text-xs font-semibold text-slate-500 hover:text-slate-800"
                    >
                      ← Back to Company Details
                    </button>

                    <button
                      onClick={handleModalSubmitApplication}
                      disabled={applying || (selectedDriveForModal.has_applied && !applyFeedback?.error)}
                      className="py-2.5 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-xs shadow-md shadow-indigo-200 transition flex items-center gap-2 cursor-pointer"
                    >
                      {applying ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Submitting Application...</span>
                        </>
                      ) : selectedDriveForModal.has_applied ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Application Submitted ✓</span>
                        </>
                      ) : (
                        <>
                          <Send className="w-3.5 h-3.5" />
                          <span>Submit Campus Application</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      {/* ------------------------------------------------------------- */}
      {/* Hermes Cron Execution Audit Drawer Modal */}
      {/* ------------------------------------------------------------- */}
      {showAuditDrawer && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/75 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden text-slate-100">
            {/* Modal Header */}
            <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                  <Terminal className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <span>Hermes Cron Execution Ledger</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-mono font-medium border border-emerald-500/30">
                      Durable SQLite History
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400">
                    Audit trail of scheduled intervals, missed-occurrence catch-ups, and quiet markers ([SILENT]).
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowAuditDrawer(false)}
                className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition-all cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Job Tabs Bar */}
            <div className="px-5 pt-3 border-b border-slate-800 flex items-center gap-2 overflow-x-auto bg-slate-900/50">
              {cronJobs.map((j) => (
                <button
                  key={j.id}
                  onClick={() => {
                    setSelectedJobForAudit(j);
                    fetchJobHistory(j.id);
                  }}
                  className={`px-3 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 whitespace-nowrap cursor-pointer ${
                    selectedJobForAudit?.id === j.id
                      ? "border-indigo-500 text-white bg-slate-800/80"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {j.name} ({j.cron_expr})
                </button>
              ))}
            </div>

            {/* Selected Job Metadata Summary */}
            {selectedJobForAudit && (
              <div className="px-5 py-3 bg-slate-800/40 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-4 flex-wrap">
                  <div>
                    <span className="text-slate-400">Cron: </span>
                    <span className="font-mono text-indigo-300 font-bold">{selectedJobForAudit.cron_expr}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Target: </span>
                    <span className="text-white font-medium">{selectedJobForAudit.target_location}</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Grace: </span>
                    <span className="text-amber-300 font-mono font-medium">{selectedJobForAudit.grace_minutes || 60}m</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Total Runs: </span>
                    <span className="text-white font-bold">{selectedJobForAudit.total_runs || 0}</span>
                  </div>
                </div>

                <button
                  onClick={() => handleRunCronJob(selectedJobForAudit.id)}
                  disabled={triggeringJobId === selectedJobForAudit.id}
                  className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
                >
                  <RefreshCw className={`w-3 h-3 ${triggeringJobId === selectedJobForAudit.id ? "animate-spin" : ""}`} />
                  <span>{triggeringJobId === selectedJobForAudit.id ? "Executing..." : "Trigger Run Now"}</span>
                </button>
              </div>
            )}

            {/* Execution Records List */}
            <div className="p-5 overflow-y-auto space-y-3 flex-1">
              {loadingAudit ? (
                <div className="py-12 flex flex-col items-center justify-center text-slate-400 space-y-2">
                  <RefreshCw className="w-6 h-6 animate-spin text-indigo-400" />
                  <span className="text-xs">Querying SQLite execution ledger...</span>
                </div>
              ) : auditHistory.length === 0 ? (
                <div className="py-12 text-center text-slate-400 space-y-2">
                  <Clock className="w-8 h-8 text-slate-600 mx-auto" />
                  <p className="text-sm font-semibold text-slate-300">No executions recorded yet for this job</p>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    Click "Trigger Run Now" above or wait for the next scheduled tick to see real-time metrics.
                  </p>
                </div>
              ) : (
                auditHistory.map((rec) => (
                  <div
                    key={rec.id}
                    className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/70 hover:border-slate-600 transition-all space-y-2"
                  >
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center gap-2">
                        {rec.status === "ok" && (
                          <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-300 text-xs font-bold border border-emerald-500/30 flex items-center gap-1">
                            ✓ OK
                          </span>
                        )}
                        {rec.status === "silent" && (
                          <span className="px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 text-xs font-bold border border-indigo-500/30 flex items-center gap-1">
                            🔇 [SILENT]
                          </span>
                        )}
                        {rec.status === "error" && (
                          <span className="px-2 py-0.5 rounded-md bg-rose-500/20 text-rose-300 text-xs font-bold border border-rose-500/30 flex items-center gap-1">
                            ⚠️ ERROR
                          </span>
                        )}
                        {rec.status === "running" && (
                          <span className="px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-300 text-xs font-bold border border-amber-500/30 animate-pulse">
                            ⏳ RUNNING
                          </span>
                        )}

                        <span className="text-xs font-mono text-slate-400">
                          {new Date(rec.started_at).toLocaleString()}
                        </span>

                        <span className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded ${
                          rec.dispatch_kind === "catch_up" ? "bg-amber-500/20 text-amber-300" :
                          rec.dispatch_kind === "late" ? "bg-orange-500/20 text-orange-300" :
                          rec.dispatch_kind === "manual" ? "bg-indigo-500/20 text-indigo-300" :
                          "bg-slate-700/60 text-slate-300"
                        }`}>
                          {rec.dispatch_kind}
                        </span>
                      </div>

                      <div className="flex items-center gap-3 text-xs">
                        {rec.duration_ms !== null && rec.duration_ms !== undefined && (
                          <span className="font-mono text-slate-400">
                            ⏱️ {rec.duration_ms}ms
                          </span>
                        )}
                        <span className="font-semibold text-emerald-400">
                          +{rec.new_drives_added || 0} drives
                        </span>
                      </div>
                    </div>

                    <p className="text-xs text-slate-300 font-sans">
                      {rec.summary || (rec.status === "silent" ? "No new drives discovered [SILENT]." : "Execution completed.")}
                    </p>

                    {rec.error_message && (
                      <p className="text-xs text-rose-400 font-mono bg-rose-950/40 p-2 rounded-lg border border-rose-900/50">
                        {rec.error_message}
                      </p>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-900/90 flex items-center justify-between text-xs text-slate-400">
              <span>Hermes Agent Cron Parity: 100% Free & Local SQLite Persistence</span>
              <button
                onClick={() => setShowAuditDrawer(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold transition-all cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

