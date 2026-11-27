import React, { useEffect, useState } from 'react';
import { CreditCard, CheckCircle2, Ban, Clock, Lock } from 'lucide-react';

export default function VirtualCardView({ card, onCharge, chargeFeedback }) {
  const [secondsLeft, setSecondsLeft] = useState(0);

  useEffect(() => {
    if (!card || card.status !== 'ACTIVE') {
      setSecondsLeft(0);
      return;
    }
    const tick = () => {
      const diff = Math.max(0, Math.floor((new Date(card.expires_at).getTime() - Date.now()) / 1000));
      setSecondsLeft(diff);
    };
    tick();
    const id = setInterval(tick, 500);
    return () => clearInterval(id);
  }, [card]);

  if (!card) {
    return (
      <div className="surface-card p-6 border-dashed border-[#CBD8D0] text-center space-y-2.5">
        <div className="w-10 h-10 rounded-full bg-[#F1F6F3] flex items-center justify-center mx-auto">
          <CreditCard className="w-5 h-5 text-[#526B5D]" />
        </div>
        <div className="font-bold text-sm text-[#0B1F16]">No Active 60s Virtual Card</div>
        <p className="text-xs text-[#526B5D] leading-relaxed">
          Run <b>Scenario 1 (Valid GPU Scale)</b> or approve a Passkey request to mint a single-use Luhn
          Visa PAN locked to an exact rupee amount and merchant.
        </p>
      </div>
    );
  }

  const isActive = card.status === 'ACTIVE' && secondsLeft > 0;
  const isShredded = card.status === 'SHREDDED';
  const ttlPct = Math.min(100, Math.round((secondsLeft / 60) * 100));

  return (
    <div className="space-y-4">
      {/* Brushed Dark-Pine Virtual Card */}
      <div
        className={`p-6 transition-all ${
          isActive
            ? 'vault-card-metal text-white'
            : isShredded
            ? 'surface-card bg-[#F7FAF8] text-[#0B1F16]'
            : 'surface-card bg-[#FEF2F2] border-[#FECACA] text-[#0B1F16]'
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg font-extrabold tracking-tight">Numen</span>
            <span
              className={`font-mono text-[10px] font-semibold px-2 py-0.5 rounded-md ${
                isActive
                  ? 'bg-white/10 text-[#6EE7B7]'
                  : 'bg-white border border-[#E2EBE5] text-[#526B5D]'
              }`}
            >
              SINGLE-USE VISA
            </span>
          </div>
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 font-mono text-[11px] font-semibold tabular-nums ${
              isActive
                ? 'bg-[#059669] text-white'
                : isShredded
                ? 'bg-[#ECFDF5] text-[#059669] border border-[#A7F3D0]'
                : 'bg-[#DC2626] text-white'
            }`}
          >
            <Clock className="w-3 h-3" />
            {isActive ? `ACTIVE · ${secondsLeft}s` : card.status}
          </span>
        </div>

        {/* EMV Chip + Exact Lock */}
        <div className="mt-5 flex items-center justify-between">
          <div
            className={`w-9 h-6 rounded-md border ${
              isActive ? 'bg-[#D1FAE5]/20 border-[#6EE7B7]/40' : 'bg-[#E2EBE5] border-[#CBD8D0]'
            }`}
          />
          <div
            className={`inline-flex items-center gap-1 font-mono text-[11px] font-semibold tabular-nums ${
              isActive ? 'text-[#6EE7B7]' : 'text-[#059669]'
            }`}
          >
            <Lock className="w-3 h-3" />
            EXACT LOCK: ₹{card.exact_amount_inr.toLocaleString('en-IN')}
          </div>
        </div>

        {/* PAN */}
        <div className="my-4 font-mono text-xl sm:text-[22px] font-semibold tracking-[0.14em] tabular-nums">
          {card.pan.replace(/(\d{4})(?=\d)/g, '$1 ')}
        </div>

        {isActive && (
          <div className="w-full h-1 rounded-full bg-white/10 overflow-hidden mb-3">
            <div
              className="h-full bg-[#6EE7B7] transition-all duration-500"
              style={{ width: `${ttlPct}%` }}
            />
          </div>
        )}

        <div
          className={`flex flex-wrap items-center justify-between gap-2 pt-3 border-t font-mono text-[11px] font-medium tabular-nums ${
            isActive ? 'border-white/15 text-white/80' : 'border-[#E2EBE5] text-[#526B5D]'
          }`}
        >
          <span>CVV {card.cvv}</span>
          <span>EXP {card.exp_month}/{card.exp_year}</span>
          <span>{card.merchant_name}</span>
          <span>MCC {card.merchant_mcc}</span>
        </div>
      </div>

      {/* Merchant Settlement Tester */}
      <div className="surface-card p-4 space-y-2.5">
        <div className="flex items-center justify-between">
          <span className="font-mono text-[10.5px] font-semibold uppercase tracking-wide text-[#526B5D]">
            Live Merchant Settlement Proof
          </span>
          <span className="font-mono text-[10px] text-[#849B8E]">±₹0.00 TOLERANCE</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <button
            onClick={() => onCharge(card.card_id, card.merchant_name, card.merchant_mcc, card.exact_amount_inr)}
            className="rounded-xl bg-[#059669] hover:bg-[#047857] text-white px-3 py-2 text-xs font-semibold transition tabular-nums"
          >
            Settle ₹{card.exact_amount_inr}
          </button>
          <button
            onClick={() => onCharge(card.card_id, card.merchant_name, card.merchant_mcc, card.exact_amount_inr + 1)}
            className="rounded-xl bg-[#FFFBEB] hover:bg-[#FEF3C7] border border-[#FDE68A] text-[#92400E] px-3 py-2 text-xs font-semibold transition tabular-nums"
          >
            Test +₹1 (₹{card.exact_amount_inr + 1})
          </button>
          <button
            onClick={() => onCharge(card.card_id, card.merchant_name, card.merchant_mcc, card.exact_amount_inr)}
            className="rounded-xl bg-[#FEF2F2] hover:bg-[#FEE2E2] border border-[#FECACA] text-[#DC2626] px-3 py-2 text-xs font-semibold transition"
          >
            Test 2nd Charge
          </button>
        </div>

        {chargeFeedback && (
          <div
            className={`p-3 rounded-xl border text-xs flex items-start gap-2.5 ${
              chargeFeedback.approved
                ? 'bg-[#ECFDF5] border-[#A7F3D0] text-[#0B1F16]'
                : 'bg-[#FEF2F2] border-[#FECACA] text-[#991B1B]'
            }`}
          >
            {chargeFeedback.approved ? (
              <CheckCircle2 className="w-4 h-4 text-[#059669] shrink-0 mt-0.5" />
            ) : (
              <Ban className="w-4 h-4 text-[#DC2626] shrink-0 mt-0.5" />
            )}
            <div className="space-y-0.5">
              <div className="font-mono text-[11px] font-bold">
                [{chargeFeedback.reason_code}] · Card: {chargeFeedback.card_status}
              </div>
              <div>{chargeFeedback.message}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
