import React from 'react';
import { RotateCcw, ShieldCheck, Sparkles, Terminal, Activity, FileCheck2 } from 'lucide-react';

const TABS = [
  { id: 'arena', label: '01 Live Spend Arena', icon: Sparkles },
  { id: 'lab', label: '02 Custom Attack Lab', icon: Terminal },
  { id: 'ledger', label: '03 AP2 Mandates & Ledger', icon: FileCheck2 },
  { id: 'benchmarks', label: '04 Benchmarks & MCP', icon: Activity },
];

export default function TopNav({ activeTab, setActiveTab, health, onReset, resetting }) {
  return (
    <header className="sticky top-3 z-30 mx-auto max-w-[1440px] px-4">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-full bg-white/90 backdrop-blur-md border border-[#CDE4C8] px-4 py-2.5 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-[#8CE563] border border-[#15803D] px-3.5 py-1 text-sm font-black tracking-tight text-[#0D2616]">
            <ShieldCheck className="w-4 h-4" />
            Numen
          </span>
          <span className="hidden md:inline font-mono text-xs font-semibold text-[#4A6653]">
            AP2-NATIVE AGENT NEOBANK
          </span>
        </div>

        <nav className="flex flex-wrap items-center gap-1.5">
          {TABS.map((t) => {
            const Icon = t.icon;
            const active = activeTab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-bold transition ${
                  active
                    ? 'bg-[#8CE563] text-[#0D2616] border border-[#15803D] shadow-sm'
                    : 'text-[#4A6653] hover:bg-[#E8F8E2] hover:text-[#0D2616] border border-transparent'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {t.label}
              </button>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full bg-[#E8F8E2] border border-[#CDE4C8] px-3 py-1 font-mono text-[11px] font-bold text-[#15803D]">
            <span className="w-2 h-2 rounded-full bg-[#15803D]" />
            {health?.gemini_mode === 'live_gemini' ? 'GEMINI LIVE' : 'OFFLINE DETERMINISTIC'}
          </span>
          <button
            onClick={onReset}
            disabled={resetting}
            className="inline-flex items-center gap-1.5 rounded-full bg-[#F6FBF5] hover:bg-[#E8F8E2] border border-[#CDE4C8] px-3 py-1.5 text-xs font-bold text-[#0D2616] transition"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin' : ''}`} />
            Reset Demo
          </button>
        </div>
      </div>
    </header>
  );
}
