"use client";

import React from "react";
import {
  FileText,
  Upload,
  RefreshCw,
  CheckCircle2,
  Save,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
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

  // Persistence & Summary State
  savingSettings: boolean;
  onSaveProfile: () => void;
  eligibilityData: EligibilityDashboardData | null;
  loadingEligibility: boolean;
  isPreviewMode: boolean;
  onViewJobs?: () => void;
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
  onViewJobs,
}: EligibilityDashboardCardProps) {
  const standingNum = parseInt(arrearsInput || "0", 10);
  const historyNum = parseInt(historyArrearsInput || "0", 10);
  const arrearsInvalid =
    Number.isFinite(standingNum) && Number.isFinite(historyNum) && historyNum < standingNum;

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
                Academic &amp; Eligibility Data
              </h3>
              <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                Rule-Based Profile
              </span>
              {isPreviewMode && (
                <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                  Unsaved Draft
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Upload your PDF resume for verification and maintain your academic credentials &amp; career targets.
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

      {/* Compact Eligibility Summary KPI Strip (Detailed Job List lives on Placement Drives Tab) */}
      <div className="rounded-2xl bg-slate-50 border border-slate-200/80 p-4 space-y-3">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-800 uppercase tracking-wider">
            <TrendingUp className="w-4 h-4 text-indigo-600" />
            <span>Eligibility Readiness Summary</span>
            {loadingEligibility && (
              <span className="inline-flex items-center gap-1 text-[11px] text-indigo-600 font-semibold normal-case tracking-normal ml-2">
                <RefreshCw className="w-3 h-3 animate-spin" />
                Updating...
              </span>
            )}
          </div>
          {onViewJobs && (
            <button
              type="button"
              onClick={onViewJobs}
              className="text-xs font-bold text-indigo-600 hover:text-indigo-800 inline-flex items-center gap-1 cursor-pointer"
            >
              <span>Filter Jobs by Eligibility</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="bg-white rounded-xl p-3 border border-slate-200">
            <span className="text-[11px] font-semibold text-slate-500 block">Total Active Drives</span>
            <span className="text-xl font-extrabold text-slate-900 mt-0.5 block">
              {eligibilityData?.total_drives ?? 0}
            </span>
          </div>

          <div className="bg-white rounded-xl p-3 border border-emerald-200">
            <span className="text-[11px] font-semibold text-emerald-700 block">Eligible Drives</span>
            <span className="text-xl font-extrabold text-emerald-600 mt-0.5 block">
              {eligibilityData?.eligible_count ?? 0}
            </span>
          </div>

          <div className="bg-white rounded-xl p-3 border border-indigo-200">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-indigo-700">Eligibility Rate</span>
              <span className="text-xs font-extrabold text-indigo-700">{pct}%</span>
            </div>
            <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden mt-2">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  pct >= 75 ? "bg-emerald-500" : pct >= 45 ? "bg-indigo-500" : "bg-amber-500"
                }`}
                style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
              />
            </div>
          </div>

          <div className="bg-white rounded-xl p-3 border border-violet-200">
            <span className="text-[11px] font-semibold text-violet-700 block">Dream Target Matches</span>
            <span className="text-xl font-extrabold text-violet-600 mt-0.5 block">
              {eligibilityData?.target_eligible_count ?? 0}
              <span className="text-xs font-semibold text-slate-400 ml-1">
                / {eligibilityData?.target_matches_count ?? 0}
              </span>
            </span>
          </div>
        </div>
      </div>

      {/* Upload Resume PDF to Auto-Fill & Verify */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-50 to-violet-50 border border-indigo-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="space-y-0.5">
          <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-950">
            <FileText className="w-4 h-4 text-indigo-600" />
            <span>Upload Resume (PDF) — Auto-Extract Academic &amp; Skill Profile</span>
          </div>
          <p className="text-[11px] text-indigo-700">
            Extracts 10th %, HSC/Diploma %, CGPA, batch, branch, skills, projects, internships &amp; links for review before saving.
          </p>
        </div>
        <label
          htmlFor="academic-resume-upload"
          className={`px-4 py-2 rounded-xl text-xs font-bold inline-flex items-center justify-center gap-1.5 shrink-0 transition shadow-sm cursor-pointer ${
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
              ATS Score: {Math.round(resumeExtractPreview.ats_score || 0)}/100
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

      {/* Clean Responsive Academic & Career Matrix Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
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

        <div>
          <label className="font-semibold text-slate-700">Min Expected CTC (LPA)</label>
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

        <div>
          <label className="font-semibold text-slate-700">Target Dream Recruiters</label>
          <input
            type="text"
            value={targetCompanies}
            onChange={(e) => setTargetCompanies(e.target.value)}
            placeholder="e.g. Zoho, Amazon, TCS, Freshworks"
            className="mt-1 w-full p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      {arrearsInvalid && (
        <div className="p-2.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold flex items-center gap-1.5">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>History of arrears cannot be less than current standing arrears.</span>
        </div>
      )}
    </div>
  );
}
