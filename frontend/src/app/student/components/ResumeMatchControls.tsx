"use client";

import React from "react";
import {
  Sparkles,
  FileText,
  RefreshCw,
  Layers,
  Target,
  Globe,
  Settings,
} from "lucide-react";

export type JobMatchMode = "both" | "based_on_resume" | "all";

export interface ResumeSummaryMeta {
  resume_id: string;
  filename: string;
  skills: string[];
  internships_count: number;
  projects_count: number;
  certifications_count: number;
  achievements_count: number;
}

interface ResumeMatchControlsProps {
  matchMode: JobMatchMode;
  onChangeMode: (mode: JobMatchMode) => void;
  hasResume: boolean;
  resumeSummary: ResumeSummaryMeta | null;
  counts: { personalized: number; others: number; total: number };
  loadingMatches: boolean;
  onRefreshMatches: () => void;
  onGoToSettings: () => void;
}

export default function ResumeMatchControls({
  matchMode,
  onChangeMode,
  hasResume,
  resumeSummary,
  counts,
  loadingMatches,
  onRefreshMatches,
  onGoToSettings,
}: ResumeMatchControlsProps) {
  return (
    <div className="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-sm space-y-3.5">
      {/* Top Row: Mode Switcher */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-violet-600" />
            <h3 className="font-bold text-sm text-slate-900">Resume-Based Job Matching</h3>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-violet-50 text-violet-700 border border-violet-200">
              Skills • Projects • Internships • Certs
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Switch fetching view between personalized resume matches, all active drives, or both grouped together.
          </p>
        </div>

        {/* 3-Mode Segmented Control */}
        <div className="inline-flex flex-wrap gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs font-bold">
          <button
            type="button"
            onClick={() => onChangeMode("both")}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition cursor-pointer ${
              matchMode === "both"
                ? "bg-white text-indigo-700 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Both (Default)</span>
          </button>

          <button
            type="button"
            onClick={() => onChangeMode("based_on_resume")}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition cursor-pointer ${
              matchMode === "based_on_resume"
                ? "bg-white text-violet-700 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Based on Resume</span>
          </button>

          <button
            type="button"
            onClick={() => onChangeMode("all")}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition cursor-pointer ${
              matchMode === "all"
                ? "bg-white text-slate-900 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>All Jobs</span>
          </button>
        </div>
      </div>

      {/* Bottom Row: Active Resume Context OR Prompt to Upload in Settings */}
      {hasResume && resumeSummary ? (
        <div className="p-3 rounded-xl bg-gradient-to-r from-violet-50/80 to-indigo-50/70 border border-violet-200/70 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-violet-950 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-violet-600" />
                <span>Active Resume: {resumeSummary.filename}</span>
              </span>
              {matchMode !== "all" && (
                <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-white text-indigo-700 border border-indigo-200">
                  {counts.personalized} Personalized Matches (≥30%)
                </span>
              )}
            </div>

            <div className="flex flex-wrap gap-1.5 text-[11px]">
              <span className="px-2 py-0.5 rounded-md bg-white border border-violet-200 text-slate-700 font-semibold">
                Skills: {resumeSummary.skills.length}
              </span>
              <span className="px-2 py-0.5 rounded-md bg-white border border-violet-200 text-slate-700 font-semibold">
                Projects: {resumeSummary.projects_count}
              </span>
              <span className="px-2 py-0.5 rounded-md bg-white border border-violet-200 text-slate-700 font-semibold">
                Internships: {resumeSummary.internships_count}
              </span>
              <span className="px-2 py-0.5 rounded-md bg-white border border-violet-200 text-slate-700 font-semibold">
                Certifications: {resumeSummary.certifications_count}
              </span>
              <span className="px-2 py-0.5 rounded-md bg-white border border-violet-200 text-slate-700 font-semibold">
                Achievements: {resumeSummary.achievements_count}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 flex-wrap">
            <button
              type="button"
              onClick={onRefreshMatches}
              disabled={loadingMatches}
              className="px-3.5 py-1.5 rounded-xl bg-white hover:bg-slate-50 border border-violet-200 text-violet-800 font-bold text-xs flex items-center gap-1.5 transition cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingMatches ? "animate-spin" : ""}`} />
              <span>{loadingMatches ? "Refreshing..." : "Refresh Matches"}</span>
            </button>
          </div>
        </div>
      ) : (
        matchMode !== "all" && (
          <div className="p-3.5 rounded-xl bg-amber-50/80 border border-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div className="space-y-0.5">
              <p className="font-bold text-amber-950 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-amber-600" />
                <span>No Resume Uploaded for Personalized Matching</span>
              </p>
              <p className="text-[11px] text-amber-800">
                Upload your resume in Settings → Academic &amp; Eligibility Data to unlock skill, project, and internship matching.
              </p>
            </div>
            <button
              type="button"
              onClick={onGoToSettings}
              className="px-3.5 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold inline-flex items-center justify-center gap-1.5 shrink-0 transition shadow-sm cursor-pointer"
            >
              <Settings className="w-3.5 h-3.5" />
              <span>Go to Settings</span>
            </button>
          </div>
        )
      )}
    </div>
  );
}
