import React from 'react';
import {
  LayoutDashboard,
  ShieldCheck,
  FileSignature,
  Workflow,
  FlaskConical,
  RotateCcw,
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'overview', label: 'Treasury Overview', icon: LayoutDashboard },
  { id: 'firewall', label: 'Spend Firewall', icon: ShieldCheck, badge: 'LIVE' },
  { id: 'mandates', label: 'AP2 Mandates & Ledger', icon: FileSignature },
  { id: 'integrations', label: 'System & Integrations', icon: Workflow },
  { id: 'benchmarks', label: 'Red-Team & Lab', icon: FlaskConical },
];

export default function SidebarNav({
  activeTab,
  setActiveTab,
  vault,
  health,
  onReset,
  resetting,
}) {
  const isLiveGemini = health?.gemini_mode === 'live_gemini';

  return (
    <aside className="lg:w-64 lg:shrink-0 lg:sticky lg:top-0 lg:h-screen bg-white border-b lg:border-b-0 lg:border-r border-[#E2EBE5] flex flex-col justify-between">
      <div>
        {/* Brand Header */}
        <div className="px-5 py-5 border-b border-[#E2EBE5] flex items-center justify-between lg:justify-start gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#0D261C] flex items-center justify-center shadow-sm">
              <svg viewBox="0 0 24 24" className="w-4 h-4 text-[#6EE7B7]" fill="none" stroke="currentColor" strokeWidth="2.2">
                <path d="M12 3l7 3v5c0 5-3 8.5-7 10-4-1.5-7-5-7-10V6l7-3z" />
                <path d="M9.5 12l2 2 3.5-4" />
              </svg>
            </div>
            <div>
              <div className="text-base font-extrabold tracking-tight text-[#0B1F16] leading-none">
                Numen
              </div>
              <div className="font-mono text-[10px] font-medium text-[#526B5D] mt-0.5">
                AGENT TREASURY OS
              </div>
            </div>
          </div>

          <button
            onClick={onReset}
            disabled={resetting}
            className="lg:hidden inline-flex items-center gap-1.5 rounded-lg border border-[#E2EBE5] bg-[#F7FAF8] px-2.5 py-1.5 text-xs font-semibold text-[#0B1F16]"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin' : ''}`} />
            Reset
          </button>
        </div>

        {/* Vault Pill */}
        <div className="px-4 pt-4 hidden lg:block">
          <div className="rounded-xl bg-[#F7FAF8] border border-[#E2EBE5] p-3.5">
            <div className="text-[11px] font-medium text-[#526B5D]">Operating Vault</div>
            <div className="text-lg font-extrabold text-[#0B1F16] tabular-nums mt-0.5">
              ₹{(vault?.balance_inr ?? 1840000).toLocaleString('en-IN')}
            </div>
            <div className="flex items-center gap-1.5 mt-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#059669]" />
              <span className="font-mono text-[10px] font-medium text-[#059669]">
                SQLITE WAL • SETTLEMENT READY
              </span>
            </div>
          </div>
        </div>

        {/* Route Links */}
        <nav className="px-3 py-3 flex lg:flex-col gap-1 overflow-x-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`shrink-0 flex items-center justify-between gap-2.5 rounded-xl px-3 py-2.5 text-[13px] font-semibold transition-colors ${
                  active
                    ? 'bg-[#ECFDF5] text-[#0B1F16] border border-[#A7F3D0]'
                    : 'text-[#526B5D] hover:bg-[#F7FAF8] hover:text-[#0B1F16] border border-transparent'
                }`}
              >
                <span className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${active ? 'text-[#059669]' : 'text-[#849B8E]'}`} />
                  {item.label}
                </span>
                {item.badge && (
                  <span className="hidden lg:inline-block rounded-md bg-white border border-[#E2EBE5] px-1.5 py-0.5 font-mono text-[9px] font-bold text-[#059669]">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Engine Status & Reset */}
      <div className="hidden lg:block p-4 border-t border-[#E2EBE5] space-y-2.5">
        <div className="rounded-xl bg-[#F7FAF8] border border-[#E2EBE5] px-3 py-2.5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-[#526B5D]">Reasoning Engine</span>
            <span className="w-2 h-2 rounded-full bg-[#059669]" />
          </div>
          <div className="font-mono text-[10.5px] font-semibold text-[#0B1F16]">
            {isLiveGemini ? 'Gemini 2.5 Live' : 'Deterministic Engine'}
          </div>
          <div className="text-[10px] text-[#849B8E]">
            {isLiveGemini ? 'google-genai SDK active' : 'Zero-key reproducible mode'}
          </div>
        </div>

        <button
          onClick={onReset}
          disabled={resetting}
          className="w-full inline-flex items-center justify-center gap-1.5 rounded-xl border border-[#E2EBE5] bg-white hover:bg-[#F7FAF8] py-2 text-xs font-semibold text-[#0B1F16] transition"
        >
          <RotateCcw className={`w-3.5 h-3.5 text-[#526B5D] ${resetting ? 'animate-spin' : ''}`} />
          {resetting ? 'Resetting Vault...' : 'Reset Demo Vault'}
        </button>
      </div>
    </aside>
  );
}
