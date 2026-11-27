import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  KeyRound,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Radio,
  Zap,
} from 'lucide-react';
import VirtualCardView from './VirtualCardView';

const PIPELINE_STEPS = [
  { id: 'ap2', label: '1. AP2 Ed25519', match: 'AP2.CryptoVerifier' },
  { id: 'router', label: '2. Gemini Router', match: 'Gemini.SmartRouter' },
  { id: 'budget', label: '3. Budget & Loop', match: 'BudgetController' },
  { id: 'camel', label: '4. CaMeL Provenance', match: 'CaMeL.CapabilityGuard' },
  { id: 'attri', label: '5. AttriGuard Drift', match: 'AttriGuard.Firewall' },
  { id: 'mint', label: '6. FinePrint & Mint', match: 'FinePrint.Auditor' },
];

export default function SpendFirewallView({
  scenarios,
  evaluation,
  activeCard,
  chargeFeedback,
  sseFeed,
  loadingEval,
  onEvaluate,
  onRetryLoop,
  onCharge,
  onOpenPasskey,
}) {
  const [traceOpen, setTraceOpen] = useState(false);

  const badgeStyle = {
    MINTED: {
      wrap: 'bg-[#ECFDF5] border-[#A7F3D0]',
      pill: 'bg-[#059669] text-white',
      label: 'APPROVED · 60s CARD MINTED',
    },
    BLOCKED: {
      wrap: 'bg-[#FEF2F2] border-[#FECACA]',
      pill: 'bg-[#DC2626] text-white',
      label: 'BLOCKED PRE-MINT · ₹0 AT RISK',
    },
    PASSKEY_REQUIRED: {
      wrap: 'bg-[#FFFBEB] border-[#FDE68A]',
      pill: 'bg-[#D97706] text-white',
      label: 'PASSKEY ESCALATION REQUIRED',
    },
  };

  const st = evaluation ? badgeStyle[evaluation.decision] || badgeStyle.BLOCKED : null;

  const getStepStatus = (stepMatch) => {
    if (!evaluation) return { state: 'idle', ms: null };
    const hop = evaluation.a2a_trace.find((h) => h.to_agent === stepMatch);
    if (stepMatch === 'FinePrint.Auditor') {
      const mintHop = evaluation.a2a_trace.find((h) => h.to_agent === 'Python.AgentSandbox');
      if (evaluation.decision === 'MINTED' && mintHop) {
        return { state: 'passed', ms: mintHop.latency_ms };
      }
      if (evaluation.decision === 'PASSKEY_REQUIRED') return { state: 'review', ms: hop?.latency_ms };
      if (evaluation.decision === 'BLOCKED' && hop && evaluation.fineprint?.spoofed_domain_of) {
        return { state: 'failed', ms: hop.latency_ms };
      }
    }
    if (!hop) return { state: 'skipped', ms: null };
    if (stepMatch === 'AttriGuard.Firewall' && evaluation.attriguard?.drift_score >= 0.25) {
      return { state: 'failed', ms: hop.latency_ms };
    }
    if (stepMatch === 'BudgetController' && evaluation.budget && !evaluation.budget.passed) {
      return { state: 'failed', ms: hop.latency_ms };
    }
    if (stepMatch === 'CaMeL.CapabilityGuard' && evaluation.camel_provenance && !evaluation.camel_provenance.control_data_isolated) {
      return { state: 'failed', ms: hop.latency_ms };
    }
    return { state: 'passed', ms: hop.latency_ms };
  };

  return (
    <div className="space-y-5">
      {/* Header + Live Scenarios Strip */}
      <div className="surface-card p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-[#059669]" />
            <h1 className="text-sm font-bold text-[#0B1F16]">Live Spend Firewall — Trigger Any Scenario</h1>
          </div>
          {evaluation && (
            <span className="font-mono text-[11px] font-semibold text-[#526B5D] tabular-nums">
              Model: <b className="text-[#0B1F16]">{evaluation.model_used}</b> · {evaluation.latency_ms} ms
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
          {scenarios.map((sc) => (
            <button
              key={sc.id}
              disabled={loadingEval}
              onClick={() => onEvaluate(sc.request)}
              className="text-left rounded-xl border border-[#E2EBE5] bg-[#F7FAF8] hover:bg-[#ECFDF5] hover:border-[#A7F3D0] px-3 py-2.5 transition"
            >
              <div className="font-mono text-[9.5px] font-bold text-[#059669]">{sc.badge}</div>
              <div className="text-xs font-bold text-[#0B1F16] truncate mt-0.5">{sc.label}</div>
            </button>
          ))}
          <button
            disabled={loadingEval}
            onClick={onRetryLoop}
            className="text-left rounded-xl border border-[#FECACA] bg-[#FEF2F2]/70 hover:bg-[#FEF2F2] px-3 py-2.5 transition"
          >
            <div className="font-mono text-[9.5px] font-bold text-[#DC2626]">VELOCITY BREAKER</div>
            <div className="text-xs font-bold text-[#0B1F16] truncate mt-0.5">5. 3x Retry Loop (₹1,200×3)</div>
          </button>
        </div>
      </div>

      {/* Horizontal 6-Gate Causal Pipeline Stepper */}
      <div className="surface-card p-4">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
          {PIPELINE_STEPS.map((step) => {
            const { state, ms } = getStepStatus(step.match);
            return (
              <div
                key={step.id}
                className={`rounded-xl border px-3 py-2.5 transition ${
                  state === 'passed'
                    ? 'bg-[#ECFDF5] border-[#A7F3D0]'
                    : state === 'failed'
                    ? 'bg-[#FEF2F2] border-[#FECACA]'
                    : state === 'review'
                    ? 'bg-[#FFFBEB] border-[#FDE68A]'
                    : 'bg-[#F7FAF8] border-[#E2EBE5] opacity-70'
                }`}
              >
                <div className="flex items-center justify-between gap-1">
                  <span className="font-mono text-[10.5px] font-bold text-[#0B1F16] truncate">{step.label}</span>
                  {state === 'passed' && <CheckCircle2 className="w-3.5 h-3.5 text-[#059669] shrink-0" />}
                  {state === 'failed' && <XCircle className="w-3.5 h-3.5 text-[#DC2626] shrink-0" />}
                </div>
                <div className="font-mono text-[10px] text-[#526B5D] mt-1 tabular-nums">
                  {state === 'idle' ? 'Waiting' : ms != null ? `${ms} ms` : state.toUpperCase()}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Split: Firewall Evidence (7 cols) + Brushed Card & Settlement (5 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        <div className="lg:col-span-7 space-y-4">
          {!evaluation ? (
            <div className="surface-card p-8 text-center space-y-2">
              <div className="text-base font-bold text-[#0B1F16]">Ready for Spend Verification</div>
              <p className="text-xs text-[#526B5D] max-w-md mx-auto leading-relaxed">
                Select any scenario above to trace Ed25519 mandate checks, AttriGuard World A vs. World B counterfactual
                attribution, fine-print extraction, and single-use virtual card minting.
              </p>
            </div>
          ) : (
            <>
              {/* Verdict Card */}
              <div className={`surface-card p-5 border ${st.wrap} space-y-3`}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className={`rounded-full px-3 py-1 font-mono text-[11px] font-bold ${st.pill}`}>
                    {st.label}
                  </span>
                  <span className="rounded-lg bg-white border border-[#E2EBE5] px-2.5 py-1 font-mono text-[10.5px] font-semibold text-[#0B1F16]">
                    AP2 Ed25519: {evaluation.ap2_verified ? 'VERIFIED' : 'FAILED'}
                  </span>
                </div>
                <p className="text-sm font-semibold text-[#0B1F16] leading-snug">{evaluation.summary}</p>
                <div className="rounded-xl bg-white/80 border border-black/5 px-3 py-2 flex flex-wrap items-center justify-between gap-2 text-xs">
                  <span className="text-[#526B5D] font-medium">Legacy ₹10,000 Static Corporate Card:</span>
                  <span className="font-mono font-bold text-[#DC2626]">{evaluation.legacy_static_card_verdict}</span>
                </div>
                {evaluation.decision === 'PASSKEY_REQUIRED' && evaluation.passkey_challenge && (
                  <button
                    onClick={() => onOpenPasskey(evaluation.passkey_challenge)}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-[#D97706] hover:bg-[#B45309] text-white px-4 py-2 text-xs font-bold transition"
                  >
                    <KeyRound className="w-3.5 h-3.5" />
                    Review &amp; Approve with 1-Tap Passkey
                  </button>
                )}
              </div>

              {/* AttriGuard Counterfactual Check */}
              <div className="surface-card p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs font-bold text-[#0B1F16]">
                      AttriGuard Counterfactual Causal Check
                    </div>
                    <div className="text-[11px] text-[#526B5D]">
                      Compares action under untrusted DOM vs. clean human IntentMandate
                    </div>
                  </div>
                  <div
                    className={`font-mono text-sm font-extrabold tabular-nums ${
                      evaluation.attriguard.drift_score >= 0.25 ? 'text-[#DC2626]' : 'text-[#059669]'
                    }`}
                  >
                    Drift {evaluation.attriguard.drift_score.toFixed(2)}
                  </div>
                </div>

                <div className="w-full h-2 rounded-full bg-[#F1F6F3] overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      evaluation.attriguard.drift_score >= 0.25 ? 'bg-[#DC2626]' : 'bg-[#059669]'
                    }`}
                    style={{ width: `${Math.max(4, evaluation.attriguard.drift_score * 100)}%` }}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="rounded-xl bg-[#F7FAF8] border border-[#E2EBE5] p-3">
                    <div className="font-mono text-[10px] font-bold text-[#526B5D]">WORLD A · FULL PAGE</div>
                    <div className="text-[#0B1F16] mt-1 font-medium">{evaluation.attriguard.world_a_action}</div>
                  </div>
                  <div className="rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] p-3">
                    <div className="font-mono text-[10px] font-bold text-[#059669]">WORLD B · MANDATE ONLY</div>
                    <div className="text-[#0B1F16] mt-1 font-medium">{evaluation.attriguard.world_b_action}</div>
                  </div>
                </div>

                {evaluation.attriguard.poisoned_spans?.length > 0 && (
                  <div className="rounded-xl bg-[#FEF2F2] border border-[#FECACA] p-3 space-y-1.5">
                    <div className="flex items-center gap-1.5 font-mono text-[10.5px] font-bold text-[#DC2626]">
                      <ShieldAlert className="w-3.5 h-3.5" />
                      HIDDEN INJECTION STRIPPED FROM DOM
                    </div>
                    {evaluation.attriguard.poisoned_spans.map((sp, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg bg-white border border-[#FECACA] px-2.5 py-1.5 font-mono text-[11px] text-[#991B1B] break-all"
                      >
                        {sp}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* FinePrint & Spoof Callout */}
              {evaluation.fineprint &&
                (evaluation.fineprint.has_trap || evaluation.fineprint.spoofed_domain_of) && (
                  <div className="surface-card p-5 border-[#FDE68A] bg-[#FFFBEB]/60 space-y-2 text-xs">
                    <div className="flex items-center justify-between font-mono text-[11px] font-bold text-[#D97706]">
                      <span>FINE-PRINT &amp; DOMAIN AUDITOR</span>
                      {evaluation.fineprint.hidden_annual_inr > 0 && (
                        <span className="text-[#DC2626] tabular-nums">
                          Hidden Liability: ₹{evaluation.fineprint.hidden_annual_inr.toLocaleString('en-IN')}/yr
                        </span>
                      )}
                    </div>
                    {evaluation.fineprint.spoofed_domain_of && (
                      <div className="font-semibold text-[#991B1B]">
                        Homoglyph spoof detected: impersonates <span className="font-mono">{evaluation.fineprint.spoofed_domain_of}</span>
                      </div>
                    )}
                    {evaluation.fineprint.clauses_flagged?.map((cl, idx) => (
                      <div key={idx} className="rounded-lg bg-white border border-[#FDE68A] p-2.5 text-[#0B1F16]">
                        {cl}
                      </div>
                    ))}
                  </div>
                )}

              {/* Collapsible Forensic Trace & SSE Tail */}
              <div className="surface-card overflow-hidden">
                <button
                  onClick={() => setTraceOpen(!traceOpen)}
                  className="w-full px-5 py-3 flex items-center justify-between text-xs font-bold text-[#0B1F16] hover:bg-[#F7FAF8] transition"
                >
                  <span>Technical Forensic Trace (CaMeL Capabilities, A2A Hops &amp; SSE)</span>
                  {traceOpen ? <ChevronUp className="w-4 h-4 text-[#526B5D]" /> : <ChevronDown className="w-4 h-4 text-[#526B5D]" />}
                </button>
                {traceOpen && (
                  <div className="px-5 pb-4 pt-2 border-t border-[#E2EBE5] space-y-3 text-xs">
                    {evaluation.camel_provenance && (
                      <div className="space-y-1.5">
                        <div className="font-mono text-[10.5px] font-bold text-[#526B5D]">
                          DEEPMIND CaMeL PROVENANCE (arXiv:2503.18813)
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {Object.entries(evaluation.camel_provenance.capability_checks || {}).map(([k, ok]) => (
                            <span
                              key={k}
                              className={`rounded-md px-2 py-0.5 font-mono text-[10px] font-semibold border ${
                                ok
                                  ? 'bg-[#ECFDF5] border-[#A7F3D0] text-[#059669]'
                                  : 'bg-[#FEF2F2] border-[#FECACA] text-[#DC2626]'
                              }`}
                            >
                              {k}: {ok ? 'PASS' : 'FAIL'}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="space-y-1">
                      <div className="font-mono text-[10.5px] font-bold text-[#526B5D]">A2A HOPS</div>
                      {evaluation.a2a_trace.map((hop, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between gap-2 rounded-lg bg-[#F7FAF8] border border-[#E2EBE5] px-3 py-1.5 font-mono text-[10.5px]"
                        >
                          <span className="font-semibold text-[#0B1F16]">
                            {hop.from_agent} → <span className="text-[#059669]">{hop.to_agent}</span>
                          </span>
                          <span className="text-[#526B5D] truncate">{hop.action}</span>
                          <span className="text-[#0B1F16] tabular-nums">{hop.latency_ms}ms</span>
                        </div>
                      ))}
                    </div>

                    <div className="space-y-1">
                      <div className="font-mono text-[10.5px] font-bold text-[#059669] flex items-center gap-1.5">
                        <Radio className="w-3 h-3" />
                        LIVE /api/stream SSE FEED
                      </div>
                      <div className="rounded-lg bg-[#F7FAF8] border border-[#E2EBE5] p-2.5 max-h-28 overflow-y-auto font-mono text-[10.5px] space-y-1">
                        {sseFeed.length === 0 ? (
                          <div className="text-[#849B8E]">Listening on /api/stream...</div>
                        ) : (
                          sseFeed.slice(0, 6).map((ev, idx) => (
                            <div key={idx} className="truncate text-[#0B1F16]">
                              <span className="text-[#059669] font-semibold">[{ev.type}]</span>{' '}
                              {ev.data?.action || ev.data?.message || JSON.stringify(ev.data)}
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Right: Brushed Dark-Pine 60s Card & Live Settlement Tester */}
        <div className="lg:col-span-5">
          <VirtualCardView card={activeCard} onCharge={onCharge} chargeFeedback={chargeFeedback} />
        </div>
      </div>
    </div>
  );
}
