import React from 'react';
import {
  ArrowRight,
  Bot,
  PauseCircle,
  PlayCircle,
  ShieldAlert,
  ShieldCheck,
  CreditCard,
} from 'lucide-react';

export default function TreasuryOverview({
  state,
  scenarios,
  onRunScenario,
  onToggleAgent,
  onNavigate,
  loadingEval,
}) {
  const activeAgents = state.agents.filter((a) => a.status === 'ACTIVE').length;
  const blockedCount = state.audit_events.filter((e) => e.decision === 'BLOCKED').length;
  const settledOrMinted = state.cards.length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#059669]">
            Treasury Control Plane
          </p>
          <h1 className="text-2xl font-extrabold tracking-tight text-[#0B1F16] mt-1">
            Autonomous Corporate Banking &amp; Spend Controls
          </h1>
          <p className="text-sm text-[#526B5D] mt-1 max-w-2xl">
            Every AI agent operates from an isolated sub-account governed by a human-signed Ed25519
            IntentMandate and audited before a single-use virtual card can mint.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => onNavigate('integrations')}
            className="rounded-xl border border-[#E2EBE5] bg-white hover:bg-[#F1F6F3] px-3.5 py-2 text-xs font-semibold text-[#0B1F16] transition"
          >
            How Integrations Work
          </button>
          <button
            onClick={() => onNavigate('firewall')}
            className="inline-flex items-center gap-1.5 rounded-xl bg-[#059669] hover:bg-[#047857] px-4 py-2 text-xs font-semibold text-white transition shadow-sm"
          >
            Open Spend Firewall
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* KPI Summary Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="surface-card p-5">
          <div className="text-xs font-medium text-[#526B5D]">Master Treasury Balance</div>
          <div className="text-2xl font-extrabold text-[#0B1F16] tabular-nums mt-1.5">
            ₹{(state.vault?.balance_inr ?? 1840000).toLocaleString('en-IN')}
          </div>
          <div className="text-[11px] text-[#059669] font-medium mt-1">
            {state.vault?.name || 'Acme AI Labs — Operating Vault'}
          </div>
        </div>

        <div className="surface-card p-5">
          <div className="text-xs font-medium text-[#526B5D]">Active Agent Sub-Accounts</div>
          <div className="text-2xl font-extrabold text-[#0B1F16] tabular-nums mt-1.5">
            {activeAgents} <span className="text-base font-semibold text-[#849B8E]">/ {state.agents.length}</span>
          </div>
          <div className="text-[11px] text-[#526B5D] mt-1">Scoped via AP2 IntentMandates</div>
        </div>

        <div className="surface-card p-5">
          <div className="text-xs font-medium text-[#526B5D]">Threats Blocked Pre-Mint</div>
          <div className="text-2xl font-extrabold text-[#0B1F16] tabular-nums mt-1.5">
            {blockedCount}
          </div>
          <div className="text-[11px] text-[#DC2626] font-medium mt-1">
            Sub-limit injections &amp; loops stopped
          </div>
        </div>

        <div className="surface-card p-5">
          <div className="text-xs font-medium text-[#526B5D]">60s Scoped Cards Minted</div>
          <div className="text-2xl font-extrabold text-[#0B1F16] tabular-nums mt-1.5">
            {settledOrMinted}
          </div>
          <div className="text-[11px] text-[#526B5D] mt-1">Exact-rupee Luhn PANs (₹0 bleed)</div>
        </div>
      </div>

      {/* Main 2-Col Split: Agent Sub-Accounts + Interactive Quick Launch */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-7 surface-card p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#E2EBE5] pb-3">
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-[#059669]" />
              <h2 className="text-sm font-bold text-[#0B1F16]">Governed AI Agent Sub-Accounts</h2>
            </div>
            <span className="font-mono text-[10.5px] text-[#849B8E]">DAILY UTILIZATION</span>
          </div>

          <div className="space-y-3">
            {state.agents.map((ag) => {
              const pct = Math.min(100, Math.round((ag.spent_today_inr / ag.daily_limit_inr) * 100));
              const paused = ag.status !== 'ACTIVE';
              return (
                <div
                  key={ag.agent_id}
                  className={`rounded-xl border p-4 transition ${
                    paused ? 'bg-[#FEF2F2]/60 border-[#FECACA]' : 'bg-[#F7FAF8] border-[#E2EBE5]'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-[#0B1F16]">{ag.name}</span>
                        <span
                          className={`rounded-full px-2 py-0.5 font-mono text-[10px] font-semibold ${
                            paused
                              ? 'bg-[#DC2626] text-white'
                              : 'bg-[#ECFDF5] text-[#059669] border border-[#A7F3D0]'
                          }`}
                        >
                          {ag.status}
                        </span>
                      </div>
                      <div className="text-xs text-[#526B5D] mt-0.5">
                        {ag.role} · MCCs: <span className="font-mono">{ag.allowed_mccs.join(', ')}</span>
                      </div>
                    </div>

                    <button
                      onClick={() => onToggleAgent(ag.agent_id)}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-white border border-[#E2EBE5] hover:bg-[#F1F6F3] px-3 py-1.5 text-xs font-semibold text-[#0B1F16] transition"
                    >
                      {paused ? (
                        <PlayCircle className="w-3.5 h-3.5 text-[#059669]" />
                      ) : (
                        <PauseCircle className="w-3.5 h-3.5 text-[#DC2626]" />
                      )}
                      {paused ? 'Resume' : 'Pause'}
                    </button>
                  </div>

                  <div className="mt-3 flex items-center gap-3">
                    <div className="flex-1 h-1.5 rounded-full bg-[#E2EBE5] overflow-hidden">
                      <div
                        className={`h-full transition-all ${paused ? 'bg-[#DC2626]' : 'bg-[#059669]'}`}
                        style={{ width: `${Math.max(2, pct)}%` }}
                      />
                    </div>
                    <span className="font-mono text-[11px] font-semibold text-[#0B1F16] tabular-nums">
                      ₹{ag.spent_today_inr.toLocaleString('en-IN')} / ₹{ag.daily_limit_inr.toLocaleString('en-IN')}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Quick-Launch 3-Act Scenarios */}
        <div className="lg:col-span-5 surface-card p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#E2EBE5] pb-3">
            <div className="flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-[#059669]" />
              <h2 className="text-sm font-bold text-[#0B1F16]">Run Live Stage Scenarios</h2>
            </div>
            <span className="font-mono text-[10.5px] text-[#849B8E]">1-CLICK TRACE</span>
          </div>

          <div className="space-y-2.5">
            {scenarios.map((sc) => (
              <button
                key={sc.id}
                disabled={loadingEval}
                onClick={() => onRunScenario(sc.request)}
                className="w-full text-left rounded-xl border border-[#E2EBE5] bg-[#F7FAF8] hover:bg-[#ECFDF5] hover:border-[#A7F3D0] p-3.5 transition group"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] font-bold text-[#059669]">{sc.badge}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-[#849B8E] group-hover:text-[#059669] transition" />
                </div>
                <div className="text-xs font-bold text-[#0B1F16] mt-1">{sc.label}</div>
                <div className="text-[11px] text-[#526B5D] mt-0.5 line-clamp-2">{sc.description}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Audit Activity */}
      <div className="surface-card p-5 space-y-3">
        <div className="flex items-center justify-between border-b border-[#E2EBE5] pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#059669]" />
            <h2 className="text-sm font-bold text-[#0B1F16]">Recent Treasury Ledger Events</h2>
          </div>
          <button
            onClick={() => onNavigate('mandates')}
            className="text-xs font-semibold text-[#059669] hover:underline"
          >
            View full ledger →
          </button>
        </div>

        {state.audit_events.length === 0 ? (
          <div className="py-6 text-center text-xs text-[#849B8E]">
            No checkout evaluations yet. Click any scenario above to trace a live transaction.
          </div>
        ) : (
          <div className="divide-y divide-[#E2EBE5]">
            {state.audit_events.slice(0, 5).map((ev) => (
              <div key={ev.event_id} className="py-2.5 flex flex-wrap items-center justify-between gap-2 text-xs">
                <div className="flex items-center gap-2.5 min-w-0">
                  {ev.decision === 'BLOCKED' ? (
                    <ShieldAlert className="w-4 h-4 text-[#DC2626] shrink-0" />
                  ) : (
                    <ShieldCheck className="w-4 h-4 text-[#059669] shrink-0" />
                  )}
                  <span className="font-mono text-[10.5px] font-semibold text-[#526B5D]">
                    {ev.agent_id}
                  </span>
                  <span className="text-[#0B1F16] truncate">{ev.summary}</span>
                </div>
                <span
                  className={`rounded-full px-2.5 py-0.5 font-mono text-[10px] font-semibold ${
                    ev.decision === 'BLOCKED'
                      ? 'bg-[#FEF2F2] text-[#DC2626]'
                      : ev.decision === 'PASSKEY_REQUIRED'
                      ? 'bg-[#FFFBEB] text-[#D97706]'
                      : 'bg-[#ECFDF5] text-[#059669]'
                  }`}
                >
                  {ev.decision}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
