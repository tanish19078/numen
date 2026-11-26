import React, { useCallback, useEffect, useState } from 'react';
import {
  Wallet,
  Bot,
  PauseCircle,
  PlayCircle,
  Zap,
  ShieldCheck,
  Terminal,
  BarChart3,
  FileCode2,
} from 'lucide-react';
import { api } from './api';
import TopNav from './components/TopNav';
import VirtualCardView from './components/VirtualCardView';
import AuditStreamPane from './components/AuditStreamPane';
import CustomAttackLab from './components/CustomAttackLab';
import PasskeyModal from './components/PasskeyModal';

const SAMPLE_MCP_CALL = JSON.stringify(
  {
    jsonrpc: '2.0',
    id: 'demo-1',
    method: 'tools/call',
    params: {
      name: 'request_scoped_card',
      arguments: {
        agent_id: 'agent-devops',
        merchant_name: 'RunPod Cloud',
        merchant_domain: 'runpod.io',
        merchant_mcc: 'CLOUD',
        amount_inr: 3400,
        cart_items: ['2x NVIDIA A100 GPU hours'],
        agent_reasoning: 'Traffic spike exceeded 85% GPU threshold; scaling 2x A100 nodes.',
      },
    },
  },
  null,
  2
);

export default function App() {
  const [activeTab, setActiveTab] = useState('arena');
  const [health, setHealth] = useState(null);
  const [state, setState] = useState({ vault: null, agents: [], mandates: [], cards: [], passkeys: [], audit_events: [] });
  const [scenarios, setScenarios] = useState([]);
  const [evaluation, setEvaluation] = useState(null);
  const [activeCard, setActiveCard] = useState(null);
  const [chargeFeedback, setChargeFeedback] = useState(null);
  const [passkeyModal, setPasskeyModal] = useState(null);
  const [sseFeed, setSseFeed] = useState([]);
  const [loadingEval, setLoadingEval] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [resolvingPk, setResolvingPk] = useState(false);
  const [benchmark, setBenchmark] = useState(null);
  const [runningBench, setRunningBench] = useState(false);
  const [mcpPayload, setMcpPayload] = useState(SAMPLE_MCP_CALL);
  const [mcpResult, setMcpResult] = useState(null);
  const [errorBanner, setErrorBanner] = useState(null);

  const refreshState = useCallback(async () => {
    try {
      const [h, st, sc] = await Promise.all([api.getHealth(), api.getState(), api.getScenarios()]);
      setHealth(h);
      setState(st);
      setScenarios(sc.scenarios || []);
      if (st.cards?.length > 0 && !activeCard) {
        setActiveCard(st.cards[0]);
      }
    } catch (err) {
      setErrorBanner(err.message);
    }
  }, [activeCard]);

  useEffect(() => {
    refreshState();
  }, []);

  useEffect(() => {
    const es = new EventSource('/api/stream');
    es.onmessage = (ev) => {
      try {
        const parsed = JSON.parse(ev.data);
        setSseFeed((prev) => [parsed, ...prev].slice(0, 25));
      } catch {
        // ignore keepalive parse errors
      }
    };
    return () => es.close();
  }, []);

  const handleEvaluate = async (spendPayload) => {
    setLoadingEval(true);
    setErrorBanner(null);
    setChargeFeedback(null);
    try {
      const res = await api.evaluateSpend(spendPayload);
      setEvaluation(res);
      if (res.virtual_card) {
        setActiveCard(res.virtual_card);
      }
      if (res.decision === 'PASSKEY_REQUIRED' && res.passkey_challenge) {
        setPasskeyModal(res.passkey_challenge);
      }
      const st = await api.getState();
      setState(st);
      setActiveTab('arena');
    } catch (err) {
      setErrorBanner(err.message);
    } finally {
      setLoadingEval(false);
    }
  };

  const handleCharge = async (cardId, merchantName, merchantMcc, amountInr) => {
    setErrorBanner(null);
    try {
      const res = await api.chargeCard(cardId, {
        merchant_name: merchantName,
        merchant_mcc: merchantMcc,
        amount_inr: amountInr,
      });
      setChargeFeedback(res);
      const st = await api.getState();
      setState(st);
      const updated = st.cards.find((c) => c.card_id === cardId);
      if (updated) setActiveCard(updated);
    } catch (err) {
      setErrorBanner(err.message);
    }
  };

  const handleResolvePasskey = async (challengeId, action) => {
    setResolvingPk(true);
    try {
      const res = await api.resolvePasskey(challengeId, action);
      setPasskeyModal(null);
      if (res.evaluation) {
        setEvaluation(res.evaluation);
        if (res.evaluation.virtual_card) setActiveCard(res.evaluation.virtual_card);
      }
      const st = await api.getState();
      setState(st);
    } catch (err) {
      setErrorBanner(err.message);
    } finally {
      setResolvingPk(false);
    }
  };

  const handleToggleAgent = async (agentId) => {
    try {
      await api.toggleAgent(agentId);
      const st = await api.getState();
      setState(st);
    } catch (err) {
      setErrorBanner(err.message);
    }
  };

  const handleReset = async () => {
    setResetting(true);
    setErrorBanner(null);
    try {
      const st = await api.resetDemo();
      setState(st);
      setEvaluation(null);
      setActiveCard(null);
      setChargeFeedback(null);
      setPasskeyModal(null);
    } catch (err) {
      setErrorBanner(err.message);
    } finally {
      setResetting(false);
    }
  };

  const handleRunBenchmarks = async () => {
    setRunningBench(true);
    try {
      const res = await api.runBenchmarks();
      setBenchmark(res);
    } catch (err) {
      setErrorBanner(err.message);
    } finally {
      setRunningBench(false);
    }
  };

  const handleRunMcp = async (overridePayload) => {
    try {
      const body = overridePayload || JSON.parse(mcpPayload);
      const res = await api.callMcp(body);
      setMcpResult(res);
      const st = await api.getState();
      setState(st);
    } catch (err) {
      setMcpResult({ error: err.message });
    }
  };

  return (
    <div className="min-h-screen pb-10">
      <TopNav
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        onReset={handleReset}
        resetting={resetting}
      />

      <main className="mx-auto max-w-[1440px] px-4 pt-5 space-y-5">
        {errorBanner && (
          <div className="rounded-2xl bg-[#FFE8EC] border border-[#E11D48] px-4 py-2.5 text-xs font-bold text-[#9F1239] flex justify-between items-center">
            <span>Error: {errorBanner}</span>
            <button onClick={() => setErrorBanner(null)} className="underline">Dismiss</button>
          </div>
        )}

        {/* ==================== TAB 1: LIVE SPEND ARENA ==================== */}
        {activeTab === 'arena' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
            {/* LEFT PANE: MASTER VAULT, AGENT SUB-ACCOUNTS, SCENARIOS & 60s CARD */}
            <div className="lg:col-span-5 space-y-4">
              {/* Master Vault Hero Card */}
              <div className="numen-card p-5 flex items-center justify-between">
                <div>
                  <span className="inline-flex items-center gap-1 rounded-full bg-[#E8F8E2] px-2.5 py-0.5 font-mono text-[10px] font-bold text-[#15803D]">
                    <Wallet className="w-3 h-3" />
                    MASTER TREASURY VAULT
                  </span>
                  <div className="font-bold text-base mt-1 text-[#0D2616]">
                    {state.vault?.name || 'Acme AI Labs — Operating Vault'}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-black text-[#0D2616]">
                    ₹{(state.vault?.balance_inr ?? 1840000).toLocaleString('en-IN')}
                  </div>
                  <div className="font-mono text-[11px] font-semibold text-[#15803D]">
                    {state.agents.filter((a) => a.status === 'ACTIVE').length} / {state.agents.length} Agents Active
                  </div>
                </div>
              </div>

              {/* 3 Governed AI Agent Sub-Accounts */}
              <div className="numen-card p-4 space-y-2.5">
                <div className="font-mono text-[11px] font-bold text-[#4A6653] flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Bot className="w-3.5 h-3.5 text-[#15803D]" />
                    AI AGENT SUB-ACCOUNTS
                  </span>
                  <span>DAILY ALLOWANCE</span>
                </div>
                {state.agents.map((ag) => {
                  const pct = Math.min(100, Math.round((ag.spent_today_inr / ag.daily_limit_inr) * 100));
                  const paused = ag.status !== 'ACTIVE';
                  return (
                    <div
                      key={ag.agent_id}
                      className={`p-3 rounded-2xl border transition ${
                        paused ? 'bg-[#FFE8EC]/60 border-[#E11D48]/50' : 'bg-[#F6FBF5] border-[#CDE4C8]'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-sm text-[#0D2616]">{ag.name}</span>
                            <span
                              className={`rounded-full px-2 py-0.5 font-mono text-[9.5px] font-bold ${
                                paused ? 'bg-[#E11D48] text-white' : 'bg-[#E8F8E2] text-[#15803D]'
                              }`}
                            >
                              {ag.status}
                            </span>
                          </div>
                          <div className="text-[11px] text-[#4A6653]">{ag.role} • MCC: {ag.allowed_mccs.join(', ')}</div>
                        </div>
                        <button
                          onClick={() => handleToggleAgent(ag.agent_id)}
                          className="inline-flex items-center gap-1 rounded-xl bg-white border border-[#CDE4C8] px-2.5 py-1 text-[11px] font-bold hover:bg-[#E8F8E2]"
                        >
                          {paused ? <PlayCircle className="w-3.5 h-3.5 text-[#15803D]" /> : <PauseCircle className="w-3.5 h-3.5 text-[#E11D48]" />}
                          {paused ? 'Resume' : 'Pause'}
                        </button>
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-[10.5px] font-mono">
                        <div className="flex-1 h-1.5 rounded-full bg-[#E2F0DE] overflow-hidden">
                          <div className="h-full bg-[#15803D]" style={{ width: `${pct}%` }} />
                        </div>
                        <span>₹{ag.spent_today_inr.toLocaleString('en-IN')} / ₹{ag.daily_limit_inr.toLocaleString('en-IN')}</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* 4 One-Click Stage Demo Scenarios */}
              <div className="numen-card p-4 space-y-2.5">
                <div className="font-mono text-[11px] font-bold text-[#15803D] flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5" />
                  ONE-CLICK LIVE STAGE SCENARIOS
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {scenarios.map((sc) => (
                    <button
                      key={sc.id}
                      disabled={loadingEval}
                      onClick={() => handleEvaluate(sc.request)}
                      className="text-left p-3 rounded-2xl bg-[#F6FBF5] hover:bg-[#E8F8E2] border border-[#CDE4C8] hover:border-[#15803D] transition space-y-1"
                    >
                      <div className="font-mono text-[9.5px] font-bold text-[#0D9488]">{sc.badge}</div>
                      <div className="font-bold text-xs text-[#0D2616]">{sc.label}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Live Mint-Lime 60s Virtual Card + Merchant Settlement Tester */}
              <VirtualCardView card={activeCard} onCharge={handleCharge} chargeFeedback={chargeFeedback} />
            </div>

            {/* RIGHT PANE: GEMINI ENTERPRISE CONTROL PLANE */}
            <div className="lg:col-span-7">
              <AuditStreamPane
                evaluation={evaluation}
                sseFeed={sseFeed}
                onOpenPasskey={(ch) => setPasskeyModal(ch)}
              />
            </div>
          </div>
        )}

        {/* ==================== TAB 2: CUSTOM ATTACK LAB ==================== */}
        {activeTab === 'lab' && (
          <div className="space-y-4">
            <CustomAttackLab agents={state.agents} onEvaluate={handleEvaluate} loading={loadingEval} />
          </div>
        )}

        {/* ==================== TAB 3: AP2 MANDATES & ACID LEDGER ==================== */}
        {activeTab === 'ledger' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div className="numen-card p-5 space-y-3">
              <div className="font-mono text-xs font-bold text-[#15803D] flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4" />
                SIGNED GOOGLE AP2 MANDATES (Ed25519 + SHA-256)
              </div>
              <div className="space-y-2.5 max-h-[540px] overflow-y-auto pr-1">
                {state.mandates.map((m, i) => (
                  <div key={i} className="p-3 rounded-2xl bg-[#F6FBF5] border border-[#CDE4C8] text-xs space-y-1">
                    <div className="flex justify-between font-mono font-bold">
                      <span className="text-[#15803D]">{m.kind} MANDATE</span>
                      <span className="text-[#4A6653]">{m.mandate_id || m.cart_id || m.payment_mandate_id}</span>
                    </div>
                    <div className="text-[#0D2616] font-semibold">
                      Agent: {m.agent_id || m.merchant_name} {m.exact_amount_inr ? `• Exact INR ${m.exact_amount_inr}` : ''}
                    </div>
                    <div className="font-mono text-[10px] text-[#4A6653] truncate">SHA256: {m.canonical_hash}</div>
                    <div className="font-mono text-[10px] text-[#0D9488] truncate">Ed25519 Sig: {m.signature_b64}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="numen-card p-5 space-y-3">
              <div className="font-mono text-xs font-bold text-[#1D4ED8] flex items-center gap-1.5">
                <FileCode2 className="w-4 h-4" />
                AUDIT LEDGER &amp; EPHEMERAL CARD HISTORY
              </div>
              <div className="space-y-2 max-h-[540px] overflow-y-auto pr-1">
                {state.audit_events.map((ev) => (
                  <div key={ev.event_id} className="p-3 rounded-2xl bg-[#F6FBF5] border border-[#CDE4C8] text-xs space-y-0.5">
                    <div className="flex justify-between font-mono text-[10px] font-bold">
                      <span className={ev.decision === 'BLOCKED' ? 'text-[#E11D48]' : 'text-[#15803D]'}>
                        [{ev.event_type}] {ev.decision}
                      </span>
                      <span className="text-[#4A6653]">{ev.agent_id}</span>
                    </div>
                    <div className="text-[#0D2616]">{ev.summary}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ==================== TAB 4: BENCHMARKS & MCP INSPECTOR ==================== */}
        {activeTab === 'benchmarks' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            <div className="lg:col-span-6 numen-card p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#E2F0DE] pb-3">
                <div>
                  <div className="font-mono text-xs font-bold text-[#0D9488] flex items-center gap-1.5">
                    <BarChart3 className="w-4 h-4" />
                    240-SCENARIO RED-TEAM BENCHMARK SUITE
                  </div>
                  <p className="text-xs text-[#4A6653]">Runs 90 sub-limit injections, 50 SaaS traps, 30 spoofed domains, 20 retry loops &amp; 50 clean checkouts live.</p>
                </div>
                <button
                  onClick={handleRunBenchmarks}
                  disabled={runningBench}
                  className="rounded-xl bg-[#8CE563] hover:bg-[#7AD950] border border-[#15803D] px-4 py-2 text-xs font-black text-[#0D2616]"
                >
                  {runningBench ? 'Running 240 Cases...' : 'Run 240 Benchmarks'}
                </button>
              </div>

              {benchmark ? (
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3.5 rounded-2xl bg-[#E8F8E2] border border-[#15803D]">
                    <div className="font-mono text-[10px] text-[#15803D] font-bold">SUB-LIMIT INJECTION BLOCK RATE</div>
                    <div className="text-3xl font-black text-[#0D2616] mt-1">{benchmark.injection_block_rate_pct}%</div>
                    <div className="text-[#4A6653]">{benchmark.sublimit_injections_blocked}/{benchmark.sublimit_injections_total} blocked (Static Card: {benchmark.static_card_block_rate_pct}%)</div>
                  </div>
                  <div className="p-3.5 rounded-2xl bg-[#F6FBF5] border border-[#CDE4C8]">
                    <div className="font-mono text-[10px] text-[#0D9488] font-bold">POST-SETTLEMENT BLEED</div>
                    <div className="text-3xl font-black text-[#15803D] mt-1">₹{benchmark.post_settlement_bleed_inr}</div>
                    <div className="text-[#4A6653]">False Positives: {benchmark.legit_false_positives}/{benchmark.legit_total}</div>
                  </div>
                  <div className="p-3.5 rounded-2xl bg-[#FEF5E4] border border-[#D97706]">
                    <div className="font-mono text-[10px] text-[#D97706] font-bold">FINE-PRINT &amp; SPOOFS CAUGHT</div>
                    <div className="text-xl font-black text-[#0D2616] mt-1">
                      {benchmark.fineprint_traps_caught}/{benchmark.fineprint_traps_total} Traps • {benchmark.spoofed_domains_blocked}/{benchmark.spoofed_domains_total} Spoofs
                    </div>
                  </div>
                  <div className="p-3.5 rounded-2xl bg-[#E8F1FF] border border-[#1D4ED8]">
                    <div className="font-mono text-[10px] text-[#1D4ED8] font-bold">EVALUATION LATENCY</div>
                    <div className="text-xl font-black text-[#0D2616] mt-1">
                      P50 {benchmark.p50_latency_ms}ms • P95 {benchmark.p95_latency_ms}ms
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-6 rounded-2xl bg-[#F6FBF5] border border-[#CDE4C8] text-xs text-[#4A6653] text-center">
                  Click <b>Run 240 Benchmarks</b> to execute the real-time verification suite on the FastAPI backend.
                </div>
              )}
            </div>

            <div className="lg:col-span-6 numen-card p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-[#E2F0DE] pb-3">
                <div className="font-mono text-xs font-bold text-[#1D4ED8] flex items-center gap-1.5">
                  <Terminal className="w-4 h-4" />
                  MCP JSON-RPC 2.0 INSPECTOR (POST /mcp)
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleRunMcp({ jsonrpc: '2.0', id: 'list-1', method: 'tools/list' })}
                    className="rounded-xl bg-[#F6FBF5] border border-[#CDE4C8] px-3 py-1.5 text-xs font-bold"
                  >
                    tools/list
                  </button>
                  <button
                    onClick={() => handleRunMcp(null)}
                    className="rounded-xl bg-[#15803D] text-white px-3 py-1.5 text-xs font-bold"
                  >
                    Send JSON-RPC
                  </button>
                </div>
              </div>
              <textarea
                rows={8}
                value={mcpPayload}
                onChange={(e) => setMcpPayload(e.target.value)}
                className="w-full rounded-xl border border-[#CDE4C8] bg-[#F6FBF5] p-3 font-mono text-[11px]"
              />
              {mcpResult && (
                <pre className="rounded-xl bg-[#F3F8F1] border border-[#CDE4C8] p-3 font-mono text-[10.5px] max-h-52 overflow-auto">
                  {JSON.stringify(mcpResult, null, 2)}
                </pre>
              )}
            </div>
          </div>
        )}
      </main>

      <PasskeyModal
        challenge={passkeyModal}
        onResolve={handleResolvePasskey}
        onClose={() => setPasskeyModal(null)}
        resolving={resolvingPk}
      />
    </div>
  );
}
