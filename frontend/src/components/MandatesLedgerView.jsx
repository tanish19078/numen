import React from 'react';
import { ShieldCheck, FileText } from 'lucide-react';

export default function MandatesLedgerView({
  state,
  mandateForm,
  setMandateForm,
  signingMandate,
  tamperResults,
  onCreateMandate,
  onVerifyTamper,
}) {
  return (
    <div className="space-y-5">
      <div>
        <p className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#059669]">
          Cryptographic Governance
        </p>
        <h1 className="text-2xl font-extrabold tracking-tight text-[#0B1F16] mt-1">
          Signed Google AP2 Mandates &amp; ACID Audit Ledger
        </h1>
        <p className="text-sm text-[#526B5D] mt-1">
          Every Intent, Cart, and Payment Mandate is hashed canonically with SHA-256 and signed with Ed25519.
          Even a +₹1 limit tamper invalidates the signature immediately.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Sign & Verify Ed25519 Mandates */}
        <div className="lg:col-span-6 surface-card p-5 space-y-4">
          <div className="flex items-center gap-2 border-b border-[#E2EBE5] pb-3">
            <ShieldCheck className="w-4 h-4 text-[#059669]" />
            <h2 className="text-sm font-bold text-[#0B1F16]">Ed25519 Mandate Chain (Intent → Cart → Payment)</h2>
          </div>

          <form
            onSubmit={onCreateMandate}
            className="rounded-xl bg-[#F7FAF8] border border-[#E2EBE5] p-4 space-y-3 text-xs"
          >
            <div className="font-mono text-[10.5px] font-bold text-[#059669]">SIGN NEW INTENT MANDATE</div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <select
                value={mandateForm.agent_id}
                onChange={(e) => setMandateForm({ ...mandateForm, agent_id: e.target.value })}
                className="rounded-lg border border-[#E2EBE5] bg-white px-2.5 py-2 font-semibold text-[#0B1F16]"
              >
                {state.agents.map((a) => (
                  <option key={a.agent_id} value={a.agent_id}>
                    {a.name}
                  </option>
                ))}
              </select>
              <input
                type="number"
                min="100"
                value={mandateForm.max_daily_inr}
                onChange={(e) => setMandateForm({ ...mandateForm, max_daily_inr: e.target.value })}
                placeholder="Daily Cap INR"
                className="rounded-lg border border-[#E2EBE5] bg-white px-2.5 py-2 font-mono tabular-nums"
              />
              <input
                value={mandateForm.allowed_mccs_csv}
                onChange={(e) => setMandateForm({ ...mandateForm, allowed_mccs_csv: e.target.value })}
                placeholder="MCCs (CLOUD, API)"
                className="rounded-lg border border-[#E2EBE5] bg-white px-2.5 py-2 font-mono"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <input
                value={mandateForm.natural_language_intent}
                onChange={(e) => setMandateForm({ ...mandateForm, natural_language_intent: e.target.value })}
                className="flex-1 min-w-[200px] rounded-lg border border-[#E2EBE5] bg-white px-3 py-2 text-[#0B1F16]"
                placeholder="Human delegation intent..."
              />
              <button
                type="submit"
                disabled={signingMandate}
                className="rounded-lg bg-[#059669] hover:bg-[#047857] text-white px-4 py-2 font-semibold transition"
              >
                {signingMandate ? 'Signing...' : 'Sign Ed25519'}
              </button>
            </div>
          </form>

          <div className="space-y-2.5 max-h-[440px] overflow-y-auto pr-1">
            {state.mandates.map((m, i) => {
              const mid = m.mandate_id || m.cart_id || m.payment_mandate_id;
              const tv = tamperResults[mid];
              return (
                <div key={i} className="rounded-xl border border-[#E2EBE5] bg-[#F7FAF8] p-3.5 text-xs space-y-1.5">
                  <div className="flex items-center justify-between font-mono text-[10.5px]">
                    <span className="rounded-md bg-[#ECFDF5] border border-[#A7F3D0] px-2 py-0.5 font-bold text-[#059669]">
                      {m.kind} MANDATE
                    </span>
                    <span className="text-[#526B5D]">{mid}</span>
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-2 pt-0.5">
                    <span className="font-semibold text-[#0B1F16]">
                      {m.agent_id || m.merchant_name}{' '}
                      {m.exact_amount_inr ? `· Exact ₹${m.exact_amount_inr.toLocaleString('en-IN')}` : ''}
                    </span>
                    {m.kind === 'INTENT' && m.mandate_id && (
                      <button
                        onClick={() => onVerifyTamper(m.mandate_id)}
                        className="rounded-lg bg-white hover:bg-[#ECFDF5] border border-[#E2EBE5] px-2.5 py-1 font-mono text-[10px] font-semibold text-[#059669] transition"
                      >
                        Run +₹1 Tamper Test
                      </button>
                    )}
                  </div>
                  {tv && (
                    <div className="rounded-lg bg-white border border-[#E2EBE5] px-3 py-1.5 font-mono text-[10.5px] font-semibold flex flex-wrap gap-4">
                      <span className="text-[#059669]">Original Sig: {tv.original_valid ? 'VALID ✓' : 'INVALID ✕'}</span>
                      <span className="text-[#DC2626]">+₹1 Tampered Sig: {tv.tampered_valid ? 'ACCEPTED' : 'REJECTED ✕'}</span>
                    </div>
                  )}
                  <div className="font-mono text-[10px] text-[#849B8E] truncate">SHA256: {m.canonical_hash}</div>
                  <div className="font-mono text-[10px] text-[#526B5D] truncate">Ed25519: {m.signature_b64}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Immutable ACID Ledger */}
        <div className="lg:col-span-6 surface-card p-5 space-y-4">
          <div className="flex items-center gap-2 border-b border-[#E2EBE5] pb-3">
            <FileText className="w-4 h-4 text-[#059669]" />
            <h2 className="text-sm font-bold text-[#0B1F16]">SQLite WAL Audit Ledger</h2>
          </div>

          <div className="space-y-2 max-h-[580px] overflow-y-auto pr-1">
            {state.audit_events.length === 0 ? (
              <div className="py-10 text-center text-xs text-[#849B8E]">
                No audit events logged yet.
              </div>
            ) : (
              state.audit_events.map((ev) => (
                <div key={ev.event_id} className="rounded-xl border border-[#E2EBE5] bg-[#F7FAF8] p-3 text-xs space-y-1">
                  <div className="flex items-center justify-between font-mono text-[10px]">
                    <span
                      className={`font-bold ${
                        ev.decision === 'BLOCKED' || ev.decision === 'DECLINED'
                          ? 'text-[#DC2626]'
                          : ev.decision === 'PASSKEY_REQUIRED'
                          ? 'text-[#D97706]'
                          : 'text-[#059669]'
                      }`}
                    >
                      [{ev.event_type}] · {ev.decision}
                    </span>
                    <span className="text-[#849B8E]">{ev.agent_id}</span>
                  </div>
                  <div className="text-[#0B1F16] leading-snug">{ev.summary}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
