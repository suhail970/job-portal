"use client";

import React, { useState, useMemo } from "react";
import {
  Award,
  FileText,
  Upload,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Save,
  Search,
  Sparkles,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  Building2,
  MapPin,
} from "lucide-react";

export interface EligibilityDriveEvaluation {
  drive_id: string;
  company_name: string;
  role_title: string;
  location?: string;
  salary_package?: string;
  drive_date?: string;
  is_eligible: boolean;
  status_label: "Eligible" | "Not Eligible";
  reasons: string[];
  passed_checks: string[];
  package_goal_match: boolean | null;
  package_goal_label: string | null;
  is_target_company: boolean;
  criteria: {
    min_cgpa: number;
    max_arrears: number;
    max_history_arrears: number | null;
    min_tenth_percentage: number | null;
    min_twelfth_percentage: number | null;
    allowed_departments: string;
    accepts_diploma: boolean;
  };
}

export interface EligibilityDashboardData {
  total_drives: number;
  eligible_count: number;
  not_eligible_count: number;
  eligibility_percentage: number;
  eligible_companies: string[];
  target_matches_count: number;
  target_eligible_count: number;
  results: EligibilityDriveEvaluation[];
}

interface EligibilityDashboardCardProps {
  // Academic Inputs
  tenthInput: string;
  setTenthInput: (val: string) => void;
  qualTypeInput: "HSC" | "DIPLOMA";
  setQualTypeInput: (val: "HSC" | "DIPLOMA") => void;
  twelfthInput: string;
  setTwelfthInput: (val: string) => void;
  cgpaInput: string;
  setCgpaInput: (val: string) => void;
  arrearsInput: string;
  setArrearsInput: (val: string) => void;
  historyArrearsInput: string;
  setHistoryArrearsInput: (val: string) => void;
  graduationYearInput: string;
  setGraduationYearInput: (val: string) => void;
  departmentCodeInput: string;
  setDepartmentCodeInput: (val: string) => void;

  // Contact & Preferences
  applyPhone: string;
  setApplyPhone: (val: string) => void;
  applyGithub: string;
  setApplyGithub: (val: string) => void;
  applyLinkedin: string;
  setApplyLinkedin: (val: string) => void;
  targetCompanies: string;
  setTargetCompanies: (val: string) => void;
  targetMinCtc: string;
  setTargetMinCtc: (val: string) => void;

  // Resume Extraction State
  uploadingResume: boolean;
  onResumeUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  resumeExtractPreview: any;
  onDismissResumePreview: () => void;

  // Persistence & Preview State
  savingSettings: boolean;
  onSaveProfile: () => void;
  eligibilityData: EligibilityDashboardData | null;
  loadingEligibility: boolean;
  isPreviewMode: boolean;
}

export default function EligibilityDashboardCard({
  tenthInput,
  setTenthInput,
  qualTypeInput,
  setQualTypeInput,
  twelfthInput,
  setTwelfthInput,
  cgpaInput,
  setCgpaInput,
  arrearsInput,
  setArrearsInput,
  historyArrearsInput,
  setHistoryArrearsInput,
  graduationYearInput,
  setGraduationYearInput,
  departmentCodeInput,
  setDepartmentCodeInput,
  applyPhone,
  setApplyPhone,
  applyGithub,
  setApplyGithub,
  applyLinkedin,
  setApplyLinkedin,
  targetCompanies,
  setTargetCompanies,
  targetMinCtc,
  setTargetMinCtc,
  uploadingResume,
  onResumeUpload,
  resumeExtractPreview,
  onDismissResumePreview,
  savingSettings,
  onSaveProfile,
  eligibilityData,
  loadingEligibility,
  isPreviewMode,
}: EligibilityDashboardCardProps) {
  const [filterMode, setFilterMode] = useState<"all" | "eligible" | "not_eligible" | "targets">("all");
  const [companySearch, setCompanySearch] = useState("");

  // Client-side arrears sanity notice (backend still validates strictly)
  const standingNum = parseInt(arrearsInput || "0", 10);
  const historyNum = parseInt(historyArrearsInput || "0", 10);
  const arrearsInvalid =
    Number.isFinite(standingNum) && Number.isFinite(historyNum) && historyNum < standingNum;

  const filteredResults = useMemo(() => {
    const items = eligibilityData?.results || [];
    const q = companySearch.trim().toLowerCase();
    return items.filter((item) => {
      if (filterMode === "eligible" && !item.is_eligible) return false;
      if (filterMode === "not_eligible" && item.is_eligible) return false;
      if (filterMode === "targets" && !item.is_target_company) return false;
      if (
        q &&
        !item.company_name.toLowerCase().includes(q) &&
        !item.role_title.toLowerCase().includes(q)
      ) {
        return false;
      }
      return true;
    });
  }, [eligibilityData, filterMode, companySearch]);

  const pct = eligibilityData?.eligibility_percentage ?? 0;

  return (
    <div className="md:col-span-2 bg-white rounded-2xl p-5 sm:p-6 border border-slate-200 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-start sm:items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-bold text-base text-slate-900">
                Smart Placement Eligibility System
              </h3>
              <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                Rule-Based Engine
              </span>
              {isPreviewMode && (
                <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                  Live Unsaved Preview
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Update your complete academic profile, upload your resume for verification, and view real-time drive eligibility.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onSaveProfile}
          disabled={savingSettings || arrearsInvalid}
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-sm shadow-indigo-200 transition-all disabled:opacity-50 cursor-pointer shrink-0"
        >
          <Save className="w-3.5 h-3.5" />
          <span>{savingSettings ? "Saving Profile..." : "Save Academic & Target Profile"}</span>
        </button>
      </div>

      {/* Live Eligibility Dashboard KPIs */}
      <div className="rounded-2xl bg-slate-50 border border-slate-200/80 p-4 space-y-4">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-800 uppercase tracking-wider">
            <TrendingUp className="w-4 h-4 text-indigo-600" />
            <span>Real-Time Campus Eligibility Dashboard</span>
          </div>
          {loadingEligibility && (
            <span className="inline-flex items-center gap-1.5 text-[11px] text-indigo-600 font-semibold">
              <RefreshCw className="w-3 h-3 animate-spin" />
              Evaluating drive rules...
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="bg-white rounded-xl p-3.5 border border-slate-200 shadow-2xs">
            <span className="text-[11px] font-semibold text-slate-500 block">Total Active Drives</span>
            <span className="text-2xl font-extrabold text-slate-900 mt-1 block">
              {eligibilityData?.total_drives ?? 0}
            </span>
          </div>

          <div className="bg-white rounded-xl p-3.5 border border-emerald-200 shadow-2xs">
            <span className="text-[11px] font-semibold text-emerald-700 block">Eligible Drives</span>
            <span className="text-2xl font-extrabold text-emerald-600 mt-1 block">
              {eligibilityData?.eligible_count ?? 0}
            </span>
          </div>

          <div className="bg-white rounded-xl p-3.5 border border-indigo-200 shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-indigo-700">Eligibility Rate</span>
              <span className="text-xs font-extrabold text-indigo-700">{pct}%</span>
            </div>
            <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden mt-2.5">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  pct >= 75 ? "bg-emerald-500" : pct >= 45 ? "bg-indigo-500" : "bg-amber-500"
                }`}
                style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
              />
            </div>
            <span className="text-[10px] text-slate-400 mt-1.5 block">
              {eligibilityData?.not_eligible_count ?? 0} drives restricted by criteria
            </span>
          </div>

          <div className="bg-white rounded-xl p-3.5 border border-violet-200 shadow-2xs">
            <span className="text-[11px] font-semibold text-violet-700 block">Dream Target Matches</span>
            <span className="text-2xl font-extrabold text-violet-600 mt-1 block">
              {eligibilityData?.target_eligible_count ?? 0}
              <span className="text-xs font-semibold text-slate-400 ml-1">
                / {eligibilityData?.target_matches_count ?? 0}
              </span>
            </span>
          </div>
        </div>

        {/* Eligible Companies Pills */}
        {eligibilityData && eligibilityData.eligible_companies.length > 0 && (
          <div className="pt-1">
            <span className="text-[11px] font-semibold text-slate-600 mr-2">
              Qualified Companies ({eligibilityData.eligible_companies.length}):
            </span>
            <div className="inline-flex flex-wrap gap-1.5 mt-1">
              {eligibilityData.eligible_companies.slice(0, 14).map((comp) => (
                <span
                  key={comp}
                  className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200"
                >
                  ✓ {comp}
                </span>
              ))}
              {eligibilityData.eligible_companies.length > 14 && (
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600">
                  +{eligibilityData.eligible_companies.length - 14} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Main Split Grid: Academic Form (Left) + Company Breakdown (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Academic Form + Resume Extractor */}
        <div className="lg:col-span-5 space-y-4">
          {/* Upload Resume PDF to Auto-Fill */}
          <div className="p-3.5 rounded-xl bg-gradient-to-r from-indigo-50 to-violet-50 border border-indigo-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-0.5">
              <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-950">
                <FileText className="w-4 h-4 text-indigo-600" />
                <span>Extract from Resume (PDF)</span>
              </div>
              <p className="text-[11px] text-indigo-700">
                Extracts 10th, HSC/Diploma %, CGPA, batch, branch &amp; links for review before saving.
              </p>
            </div>
            <label
              htmlFor="academic-resume-upload"
              className={`px-3.5 py-2 rounded-xl text-xs font-bold inline-flex items-center justify-center gap-1.5 shrink-0 transition shadow-sm cursor-pointer ${
                uploadingResume
                  ? "bg-indigo-300 text-white cursor-wait"
                  : "bg-indigo-600 hover:bg-indigo-700 text-white"
              }`}
            >
              {uploadingResume ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Reading PDF...</span>
                </>
              ) : (
                <>
                  <Upload className="w-3.5 h-3.5" />
                  <span>Upload PDF</span>
                </>
              )}
              <input
                id="academic-resume-upload"
                type="file"
                accept=".pdf,application/pdf"
                disabled={uploadingResume}
                onChange={onResumeUpload}
                className="hidden"
              />
            </label>
          </div>

          {/* Extracted Data Review Banner */}
          {resumeExtractPreview && (
            <div className="p-3.5 rounded-xl bg-emerald-50/80 border border-emerald-200 space-y-2 text-xs">
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <span className="font-bold text-emerald-900 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Verify Extracted Data ({resumeExtractPreview.filename})</span>
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-white text-emerald-700 border border-emerald-200">
                  ATS: {Math.round(resumeExtractPreview.ats_score || 0)}/100
                </span>
              </div>
              {resumeExtractPreview.foundFields?.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {resumeExtractPreview.foundFields.map((tag: string, i: number) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded-md bg-white border border-emerald-200 text-emerald-800 text-[11px] font-semibold"
                    >
                      ✓ {tag}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-[11px] text-amber-800">
                  No academic fields were matched automatically in this PDF.
                </p>
              )}
              {resumeExtractPreview.warnings?.length > 0 && (
                <ul className="space-y-0.5 text-[11px] text-amber-800 list-disc list-inside">
                  {resumeExtractPreview.warnings.map((w: string, i: number) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              )}
              <div className="pt-1 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={onDismissResumePreview}
                  className="px-2.5 py-1 rounded-lg bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 font-semibold text-[11px] cursor-pointer"
                >
                  Dismiss
                </button>
                <button
                  type="button"
                  onClick={onSaveProfile}
                  disabled={savingSettings || arrearsInvalid}
                  className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[11px] flex items-center gap-1 cursor-pointer disabled:opacity-50"
                >
                  <Save className="w-3 h-3" />
                  <span>{savingSettings ? "Saving..." : "Confirm & Save Academic Data"}</span>
                </button>
              </div>
            </div>
          )}

          {/* Academic Inputs Matrix */}
          <div className="space-y-3 text-xs">
            {/* Row 1: 10th % + HSC/Diploma Toggle */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="font-semibold text-slate-700">10th Standard (%)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  placeholder="e.g. 89.4"
                  value={tenthInput}
                  onChange={(e) => setTenthInput(e.target.value)}
                  className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-bold"
                />
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <label className="font-semibold text-slate-700">
                    {qualTypeInput === "DIPLOMA" ? "Diploma (%)" : "12th HSC (%)"}
                  </label>
                  {/* HSC / Diploma Segmented Toggle */}
                  <div className="inline-flex rounded-lg bg-slate-100 p-0.5 border border-slate-200">
                    <button
                      type="button"
                      onClick={() => setQualTypeInput("HSC")}
                      className={`px-2 py-0.5 text-[10px] font-bold rounded-md transition cursor-pointer ${
                        qualTypeInput === "HSC"
                          ? "bg-indigo-600 text-white shadow-2xs"
                          : "text-slate-600 hover:text-slate-900"
                      }`}
                    >
                      HSC
                    </button>
                    <button
                      type="button"
                      onClick={() => setQualTypeInput("DIPLOMA")}
                      className={`px-2 py-0.5 text-[10px] font-bold rounded-md transition cursor-pointer ${
                        qualTypeInput === "DIPLOMA"
                          ? "bg-indigo-600 text-white shadow-2xs"
                          : "text-slate-600 hover:text-slate-900"
                      }`}
                    >
                      Diploma
                    </button>
                  </div>
                </div>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  placeholder={qualTypeInput === "DIPLOMA" ? "e.g. 88.0" : "e.g. 91.2"}
                  value={twelfthInput}
                  onChange={(e) => setTwelfthInput(e.target.value)}
                  className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-bold"
                />
              </div>
            </div>

            {/* Row 2: CGPA + Department */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-semibold text-slate-700">Current CGPA (0–10)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="10"
                  value={cgpaInput}
                  onChange={(e) => setCgpaInput(e.target.value)}
                  className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-bold"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700">Department / Branch</label>
                <select
                  value={departmentCodeInput}
                  onChange={(e) => setDepartmentCodeInput(e.target.value)}
                  className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-bold bg-white"
                >
                  {["CSE", "IT", "ECE", "EEE", "MECH", "CIVIL", "AIDS", "AIML"].map((dept) => (
                    <option key={dept} value={dept}>
                      {dept}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Row 3: Standing Arrears + History of Arrears */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-semibold text-slate-700">Standing Arrears</label>
                <input
                  type="number"
                  min="0"
                  max="50"
                  value={arrearsInput}
                  onChange={(e) => setArrearsInput(e.target.value)}
                  className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-bold"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700">History of Arrears</label>
                <input
                  type="number"
                  min="0"
                  max="50"
                  value={historyArrearsInput}
                  onChange={(e) => setHistoryArrearsInput(e.target.value)}
                  className={`mt-1 w-full p-2.5 rounded-xl border focus:outline-none focus:ring-2 font-bold ${
                    arrearsInvalid
                      ? "border-rose-400 bg-rose-50 focus:ring-rose-500 text-rose-800"
                      : "border-slate-200 focus:ring-indigo-500"
                  }`}
                />
              </div>
            </div>

            {arrearsInvalid && (
              <div className="p-2.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-[11px] font-semibold flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>History of arrears cannot be less than current standing arrears.</span>
              </div>
            )}

            {/* Row 4: Graduation Year + Phone */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-semibold text-slate-700">Graduation Batch</label>
                <input
                  type="number"
                  min="2020"
                  max="2035"
                  value={graduationYearInput}
                  onChange={(e) => setGraduationYearInput(e.target.value)}
                  className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-bold"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700">Phone Number</label>
                <input
                  type="text"
                  value={applyPhone}
                  onChange={(e) => setApplyPhone(e.target.value)}
                  placeholder="+91 98765 43210"
                  className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            {/* Row 5: GitHub + LinkedIn */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="font-semibold text-slate-700">GitHub URL</label>
                <input
                  type="text"
                  value={applyGithub}
                  onChange={(e) => setApplyGithub(e.target.value)}
                  placeholder="https://github.com/..."
                  className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700">LinkedIn URL</label>
                <input
                  type="text"
                  value={applyLinkedin}
                  onChange={(e) => setApplyLinkedin(e.target.value)}
                  placeholder="https://linkedin.com/in/..."
                  className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            {/* Row 6: Target Dream Recruiters + Min Expected CTC */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2">
                <label className="font-semibold text-slate-700">Target Dream Recruiters</label>
                <input
                  type="text"
                  value={targetCompanies}
                  onChange={(e) => setTargetCompanies(e.target.value)}
                  placeholder="e.g. Zoho, Amazon, TCS, Freshworks"
                  className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700">Min CTC Goal (LPA)</label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  max="500"
                  value={targetMinCtc}
                  onChange={(e) => setTargetMinCtc(e.target.value)}
                  placeholder="e.g. 8.0"
                  className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-bold"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Company-by-Company Real-Time Eligibility Matrix */}
        <div className="lg:col-span-7 flex flex-col space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-1.5 flex-wrap">
              {[
                { key: "all", label: `All (${eligibilityData?.total_drives ?? 0})` },
                { key: "eligible", label: `Eligible (${eligibilityData?.eligible_count ?? 0})` },
                { key: "not_eligible", label: `Not Eligible (${eligibilityData?.not_eligible_count ?? 0})` },
                { key: "targets", label: `Dream Targets (${eligibilityData?.target_matches_count ?? 0})` },
              ].map((t) => (
                <button
                  key={t.key}
                  type="button"
                  onClick={() => setFilterMode(t.key as any)}
                  className={`px-3 py-1.5 rounded-lg text-[11px] font-bold transition cursor-pointer ${
                    filterMode === t.key
                      ? "bg-indigo-600 text-white shadow-2xs"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                value={companySearch}
                onChange={(e) => setCompanySearch(e.target.value)}
                placeholder="Filter companies..."
                className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 w-full sm:w-44"
              />
            </div>
          </div>

          <div className="space-y-2.5 max-h-[540px] overflow-y-auto pr-1">
            {filteredResults.length === 0 ? (
              <div className="p-8 text-center rounded-xl border border-dashed border-slate-200 text-slate-400 text-xs">
                No placement drives match the current filter.
              </div>
            ) : (
              filteredResults.map((item) => (
                <div
                  key={item.drive_id}
                  className={`p-3.5 rounded-xl border transition-all space-y-2 ${
                    item.is_eligible
                      ? "bg-white border-emerald-200/80 hover:border-emerald-300"
                      : "bg-slate-50/70 border-rose-200/70 hover:border-rose-300"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 flex-wrap">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-sm text-slate-900 flex items-center gap-1.5">
                          <Building2 className="w-3.5 h-3.5 text-slate-400" />
                          {item.company_name}
                        </span>
                        {item.is_target_company && (
                          <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-violet-100 text-violet-800 border border-violet-200">
                            <Sparkles className="w-2.5 h-2.5" />
                            Dream Target
                          </span>
                        )}
                        {item.package_goal_match !== null && item.package_goal_label && (
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                              item.package_goal_match
                                ? "bg-indigo-50 text-indigo-700 border-indigo-200"
                                : "bg-amber-50 text-amber-800 border-amber-200"
                            }`}
                          >
                            {item.package_goal_label}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-600 font-medium mt-0.5">
                        {item.role_title}
                        {item.salary_package ? ` • ${item.salary_package}` : ""}
                      </p>
                      {item.location && (
                        <p className="text-[11px] text-slate-400 flex items-center gap-1 mt-0.5">
                          <MapPin className="w-3 h-3" />
                          <span>{item.location}</span>
                        </p>
                      )}
                    </div>

                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-extrabold shrink-0 border ${
                        item.is_eligible
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : "bg-rose-50 text-rose-700 border-rose-200"
                      }`}
                    >
                      {item.is_eligible ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Eligible</span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Not Eligible</span>
                        </>
                      )}
                    </span>
                  </div>

                  {/* Rule Reasons / Passed Checks */}
                  {!item.is_eligible && item.reasons.length > 0 && (
                    <div className="p-2.5 rounded-lg bg-rose-50/80 border border-rose-200/70 space-y-1">
                      {item.reasons.map((reason, idx) => (
                        <p key={idx} className="text-[11px] font-semibold text-rose-800 flex items-start gap-1.5">
                          <XCircle className="w-3.5 h-3.5 text-rose-600 shrink-0 mt-0.5" />
                          <span>{reason}</span>
                        </p>
                      ))}
                    </div>
                  )}

                  {item.passed_checks.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {item.passed_checks.map((chk, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-emerald-50/70 text-emerald-800 border border-emerald-200/70"
                        >
                          ✓ {chk}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

