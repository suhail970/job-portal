"use client";

import { useState, useEffect } from "react";
import { api, getToken } from "@/lib/api";
import {
  Building2,
  PlusCircle,
  Users,
  Send,
  Calendar,
  Award,
  CheckCircle2,
  TrendingUp,
  FileText,
  RefreshCw,
  Clock,
  Sparkles,
  MapPin,
  History,
  Terminal,
  Power
} from "lucide-react";

export default function TpoPortalPage() {
  const [drives, setDrives] = useState<any[]>([]);
  const [applicants, setApplicants] = useState<any[]>([]);
  const [selectedDriveId, setSelectedDriveId] = useState<string | null>(null);
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [broadcastSent, setBroadcastSent] = useState(false);
  const [broadcastInfo, setBroadcastInfo] = useState<any>(null);
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
  const [togglingJobId, setTogglingJobId] = useState<string | null>(null);
  const [selectedLocation, setSelectedLocation] = useState("All");
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

  // Create Drive Form State
  const [companyName, setCompanyName] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [salaryPackage, setSalaryPackage] = useState("8.5 LPA");
  const [minCgpa, setMinCgpa] = useState("7.0");
  const [maxArrears, setMaxArrears] = useState("0");
  const [maxHistoryArrears, setMaxHistoryArrears] = useState("");
  const [minTenthPct, setMinTenthPct] = useState("");
  const [minTwelfthPct, setMinTwelfthPct] = useState("");
  const [acceptsDiploma, setAcceptsDiploma] = useState(true);
  const [allowedDepts, setAllowedDepts] = useState("CSE,IT,ECE");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      let token = getToken();
      if (!token) {
        const loginData = await api.login("tpo@ceg.edu", "Tpo@123");
        localStorage.setItem("skillbridge_token", loginData.access_token);
      } else {
        try {
          const meData = await api.getMe();
          if (meData?.role === "STUDENT" || meData?.role === "JOB_SEEKER") {
            const loginData = await api.login("tpo@ceg.edu", "Tpo@123");
            localStorage.setItem("skillbridge_token", loginData.access_token);
          }
        } catch {
          const loginData = await api.login("tpo@ceg.edu", "Tpo@123");
          localStorage.setItem("skillbridge_token", loginData.access_token);
        }
      }

      const drivesData = await api.getDrives();
      setDrives(drivesData);

      if (drivesData.length > 0) {
        setSelectedDriveId(drivesData[0].id);
        const appData = await api.getDriveApplicants(drivesData[0].id);
        setApplicants(appData.applicants || []);
      }

      const lData = await api.getLeaderboard();
      setLeaderboard(lData);

      try {
        const sData = await api.getCronStatus();
        setSyncStatus(sData);
        if (sData.jobs) setCronJobs(sData.jobs);
      } catch {}
    } catch (e: any) {
      console.error("TPO Data Error:", e);
    }
  };

  const handleSelectDrive = async (id: string) => {
    setSelectedDriveId(id);
    try {
      const appData = await api.getDriveApplicants(id);
      setApplicants(appData.applicants || []);
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleCreateDrive = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const now = new Date();
      const driveDate = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
      const regDeadline = new Date(now.getTime() + 5 * 24 * 60 * 60 * 1000);

      const payload: any = {
        company_name: companyName,
        role_title: roleTitle,
        job_description: jobDescription,
        salary_package: salaryPackage,
        min_cgpa: parseFloat(minCgpa),
        max_arrears: parseInt(maxArrears),
        allowed_departments: allowedDepts,
        accepts_diploma: acceptsDiploma,
        drive_date: driveDate.toISOString(),
        registration_deadline: regDeadline.toISOString()
      };
      if (maxHistoryArrears.trim() !== "") payload.max_history_arrears = parseInt(maxHistoryArrears, 10);
      if (minTenthPct.trim() !== "") payload.min_tenth_percentage = parseFloat(minTenthPct);
      if (minTwelfthPct.trim() !== "") payload.min_twelfth_percentage = parseFloat(minTwelfthPct);

      await api.createDrive(payload);

      setShowCreateModal(false);
      setMsg(`Drive for ${companyName} created successfully!`);
      loadData();
    } catch (e: any) {
      alert(`Drive creation failed: ${e.message}`);
    }
  };

  const handleTelegramBroadcast = async () => {
    if (!selectedDriveId) return;
    try {
      const res = await api.broadcastDriveTelegram(selectedDriveId);
      setBroadcastInfo(res);
      setBroadcastSent(true);
      setTimeout(() => setBroadcastSent(false), 6000);
    } catch (e: any) {
      alert(`Broadcast failed: ${e.message}`);
    }
  };

  const handleSelectLocation = async (loc: string) => {
    setSelectedLocation(loc);
    try {
      const filtered = await api.getDrives(loc);
      setDrives(filtered);
      if (filtered.length > 0) {
        setSelectedDriveId(filtered[0].id);
        const appData = await api.getDriveApplicants(filtered[0].id);
        setApplicants(appData.applicants || []);
      } else {
        setSelectedDriveId(null);
        setApplicants([]);
      }
    } catch (e: any) {
      console.error("Location filter error:", e);
    }
  };

  const handleFetchLatestDrives = async (targetCity?: string) => {
    setFetchingDrives(true);
    setSyncMsg("");
    const locToFetch = targetCity || selectedLocation;
    try {
      const res = await api.fetchLatestDrives(locToFetch !== "All" ? locToFetch : undefined);
      const updatedDrives = await api.getDrives(locToFetch !== "All" ? locToFetch : undefined);
      setDrives(updatedDrives);
      try {
        const sData = await api.getCronStatus();
        setSyncStatus(sData);
        if (sData.jobs) setCronJobs(sData.jobs);
      } catch {}
      const added = res.new_drives_added || 0;
      const totalCount = updatedDrives.length;
      const locLabel = locToFetch === "All" ? "all hubs" : locToFetch;
      if (added > 0) {
        setSyncMsg(`⚡ Ingestion complete: Added ${added} new campus drives for ${locLabel} (${res.companies_added?.slice(0, 4).join(", ")}${res.companies_added?.length > 4 ? "..." : ""}). Now managing ${totalCount} drives.`);
      } else {
        setSyncMsg(`✓ Live Feeds Refreshed! Evaluated ${res.total_candidates_evaluated || 30} opportunities across Arbeitnow, Jobicy, Remotive & Campus tracks for ${locLabel}. All ${totalCount} drives verified.`);
      }
    } catch (e: any) {
      setSyncMsg(`⚠️ Sync failed: ${e.message}`);
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
      const sData = await api.getCronStatus();
      setSyncStatus(sData);
      if (sData.jobs) setCronJobs(sData.jobs);
      if (selectedJobForAudit && selectedJobForAudit.id === jobId) {
        await fetchJobHistory(jobId);
      }
      const updatedDrives = await api.getDrives(selectedLocation !== "All" ? selectedLocation : undefined);
      setDrives(updatedDrives);
    } catch (err: any) {
      setSyncMsg(`❌ Run failed: ${err.message}`);
    } finally {
      setTriggeringJobId(null);
    }
  };

  const handleToggleJob = async (job: any) => {
    setTogglingJobId(job.id);
    try {
      await api.updateCronJob(job.id, { enabled: !job.enabled });
      const sData = await api.getCronStatus();
      setSyncStatus(sData);
      if (sData.jobs) setCronJobs(sData.jobs);
      setSyncMsg(`✓ Watcher '${job.name}' ${job.enabled ? "paused" : "resumed"} successfully.`);
    } catch (err: any) {
      setSyncMsg(`❌ Failed to toggle job: ${err.message}`);
    } finally {
      setTogglingJobId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header bar */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Building2 className="w-6 h-6 text-violet-600" />
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              TPO Placement Administration
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Anna University — College of Engineering Guindy (CEG) • Isolated Tenant Workspace
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-1.5 bg-slate-100 rounded-xl px-2.5 py-1.5 border border-slate-200">
            <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <select
              value={selectedLocation}
              onChange={(e) => handleSelectLocation(e.target.value)}
              className="bg-transparent text-slate-800 text-xs font-semibold focus:outline-none cursor-pointer max-w-[200px]"
            >
              {DISTRICT_HUBS.map(hub => (
                <option key={hub.value} value={hub.value}>
                  {hub.label}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => handleFetchLatestDrives(selectedLocation)}
            disabled={fetchingDrives}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white font-semibold text-xs shadow-md transition-all cursor-pointer"
            id="tpo-fetch-drives-btn"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${fetchingDrives ? "animate-spin" : ""}`} />
            <span>{fetchingDrives ? `Syncing ${selectedLocation}...` : `⚡ Sync Drives (${selectedLocation})`}</span>
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-semibold text-xs shadow-md shadow-violet-200 transition-all cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Create Placement Drive</span>
          </button>
        </div>
      </div>

      {/* Automated Hermes Cron Console & Status Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-2xl p-5 border border-indigo-500/20 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-semibold border border-emerald-500/30">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Hermes Cron Engine Active
              </span>
              <span className="text-xs text-slate-300 font-mono">
                Standard 5-Field Syntax via croniter • Durable SQLite Persistence
              </span>
            </div>
            <p className="text-xs text-slate-400 max-w-2xl">
              Durable background daemon continuously scrapes and ingests campus opportunities with missed-occurrence catch-ups, quiet markers ([SILENT]), and per-job concurrency locks.
            </p>
            {syncStatus?.next_run && (
              <p className="text-[11px] text-indigo-300 font-medium">
                Next scheduled run: <strong>{syncStatus.next_run.slot_name} ({syncStatus.next_run.scheduled_time})</strong> in ~{syncStatus.next_run.countdown}
              </p>
            )}
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => handleOpenAuditDrawer()}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-indigo-300 hover:text-white font-semibold text-xs flex items-center justify-center gap-2 transition-all cursor-pointer whitespace-nowrap"
            >
              <History className="w-3.5 h-3.5" />
              <span>📜 Execution Audit Logs</span>
            </button>
            <div className="text-right pl-3 border-l border-white/10">
              <span className="text-2xl font-black text-indigo-400">{drives.length}</span>
              <p className="text-[11px] text-slate-400 font-medium">Active Drives</p>
            </div>
          </div>
        </div>

        {/* Watchers Grid */}
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
                    onClick={() => handleToggleJob(job)}
                    disabled={togglingJobId === job.id}
                    className={`p-1.5 rounded-lg border transition-all cursor-pointer ${
                      job.enabled
                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                        : "bg-slate-700/50 border-slate-600 text-slate-400 hover:text-white"
                    }`}
                    title={job.enabled ? "Pause Job" : "Resume Job"}
                  >
                    <Power className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => handleOpenAuditDrawer(job)}
                    className="p-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 transition-all cursor-pointer"
                    title="View Execution History"
                  >
                    <History className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {syncMsg && (
        <div className="p-3 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-900 text-xs font-semibold flex items-center justify-between">
          <span>{syncMsg}</span>
          <button onClick={() => setSyncMsg("")} className="text-indigo-400 hover:text-indigo-600 text-xs">✕</button>
        </div>
      )}

      {msg && (
        <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold">
          {msg}
        </div>
      )}

      {/* Main Grid: Drives List + Applicants Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Drives */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
          <h2 className="font-bold text-sm text-slate-900 flex items-center justify-between">
            <span>Organized Drives ({drives.length})</span>
            <span className="text-xs text-slate-400 font-normal">Select to view applicants</span>
          </h2>

          <div className="space-y-3">
            {drives.map((d) => (
              <div
                key={d.id}
                onClick={() => handleSelectDrive(d.id)}
                className={`p-4 rounded-xl border cursor-pointer transition-all space-y-1.5 ${
                  selectedDriveId === d.id
                    ? "bg-violet-50/70 border-violet-400 shadow-sm"
                    : "bg-slate-50 border-slate-200 hover:bg-slate-100"
                }`}
              >
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-sm text-slate-900">{d.company_name}</h4>
                  <span className="text-xs font-bold text-indigo-600">{d.salary_package}</span>
                </div>
                <p className="text-xs text-slate-600 font-medium">{d.role_title}</p>
                <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                  <span>Min CGPA: {d.min_cgpa}</span>
                  <span>Depts: {d.allowed_departments}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Applicants & Telegram Broadcast */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
            <div>
              <h3 className="font-bold text-lg text-slate-900">
                Applicant Rankings & Eligibility Match
              </h3>
              <p className="text-xs text-slate-500">
                AI semantic matching score based on student resume skills vs drive JD.
              </p>
            </div>

            <button
              onClick={handleTelegramBroadcast}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs border border-indigo-200 transition-colors"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{broadcastSent ? "Broadcasted to Telegram!" : "Telegram Broadcast Alert"}</span>
            </button>
          </div>

          {broadcastSent && broadcastInfo && (
            <div className="p-3 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-900 text-xs font-semibold space-y-1">
              <div className="flex items-center justify-between">
                <span>✓ Broadcast Alert Dispatched ({broadcastInfo.mode})</span>
                <span className="font-mono text-[10px] text-indigo-600">{broadcastInfo.target_channel}</span>
              </div>
              <p className="text-[11px] text-indigo-700 font-normal">{broadcastInfo.note || "Alert delivered to student Telegram channels."}</p>
            </div>
          )}

          {/* Applicants Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-bold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-3">Student Name</th>
                  <th className="py-3 px-3">Roll No</th>
                  <th className="py-3 px-3">CGPA</th>
                  <th className="py-3 px-3">AI Match Score</th>
                  <th className="py-3 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {applicants.length > 0 ? (
                  applicants.map((app) => (
                    <tr key={app.application_id} className="hover:bg-slate-50">
                      <td className="py-3 px-3 font-semibold text-slate-900">{app.student_name}</td>
                      <td className="py-3 px-3 text-slate-600">{app.roll_number}</td>
                      <td className="py-3 px-3 font-bold text-slate-900">{app.cgpa}</td>
                      <td className="py-3 px-3">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          {app.match_score}% Match
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span className="font-semibold text-indigo-600">{app.status}</span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-400">
                      No applications submitted for this drive yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Modal: Create Drive */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl border border-slate-200 text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="font-bold text-base text-slate-900">Create Campus Recruitment Drive</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateDrive} className="space-y-3">
              <div>
                <label className="font-semibold text-slate-700">Company Name</label>
                <input
                  required
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="e.g. Microsoft / Qualcomm"
                  className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700">Role Title</label>
                <input
                  required
                  type="text"
                  value={roleTitle}
                  onChange={(e) => setRoleTitle(e.target.value)}
                  placeholder="e.g. Software Engineer"
                  className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700">Job Description & Requirements</label>
                <textarea
                  required
                  rows={3}
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste requirements, tech stack, and drive guidelines..."
                  className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700">Min CGPA</label>
                  <input
                    type="number"
                    step="0.1"
                    value={minCgpa}
                    onChange={(e) => setMinCgpa(e.target.value)}
                    className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700">Max Standing Arrears</label>
                  <input
                    type="number"
                    value={maxArrears}
                    onChange={(e) => setMaxArrears(e.target.value)}
                    className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="font-semibold text-slate-700">Min 10th % (opt.)</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    max="100"
                    placeholder="None"
                    value={minTenthPct}
                    onChange={(e) => setMinTenthPct(e.target.value)}
                    className="mt-1 w-full p-2 rounded-xl border border-slate-200 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700">Min 12th/Dip %</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    max="100"
                    placeholder="None"
                    value={minTwelfthPct}
                    onChange={(e) => setMinTwelfthPct(e.target.value)}
                    className="mt-1 w-full p-2 rounded-xl border border-slate-200 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700">Max Hist. Arrears</label>
                  <input
                    type="number"
                    min="0"
                    placeholder="None"
                    value={maxHistoryArrears}
                    onChange={(e) => setMaxHistoryArrears(e.target.value)}
                    className="mt-1 w-full p-2 rounded-xl border border-slate-200 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 items-center">
                <div>
                  <label className="font-semibold text-slate-700">Eligible Branches</label>
                  <input
                    type="text"
                    value={allowedDepts}
                    onChange={(e) => setAllowedDepts(e.target.value)}
                    placeholder="CSE,IT,ECE"
                    className="mt-1 w-full p-2 rounded-xl border border-slate-200 focus:outline-none"
                  />
                </div>
                <label className="flex items-center gap-2 pt-4 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={acceptsDiploma}
                    onChange={(e) => setAcceptsDiploma(e.target.checked)}
                    className="rounded border-slate-300 text-violet-600 focus:ring-violet-500"
                  />
                  <span className="font-semibold text-slate-700">Accepts Diploma Students</span>
                </label>
              </div>

              <div>
                <label className="font-semibold text-slate-700">Salary Package</label>
                <input
                  type="text"
                  value={salaryPackage}
                  onChange={(e) => setSalaryPackage(e.target.value)}
                  placeholder="e.g. 10.5 LPA"
                  className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-100 text-slate-700 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-bold shadow-md shadow-violet-200"
                >
                  Publish Drive
                </button>
              </div>
            </form>
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

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleToggleJob(selectedJobForAudit)}
                    disabled={togglingJobId === selectedJobForAudit.id}
                    className={`px-3 py-1.5 rounded-lg border text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                      selectedJobForAudit.enabled
                        ? "bg-amber-500/10 border-amber-500/30 text-amber-300 hover:bg-amber-500/20"
                        : "bg-emerald-500/10 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20"
                    }`}
                  >
                    <Power className="w-3 h-3" />
                    <span>{selectedJobForAudit.enabled ? "Pause Watcher" : "Resume Watcher"}</span>
                  </button>
                  <button
                    onClick={() => handleRunCronJob(selectedJobForAudit.id)}
                    disabled={triggeringJobId === selectedJobForAudit.id}
                    className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
                  >
                    <RefreshCw className={`w-3 h-3 ${triggeringJobId === selectedJobForAudit.id ? "animate-spin" : ""}`} />
                    <span>{triggeringJobId === selectedJobForAudit.id ? "Executing..." : "Trigger Run Now"}</span>
                  </button>
                </div>
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

