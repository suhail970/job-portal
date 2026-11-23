"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken } from "@/lib/api";
import {
  Sparkles,
  GraduationCap,
  Building2,
  BrainCircuit,
  Mic,
  Code2,
  FileCheck2,
  ArrowRight,
  CheckCircle2,
  ShieldCheck,
  Bot,
  Zap
} from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [loggingIn, setLoggingIn] = useState(false);
  const [msg, setMsg] = useState("");

  const handleDemoLogin = async (email: string, role: string) => {
    setLoggingIn(true);
    setMsg(`Logging in as demo ${role}...`);
    try {
      const data = await api.login(email, role === "Student" ? "Student@123" : "Tpo@123");
      setToken(data.access_token);
      setMsg(`Success! Redirecting...`);
      if (role === "Student") {
        router.push("/student");
      } else {
        router.push("/tpo");
      }
    } catch (e: any) {
      setMsg(`Error: ${e.message}. Is backend running on :8000?`);
      setLoggingIn(false);
    }
  };

  return (
    <div className="space-y-16 py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Hero Section */}
      <section className="text-center space-y-6 pt-6 sm:pt-12">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs sm:text-sm font-semibold shadow-sm">
          <Zap className="w-4 h-4 text-indigo-600" />
          <span>100% Free Campus Placement Intelligence Platform</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-slate-900 max-w-4xl mx-auto leading-tight">
          Discover the right opportunity. Build skills.{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-violet-600">
            Prepare with AI.
          </span>
        </h1>

        <p className="text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
          From last-minute 1-day drive revision to AI voice mock interviews and sandboxed coding rounds.
          Built specifically for engineering colleges and ambitious students.
        </p>

        {/* Quick Demo Access Bar */}
        <div className="pt-4 flex flex-wrap items-center justify-center gap-4">
          <button
            onClick={() => handleDemoLogin("student@ceg.edu", "Student")}
            disabled={loggingIn}
            className="flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-lg shadow-indigo-200 transition-all active:scale-95 disabled:opacity-50"
          >
            <GraduationCap className="w-5 h-5" />
            <span>Launch Student AI Hub</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            onClick={() => handleDemoLogin("tpo@ceg.edu", "TPO")}
            disabled={loggingIn}
            className="flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-white hover:bg-slate-50 text-slate-800 font-semibold text-sm border border-slate-300 shadow-sm transition-all active:scale-95 disabled:opacity-50"
          >
            <Building2 className="w-5 h-5 text-violet-600" />
            <span>Open TPO Portal</span>
          </button>
        </div>

        {msg && (
          <p className="text-xs font-medium text-indigo-600 animate-pulse pt-2">
            {msg}
          </p>
        )}
      </section>

      {/* Feature Grid */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-8">
        {/* Card 1 */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition-shadow space-y-4">
          <div className="w-12 h-12 rounded-xl bg-violet-50 text-violet-600 flex items-center justify-center border border-violet-100">
            <BrainCircuit className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">Placement Intelligence Hub</h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            Drive announced tomorrow? Select 1-Day, 3-Day, or 7-Day sprint. AI decomposes company requirements into high-yield revision topics and top probable questions.
          </p>
          <ul className="text-xs text-slate-500 space-y-1.5 pt-2">
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>Timeframe-adaptive study checklists</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>High-frequency company question bank</span>
            </li>
          </ul>
        </div>

        {/* Card 2 */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition-shadow space-y-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100">
            <Mic className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">AI Voice Mock Interview</h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            AI speaks questions aloud. Student responds through the microphone. Browser Web Speech API provides sub-second evaluation of technical and communication depth.
          </p>
          <ul className="text-xs text-slate-500 space-y-1.5 pt-2">
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>Zero-latency browser audio processing</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>Objective 1-10 scoring and feedback</span>
            </li>
          </ul>
        </div>

        {/* Card 3 */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm hover:shadow-md transition-shadow space-y-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
            <Code2 className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-slate-900">Placement Simulation Sandbox</h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            Sandboxed coding assessment runner powered by Piston API. Multi-language support (Python, Java, C++, JS) with execution time and test-case verification.
          </p>
          <ul className="text-xs text-slate-500 space-y-1.5 pt-2">
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>Real-time test case verification</span>
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>Execution safety & zero Docker requirement</span>
            </li>
          </ul>
        </div>
      </section>

      {/* Institutional Isolation Callout */}
      <section className="bg-slate-900 rounded-2xl p-8 sm:p-10 text-white flex flex-col md:flex-row items-center justify-between gap-8 shadow-xl">
        <div className="space-y-3 max-w-xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800 text-indigo-400 text-xs font-semibold border border-slate-700">
            <ShieldCheck className="w-4 h-4" />
            <span>Strict College-Level Multi-Tenancy</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Institutional Data Privacy by Design
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            Every college operates in an isolated environment. Student profiles, placement drive criteria, and conversion analytics are physically isolated with PostgreSQL Row-Level Security.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
          <Link
            href="/student"
            className="text-center px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold text-sm transition-colors"
          >
            Student Experience
          </Link>
          <Link
            href="/tpo"
            className="text-center px-5 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 font-semibold text-sm border border-slate-700 transition-colors"
          >
            TPO Dashboard
          </Link>
        </div>
      </section>
    </div>
  );
}

