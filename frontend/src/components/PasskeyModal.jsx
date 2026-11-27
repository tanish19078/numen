import React from 'react';
import { KeyRound, ShieldAlert, Check, X } from 'lucide-react';

export default function PasskeyModal({ challenge, onResolve, onClose, resolving }) {
  if (!challenge) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0B1F16]/45 backdrop-blur-sm p-4">
      <div className="surface-card max-w-lg w-full p-6 space-y-4 border-[#FDE68A]">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-[#FFFBEB] border border-[#FDE68A] text-[#D97706]">
              <KeyRound className="w-5 h-5" />
            </div>
            <div>
              <div className="font-mono text-[10.5px] font-bold text-[#D97706]">FOUNDER PASSKEY ESCALATION</div>
              <h3 className="text-lg font-extrabold text-[#0B1F16]">Hidden Recurring Liability Detected</h3>
            </div>
          </div>
          <button onClick={onClose} className="text-[#526B5D] hover:text-[#0B1F16]">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-3.5 rounded-xl bg-[#FFFBEB] border border-[#FDE68A] text-xs space-y-1.5">
          <div className="font-bold text-[#92400E] flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 shrink-0" />
            {challenge.reason}
          </div>
          <div className="text-[#0B1F16] tabular-nums">
            Headline Checkout: <b>₹{challenge.spend_request.amount_inr}</b> at <b>{challenge.spend_request.merchant_name}</b> — hidden clause binds{' '}
            <b className="text-[#DC2626]">₹{challenge.hidden_liability_inr.toLocaleString('en-IN')}/yr</b>.
          </div>
        </div>

        <p className="text-xs text-[#526B5D] leading-relaxed">
          If approved, Numen mints a <b>single-use exact ₹{challenge.spend_request.amount_inr}</b> card that shreds immediately after the first charge so future annual auto-debits fail automatically.
        </p>

        <div className="grid grid-cols-2 gap-3 pt-1">
          <button
            disabled={resolving}
            onClick={() => onResolve(challenge.challenge_id, 'deny')}
            className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-[#FEF2F2] hover:bg-[#FEE2E2] border border-[#FECACA] py-2.5 text-xs font-bold text-[#DC2626] transition"
          >
            <X className="w-4 h-4" />
            Deny &amp; Block Trap
          </button>
          <button
            disabled={resolving}
            onClick={() => onResolve(challenge.challenge_id, 'approve')}
            className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-[#059669] hover:bg-[#047857] py-2.5 text-xs font-bold text-white transition"
          >
            <Check className="w-4 h-4" />
            Approve 1-Time ₹{challenge.spend_request.amount_inr} Cap
          </button>
        </div>
      </div>
    </div>
  );
}
