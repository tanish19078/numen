import React, { useCallback, useEffect, useState } from 'react';
import { api } from './api';
import SidebarNav from './components/SidebarNav';
import TreasuryOverview from './components/TreasuryOverview';
import SpendFirewallView from './components/SpendFirewallView';
import MandatesLedgerView from './components/MandatesLedgerView';
import IntegrationsView from './components/IntegrationsView';
import BenchmarksLabView from './components/BenchmarksLabView';
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
  const [activeTab, setActiveTab] = useState('overview');
  const [health, setHealth] = useState(null);
  const [agentCard, setAgentCard] = useState(null);
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
  const [tamperResults, setTamperResults] = useState({});
  const [mandateForm, setMandateForm] = useState({
    agent_id: 'agent-devops',
    natural_language_intent: 'Auto-scale RunPod & GCP GPUs up to INR 25,000/day; zero recurring annual lock-ins.',
    max_daily_inr: 25000,
    max_single_tx_inr: 15000,
    allowed_mccs_csv: 'CLOUD, INFRA, API',
    allow_recurring: false,
  });
  const [signingMandate, setSigningMandate] = useState(false);
  const [errorBanner, setErrorBanner] = useState(null);

  const refreshState = useCallback(async () => {
    try {
      const [h, ac, st, sc] = await Promise.all([
        api.getHealth(),
        api.getAgentCard(),
        api.getState(),
        api.getScenarios(),
      ]);
      setHealth(h);
      setAgentCard(ac);
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
      setActiveTab('firewall');
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

  const handleRetryLoopDemo = async () => {
    setLoadingEval(true);
    setErrorBanner(null);
    setChargeFeedback(null);
    const loopReq = {
      agent_id: 'agent-devops',
      merchant_name: 'RunPod Cloud',
      merchant_domain: 'runpod.io',
      merchant_mcc: 'CLOUD',
      amount_inr: 1200.0,
      cart_items: ['1x A100 GPU node (timeout retry)'],
      agent_reasoning: 'Retrying cloud compute checkout after gateway timeout.',
    };
    try {
      let lastRes = null;
      for (let i = 0; i < 3; i += 1) {
        lastRes = await api.evaluateSpend(loopReq);
      }
      if (lastRes) setEvaluation(lastRes);
      const st = await api.getState();
      setState(st);
      setActiveTab('firewall');
    } catch (err) {
      setErrorBanner(err.message);
    } finally {
      setLoadingEval(false);
    }
  };

  const handleCreateMandate = async (e) => {
    e.preventDefault();
    setSigningMandate(true);
    setErrorBanner(null);
    try {
      await api.createMandate({
        agent_id: mandateForm.agent_id,
        natural_language_intent: mandateForm.natural_language_intent,
        max_daily_inr: Number(mandateForm.max_daily_inr),
        max_single_tx_inr: Number(mandateForm.max_single_tx_inr),
        allowed_mccs: mandateForm.allowed_mccs_csv
          .split(',')
          .map((s) => s.trim().toUpperCase())
          .filter(Boolean),
        allow_recurring: Boolean(mandateForm.allow_recurring),
      });
      const st = await api.getState();
      setState(st);
    } catch (err) {
      setErrorBanner(err.message);
    } finally {
      setSigningMandate(false);
    }
  };

  const handleVerifyTamper = async (mandateId) => {
    setErrorBanner(null);
    try {
      const res = await api.verifyMandateTamper(mandateId);
      setTamperResults((prev) => ({ ...prev, [mandateId]: res }));
    } catch (err) {
      setErrorBanner(err.message);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-[#F7FAF8] text-[#0B1F16]">
      <SidebarNav
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        vault={state.vault}
        health={health}
        onReset={handleReset}
        resetting={resetting}
      />

      <main className="flex-1 min-w-0 p-5 sm:p-8 max-w-[1320px] mx-auto w-full space-y-5">
        {errorBanner && (
          <div className="rounded-xl bg-[#FEF2F2] border border-[#FECACA] px-4 py-3 text-xs font-semibold text-[#991B1B] flex justify-between items-center">
            <span>Error: {errorBanner}</span>
            <button onClick={() => setErrorBanner(null)} className="underline font-bold">
              Dismiss
            </button>
          </div>
        )}

        {activeTab === 'overview' && (
          <TreasuryOverview
            state={state}
            scenarios={scenarios}
            onRunScenario={handleEvaluate}
            onToggleAgent={handleToggleAgent}
            onNavigate={setActiveTab}
            loadingEval={loadingEval}
          />
        )}

        {activeTab === 'firewall' && (
          <SpendFirewallView
            scenarios={scenarios}
            evaluation={evaluation}
            activeCard={activeCard}
            chargeFeedback={chargeFeedback}
            sseFeed={sseFeed}
            loadingEval={loadingEval}
            onEvaluate={handleEvaluate}
            onRetryLoop={handleRetryLoopDemo}
            onCharge={handleCharge}
            onOpenPasskey={(ch) => setPasskeyModal(ch)}
          />
        )}

        {activeTab === 'mandates' && (
          <MandatesLedgerView
            state={state}
            mandateForm={mandateForm}
            setMandateForm={setMandateForm}
            signingMandate={signingMandate}
            tamperResults={tamperResults}
            onCreateMandate={handleCreateMandate}
            onVerifyTamper={handleVerifyTamper}
          />
        )}

        {activeTab === 'integrations' && (
          <IntegrationsView
            agentCard={agentCard}
            mcpPayload={mcpPayload}
            setMcpPayload={setMcpPayload}
            mcpResult={mcpResult}
            onRunMcp={handleRunMcp}
          />
        )}

        {activeTab === 'benchmarks' && (
          <BenchmarksLabView
            agents={state.agents}
            benchmark={benchmark}
            runningBench={runningBench}
            loadingEval={loadingEval}
            onRunBenchmarks={handleRunBenchmarks}
            onEvaluate={handleEvaluate}
          />
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
