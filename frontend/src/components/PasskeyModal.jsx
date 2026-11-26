import React from 'react';
import { KeyRound, ShieldAlert, Check, X } from 'lucide-react';

export default function PasskeyModal({ challenge, onResolve, onClose, resolving }) {
  if (!challenge) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0D2616]/45 backdrop-blur-sm p-4">
      <div className="numen-card max-w-lg w-full p-6 space-y-4 border-2 border-[#D97706]">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 rounded-2xl bg-[#FEF5E4] border border-[#D97706] text-[#D97706]">
              <KeyRound className="w-5 h-5" />
            </div>
            <div>
              <div className="font-mono text-[11px] font-bold text-[#D97706]">FOUNDER PASSKEY ESCALATION</div>
              <h3 className="text-lg font-extrabold text-[#0D2616]">Hidden Recurring Liability Detected</h3>
            </div>
          </div>
          <button onClick={onClose} className="text-[#4A6653] hover:text-[#0D2616]">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-3.5 rounded-2xl bg-[#FEF5E4] border border-[#D97706]/50 text-xs space-y-1.5">
          <div className="font-bold text-[#92400E] flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4" />
            {challenge.reason}
          </div>
          <div className="text-[#0D2616]">
            Headline Checkout: <b>₹{challenge.spend_request.amount_inr}</b> at <b>{challenge.spend_request.merchant_name}</b> — hidden clause commits{' '}
            <b className="text-[#E11D48]">₹{challenge.hidden_liability_inr.toLocaleString('en-IN')}/yr</b>.
          </div>
        </div>

        <p className="text-xs text-[#4A6653]">
          If you approve, Numen mints a <b>single-use exact ₹{challenge.spend_request.amount_inr}</b> card that auto-shreds after the initial charge so future annual renewals automatically decline.
        </p>

        <div className="grid grid-cols-2 gap-3 pt-1">
          <button
            disabled={resolving}
            onClick={() => onResolve(challenge.challenge_id, 'deny')}
            className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-[#FFE8EC] hover:bg-[#FECDD3] border border-[#E11D48] py-2.5 text-xs font-extrabold text-[#E11D48] transition"
          >
            <X className="w-4 h-4" />
            Deny &amp; Block Trap
          </button>
          <button
            disabled={resolving}
            onClick={() => onResolve(challenge.challenge_id, 'approve')}
            className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-[#8CE563] hover:bg-[#7AD950] border border-[#15803D] py-2.5 text-xs font-extrabold text-[#0D2616] transition"
          >
            <Check className="w-4 h-4" />
            Approve 1-Time ₹{challenge.spend_request.amount_inr} Cap
          </button>
        </div>
      </div>
    </div>
  );
}
