import React, { useEffect, useState } from 'react';
import { CreditCard, CheckCircle2, AlertTriangle, Ban, Clock } from 'lucide-react';

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
      <div className="numen-card p-5 border-dashed border-2 border-[#CDE4C8] text-center space-y-2">
        <CreditCard className="w-8 h-8 mx-auto text-[#4A6653]" />
        <div className="font-bold text-sm text-[#0D2616]">No Active Ephemeral Virtual Card</div>
        <p className="text-xs text-[#4A6653]">
          Trigger <b>Scenario 1</b> (or pass any custom spend evaluation) to mint a 60-second single-use Luhn PAN locked to the exact rupee amount.
        </p>
      </div>
    );
  }

  const isActive = card.status === 'ACTIVE' && secondsLeft > 0;
  const isShredded = card.status === 'SHREDDED';

  return (
    <div className="space-y-3">
      <div
        className={`p-5 rounded-3xl border-2 transition-all ${
          isActive
            ? 'mint-card-surface text-[#0D2616]'
            : isShredded
            ? 'bg-[#E8F8E2] border-[#15803D] text-[#0D2616]'
            : 'bg-[#FFE8EC] border-[#E11D48] text-[#0D2616]'
        }`}
      >
        <div className="flex items-center justify-between">
          <span className="text-xl font-black tracking-tight">Numen</span>
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 font-mono text-[11px] font-bold ${
              isActive
                ? 'bg-[#0D2616] text-[#8CE563]'
                : isShredded
                ? 'bg-[#15803D] text-white'
                : 'bg-[#E11D48] text-white'
            }`}
          >
            <Clock className="w-3 h-3" />
            {isActive ? `ACTIVE • TTL ${secondsLeft}s` : card.status}
          </span>
        </div>

        <div className="my-4 font-mono text-xl sm:text-2xl font-bold tracking-widest">
          {card.pan.replace(/(\d{4})(?=\d)/g, '$1  ')}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[#0D2616]/15 font-mono text-[11px] font-bold">
          <span>CVV: {card.cvv}</span>
          <span>EXP: {card.exp_month}/{card.exp_year}</span>
          <span>MERCHANT: {card.merchant_name}</span>
          <span>EXACT LOCK: ₹{card.exact_amount_inr.toLocaleString('en-IN')}</span>
        </div>
      </div>

      {/* Live Merchant Settlement Proof Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <button
          onClick={() => onCharge(card.card_id, card.merchant_name, card.merchant_mcc, card.exact_amount_inr)}
          className="rounded-xl bg-[#15803D] hover:bg-[#166534] text-white px-3 py-2 text-xs font-bold transition shadow-sm"
        >
          ✓ Test Valid Charge (₹{card.exact_amount_inr})
        </button>
        <button
          onClick={() => onCharge(card.card_id, card.merchant_name, card.merchant_mcc, card.exact_amount_inr + 1)}
          className="rounded-xl bg-[#FEF5E4] hover:bg-[#FDE68A] border border-[#D97706] text-[#92400E] px-3 py-2 text-xs font-bold transition"
        >
          ⚠ Test +₹1 Overcharge (₹{card.exact_amount_inr + 1})
        </button>
        <button
          onClick={() => onCharge(card.card_id, card.merchant_name, card.merchant_mcc, card.exact_amount_inr)}
          className="rounded-xl bg-[#FFE8EC] hover:bg-[#FECDD3] border border-[#E11D48] text-[#9F1239] px-3 py-2 text-xs font-bold transition"
        >
          ↻ Test 2nd Recurring Charge
        </button>
      </div>

      {chargeFeedback && (
        <div
          className={`p-3 rounded-xl border text-xs flex items-start gap-2 ${
            chargeFeedback.approved
              ? 'bg-[#E8F8E2] border-[#15803D] text-[#0D2616]'
              : 'bg-[#FFE8EC] border-[#E11D48] text-[#9F1239]'
          }`}
        >
          {chargeFeedback.approved ? (
            <CheckCircle2 className="w-4 h-4 text-[#15803D] shrink-0 mt-0.5" />
          ) : (
            <Ban className="w-4 h-4 text-[#E11D48] shrink-0 mt-0.5" />
          )}
          <div>
            <div className="font-mono font-bold">
              [{chargeFeedback.reason_code}] • Card Status: {chargeFeedback.card_status}
            </div>
            <div>{chargeFeedback.message}</div>
          </div>
        </div>
      )}
    </div>
  );
}
