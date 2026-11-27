import React from 'react';
import { BarChart3 } from 'lucide-react';
import CustomAttackLab from './CustomAttackLab';

export default function BenchmarksLabView({
  agents,
  benchmark,
  runningBench,
  loadingEval,
  onRunBenchmarks,
  onEvaluate,
}) {
  return (
    <div className="space-y-6">
      <div>
        <p className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#059669]">
          Verification &amp; Red-Team Suite
        </p>
        <h1 className="text-2xl font-extrabold tracking-tight text-[#0B1F16] mt-1">
          240-Scenario Adversarial Benchmark &amp; Custom Payload Lab
        </h1>
        <p className="text-sm text-[#526B5D] mt-1">
          Execute 240 live deterministic evaluations against the backend firewall or test custom injections directly.
        </p>
      </div>

      {/* 240-Case Benchmark Panel */}
      <div className="surface-card p-5 space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E2EBE5] pb-4">
          <div className="flex items-center gap-2.5">
            <BarChart3 className="w-4 h-4 text-[#059669]" />
            <div>
              <h2 className="text-sm font-bold text-[#0B1F16]">240-Scenario Red-Team Verification Suite</h2>
              <p className="text-xs text-[#526B5D]">
                90 sub-limit injections + 50 fine-print traps + 30 spoofed domains + 20 retry loops + 50 legitimate cloud checkouts.
              </p>
            </div>
          </div>
          <button
            onClick={onRunBenchmarks}
            disabled={runningBench}
            className="rounded-xl bg-[#059669] hover:bg-[#047857] text-white px-4 py-2 text-xs font-semibold transition shadow-sm"
          >
            {runningBench ? 'Running 240 Cases...' : 'Run 240 Benchmarks'}
          </button>
        </div>

        {benchmark ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] p-4">
              <div className="font-mono text-[10px] font-bold text-[#059669]">INJECTION BLOCK RATE</div>
              <div className="text-3xl font-extrabold text-[#0B1F16] tabular-nums mt-1">
                {benchmark.injection_block_rate_pct}%
              </div>
              <div className="text-xs text-[#526B5D] mt-1 tabular-nums">
                {benchmark.sublimit_injections_blocked}/{benchmark.sublimit_injections_total} caught (Static Cap:{' '}
                {benchmark.static_card_block_rate_pct}%)
              </div>
            </div>

            <div className="rounded-xl bg-[#F7FAF8] border border-[#E2EBE5] p-4">
              <div className="font-mono text-[10px] font-bold text-[#526B5D]">POST-SETTLE BLEED</div>
              <div className="text-3xl font-extrabold text-[#059669] tabular-nums mt-1">
                ₹{benchmark.post_settlement_bleed_inr}
              </div>
              <div className="text-xs text-[#526B5D] mt-1 tabular-nums">
                False Positives: {benchmark.legit_false_positives}/{benchmark.legit_total}
              </div>
            </div>

            <div className="rounded-xl bg-[#FFFBEB] border border-[#FDE68A] p-4">
              <div className="font-mono text-[10px] font-bold text-[#D97706]">TRAPS &amp; SPOOFS CAUGHT</div>
              <div className="text-2xl font-extrabold text-[#0B1F16] tabular-nums mt-1">
                {benchmark.fineprint_traps_caught}/{benchmark.fineprint_traps_total} · {benchmark.spoofed_domains_blocked}/{benchmark.spoofed_domains_total}
              </div>
              <div className="text-xs text-[#526B5D] mt-1">Annual lock-ins &amp; lookalikes</div>
            </div>

            <div className="rounded-xl bg-[#EFF6FF] border border-[#BFDBFE] p-4">
              <div className="font-mono text-[10px] font-bold text-[#2563EB]">PRE-FILTER LATENCY</div>
              <div className="text-2xl font-extrabold text-[#0B1F16] tabular-nums mt-1">
                P95 {benchmark.p95_latency_ms}ms
              </div>
              <div className="text-xs text-[#526B5D] mt-1 tabular-nums">
                Median P50 {benchmark.p50_latency_ms}ms
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-xl bg-[#F7FAF8] border border-[#E2EBE5] py-8 text-center text-xs text-[#526B5D]">
            Click <b>Run 240 Benchmarks</b> to evaluate live defense precision, false positives, and deterministic pre-filter speed.
          </div>
        )}
      </div>

      {/* Custom Payload Attack Lab */}
      <CustomAttackLab agents={agents} onEvaluate={onEvaluate} loading={loadingEval} />
    </div>
  );
}
