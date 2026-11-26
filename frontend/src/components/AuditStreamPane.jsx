import React from 'react';
import { Cpu, ShieldAlert, ShieldCheck, KeyRound, Radio } from 'lucide-react';

export default function AuditStreamPane({ evaluation, sseFeed, onOpenPasskey }) {
  const decisionStyles = {
    MINTED: { bg: 'bg-[#E8F8E2]', border: 'border-[#15803D]', text: 'text-[#15803D]', label: 'MINTED • 60s CARD ISSUED' },
    BLOCKED: { bg: 'bg-[#FFE8EC]', border: 'border-[#E11D48]', text: 'text-[#E11D48]', label: 'BLOCKED • TREASURY PROTECTED' },
    PASSKEY_REQUIRED: { bg: 'bg-[#FEF5E4]', border: 'border-[#D97706]', text: 'text-[#D97706]', label: 'PASSKEY REQUIRED • HITL HOLD' },
  };

  const st = evaluation ? decisionStyles[evaluation.decision] || decisionStyles.BLOCKED : null;

  return (
    <div className="numen-card p-5 flex flex-col gap-4 h-full">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E2F0DE] pb-3">
        <div>
          <div className="font-mono text-[11px] font-bold text-[#1D4ED8] flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5" />
            GEMINI ENTERPRISE GLASS-BOX CONTROL PLANE
          </div>
          <div className="text-xs text-[#4A6653]">ADK + A2A Mesh + AttriGuard + Python Agent Sandbox</div>
        </div>
        {evaluation && (
          <span className="rounded-full bg-[#E8F1FF] border border-[#1D4ED8]/40 px-3 py-1 font-mono text-[11px] font-bold text-[#1D4ED8]">
            Router: {evaluation.model_used} ({evaluation.latency_ms} ms)
          </span>
        )}
      </div>

      {!evaluation ? (
        <div className="p-5 rounded-2xl bg-[#F6FBF5] border border-[#CDE4C8] text-xs text-[#4A6653] space-y-1.5">
          <div className="font-bold text-sm text-[#0D2616]">Ready for Live Agent Checkout Evaluation</div>
          <p>Click any preset scenario on the left pane (or use the Custom Attack Lab) to stream real A2A hops, counterfactual drift scores, and Ed25519 AP2 signature proofs.</p>
        </div>
      ) : (
        <>
          {/* Decision Banner + Legacy Card Comparison */}
          <div className={`p-3.5 rounded-2xl border ${st.bg} ${st.border} space-y-2`}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className={`font-mono text-xs font-black ${st.text}`}>{st.label}</span>
              <span className="rounded-full bg-white/90 px-2.5 py-0.5 font-mono text-[10px] font-bold text-[#0D2616] border border-[#CDE4C8]">
                AP2 Ed25519: {evaluation.ap2_verified ? 'VERIFIED ✓' : 'INVALID ✕'}
              </span>
            </div>
            <div className="text-xs font-semibold text-[#0D2616]">{evaluation.summary}</div>
            <div className="flex flex-wrap items-center justify-between gap-2 pt-1.5 border-t border-black/10 text-[11px]">
              <span className="font-mono text-[#4A6653]">Legacy ₹10k Static Card Verdict:</span>
              <span className="font-mono font-bold text-[#E11D48]">{evaluation.legacy_static_card_verdict}</span>
            </div>
            {evaluation.decision === 'PASSKEY_REQUIRED' && evaluation.passkey_challenge && (
              <button
                onClick={() => onOpenPasskey(evaluation.passkey_challenge)}
                className="mt-1 inline-flex items-center gap-1.5 rounded-xl bg-[#D97706] hover:bg-[#B45309] text-white px-3.5 py-1.5 text-xs font-bold transition"
              >
                <KeyRound className="w-3.5 h-3.5" />
                Open 1-Tap Founder Passkey Approval
              </button>
            )}
          </div>

          {/* AttriGuard Counterfactual World A vs World B */}
          <div className="rounded-2xl bg-[#F6FBF5] border border-[#CDE4C8] p-3.5 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] font-bold text-[#15803D]">
                ATTRIGUARD COUNTERFACTUAL DRIFT (arXiv:2603.10749)
              </span>
              <span
                className={`font-mono text-xs font-black ${
                  evaluation.attriguard.drift_score >= 0.25 ? 'text-[#E11D48]' : 'text-[#15803D]'
                }`}
              >
                Drift: {evaluation.attriguard.drift_score.toFixed(2)} / 1.00
              </span>
            </div>
            <div className="w-full h-2.5 rounded-full bg-[#E2F0DE] overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${
                  evaluation.attriguard.drift_score >= 0.25 ? 'bg-[#E11D48]' : 'bg-[#15803D]'
                }`}
                style={{ width: `${Math.max(4, evaluation.attriguard.drift_score * 100)}%` }}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
              <div className="p-2.5 rounded-xl bg-white border border-[#CDE4C8]">
                <div className="font-mono font-bold text-[#4A6653]">WORLD A (Full Context)</div>
                <div className="mt-0.5 text-[#0D2616] font-medium">{evaluation.attriguard.world_a_action}</div>
              </div>
              <div className="p-2.5 rounded-xl bg-[#E8F8E2] border border-[#15803D]/40">
                <div className="font-mono font-bold text-[#15803D]">WORLD B (DOM Stripped)</div>
                <div className="mt-0.5 text-[#0D2616] font-medium">{evaluation.attriguard.world_b_action}</div>
              </div>
            </div>

            {evaluation.attriguard.poisoned_spans?.length > 0 && (
              <div className="p-2.5 rounded-xl bg-[#FFE8EC] border border-[#E11D48] space-y-1">
                <div className="font-mono text-[10px] font-bold text-[#E11D48] flex items-center gap-1">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  POISONED DOM / INJECTION SPANS ISOLATED:
                </div>
                {evaluation.attriguard.poisoned_spans.map((sp, idx) => (
                  <div key={idx} className="font-mono text-[11px] bg-white/90 text-[#9F1239] p-1.5 rounded border border-[#FECDD3] break-all">
                    {sp}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* A2A Trace Hops */}
          <div className="space-y-1.5">
            <div className="font-mono text-[11px] font-bold text-[#4A6653]">A2A SPECIALIST COMMITTEE TRACE</div>
            <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
              {evaluation.a2a_trace.map((hop, i) => (
                <div key={i} className="flex items-center justify-between gap-2 rounded-xl bg-[#F6FBF5] border border-[#CDE4C8] px-3 py-1.5 font-mono text-[11px]">
                  <span className="font-bold text-[#0D2616]">
                    {hop.from_agent} → <span className="text-[#15803D]">{hop.to_agent}</span>
                  </span>
                  <span className="text-[#4A6653] truncate max-w-[200px]">{hop.action}</span>
                  <span className="text-[#0D9488] font-bold">{hop.latency_ms}ms</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Live SSE Stream Tail */}
      <div className="mt-auto pt-2 border-t border-[#E2F0DE]">
        <div className="font-mono text-[10px] font-bold text-[#0D9488] flex items-center gap-1.5 mb-1.5">
          <Radio className="w-3 h-3 animate-pulse" />
          LIVE /api/stream SSE TELEMETRY
        </div>
        <div className="rounded-xl bg-[#F3F8F1] border border-[#CDE4C8] p-2.5 max-h-28 overflow-y-auto font-mono text-[10.5px] space-y-1">
          {sseFeed.length === 0 ? (
            <div className="text-[#4A6653]">Connected to SSE stream — waiting for live agent events...</div>
          ) : (
            sseFeed.slice(0, 8).map((ev, idx) => (
              <div key={idx} className="text-[#0D2616] truncate">
                <span className="text-[#15803D] font-bold">[{ev.type}]</span>{' '}
                {ev.data?.action || ev.data?.message || JSON.stringify(ev.data)}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
