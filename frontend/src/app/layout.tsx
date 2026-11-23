import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";
import { Sparkles, GraduationCap, Building2, ShieldCheck, Terminal } from "lucide-react";

export const metadata: Metadata = {
  title: "SkillBridge AI — Career Guidance & Placement Preparation",
  description: "100% Free AI-Powered Job Discovery, Placement Preparation and Career Ecosystem",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
        {/* Bright Auditorium Header */}
        <header className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-slate-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-md shadow-indigo-200">
                <Sparkles className="w-5 h-5 transition-transform group-hover:scale-110" />
              </div>
              <div>
                <span className="font-bold text-lg tracking-tight text-slate-900">SkillBridge<span className="text-indigo-600"> AI</span></span>
                <span className="hidden sm:inline-block ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">100% Free</span>
              </div>
            </Link>

            <nav className="flex items-center gap-1 sm:gap-4 text-sm font-medium">
              <Link
                href="/student"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-slate-700 hover:text-indigo-600 hover:bg-slate-100 transition-colors"
              >
                <GraduationCap className="w-4 h-4 text-indigo-500" />
                <span>Student Hub</span>
              </Link>

              <Link
                href="/tpo"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-slate-700 hover:text-indigo-600 hover:bg-slate-100 transition-colors"
              >
                <Building2 className="w-4 h-4 text-violet-500" />
                <span>TPO Portal</span>
              </Link>

              <div className="h-4 w-px bg-slate-200 mx-1 hidden sm:block"></div>

              <span className="hidden md:flex items-center gap-1 text-xs text-emerald-600 font-semibold bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                Backend Ready
              </span>
            </nav>
          </div>
        </header>

        {/* Main Workspace */}
        <main className="flex-1">{children}</main>

        {/* Footer */}
        <footer className="bg-white border-t border-slate-200 py-6 mt-12 text-center text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p>SkillBridge AI — Production-Grade Multi-Tenant College Career Ecosystem</p>
            <p className="flex items-center gap-2">
              <span>Anna University CEG Pilot</span> • <span>FastAPI + Next.js + Gemini Flash</span>
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}

