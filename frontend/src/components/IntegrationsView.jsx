import React, { useState } from 'react';
import { Workflow, Terminal, Check, Copy, ArrowRight, Layers } from 'lucide-react';

const FLOW_NODES = [
  {
    id: 'human',
    step: '01',
    title: 'Human Treasury Owner',
    sub: 'Signs AP2 IntentMandate',
    detail:
      'Treasury owner funds the Operating Vault (₹18.4L) and signs scoped per-agent daily budgets + MCC allowlists using Ed25519 (POST /api/mandates).',
  },
  {
    id: 'mcp',
    step: '02',
    title: 'External AI Agent',
    sub: 'Calls MCP / A2A Card',
    detail:
      'Any framework (Claude Desktop, Cursor, Google ADK, LangGraph) discovers Numen via GET /.well-known/agent.json and calls POST /mcp -> request_scoped_card.',
  },
  {
    id: 'firewall',
    step: '03',
    title: 'Numen Causal Firewall',
    sub: 'CaMeL + AttriGuard + FinePrint',
    detail:
      'Smart Router routes clean infra to Gemini 2.5 Flash or escalates untrusted HTML/dense terms to Pro. Verifies World A vs World B causal drift & hidden clauses.',
  },
  {
    id: 'mint',
    step: '04',
    title: '60s Card Issuer',
    sub: 'Exact-Rupee Luhn PAN',
    detail:
      'Mints a single-use Luhn Visa PAN bound via HMAC-SHA256 to the exact rupee amount (±₹0.00), exact merchant, and 60s TTL (or raises 1-Tap Passkey escalation).',
  },
  {
    id: 'settle',
    step: '05',
    title: 'Merchant Settlement',
    sub: 'Settle & Auto-Shred',
    detail:
      'Merchant charges via /api/cards/{id}/charge (or settle_ephemeral_card). Overcharges (+₹1) fail immediately; valid charges settle and permanently shred the PAN.',
  },
];

const HONESTY_ROWS = [
  {
    layer: 'Agent Protocol (MCP & A2A)',
    live: 'Live GET /.well-known/agent.json + POST /mcp JSON-RPC 2.0 server.',
    prod: 'Same contract deployed behind Cloud Run IAM / OAuth.',
  },
  {
    layer: 'AP2 Mandate Crypto',
    live: 'Real Ed25519 keypairs + canonical SHA-256 verification (crypto_ap2.py).',
    prod: 'Google Cloud KMS / hardware security module + WebAuthn Passkeys.',
  },
  {
    layer: 'LLM & Causal Reasoning',
    live: 'Gemini 2.5 Flash/Pro router + deterministic engine (or live GEMINI_API_KEY).',
    prod: 'Vertex AI Gemini Enterprise endpoint.',
  },
  {
    layer: 'Card Issuing Rail',
    live: 'Local Issuing Sandbox (sandbox_mint.py) issuing Luhn PANs & HMAC locks.',
    prod: 'Drop-in adapter for Stripe Issuing, Marqeta, or RazorpayX JIT.',
  },
  {
    layer: 'Ledger & Event Stream',
    live: 'SQLite WAL ACID storage + live SSE (/api/stream).',
    prod: 'Cloud SQL PostgreSQL / Firestore + Cloud Pub/Sub.',
  },
];

const MCP_SNIPPET = `{
  "mcpServers": {
    "numen-treasury": {
      "url": "http://127.0.0.1:8000/mcp",
      "transport": "http"
    }
  }
}`;

export default function IntegrationsView({
  agentCard,
  mcpPayload,
  setMcpPayload,
  mcpResult,
  onRunMcp,
}) {
  const [selectedNode, setSelectedNode] = useState(FLOW_NODES[1]);
  const [copied, setCopied] = useState(false);

  const copySnippet = () => {
    navigator.clipboard?.writeText(MCP_SNIPPET);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#059669]">
          3-Cluster Architecture &amp; Integration Clarity
        </p>
        <h1 className="text-2xl font-extrabold tracking-tight text-[#0B1F16] mt-1">
          3-Cluster Agentic Quorum: Untrusted Browsing Isolated From Real Money
        </h1>
        <p className="text-sm text-[#526B5D] mt-1 max-w-3xl">
          Numen separates untrusted edge agents (Cluster 1) from multi-agent consensus verification (Cluster 2)
          and a Zero-LLM deterministic card-minting vault (Cluster 3).
        </p>
      </div>

      {/* 3-Cluster Agentic Topology */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="surface-card p-5 space-y-2">
          <div className="font-mono text-[10.5px] font-bold text-[#526B5D]">CLUSTER 1 · UNTRUSTED EDGE</div>
          <h2 className="text-sm font-extrabold text-[#0B1F16]">Edge Commerce Agents</h2>
          <p className="text-xs text-[#526B5D] leading-relaxed">
            DevOps, Procurement, Research, Claude Desktop, Cursor &amp; ADK agents discover Numen via{' '}
            <span className="font-mono text-[#0B1F16]">/.well-known/agent.json</span> and call{' '}
            <span className="font-mono text-[#0B1F16]">POST /mcp</span>. Hold zero raw PANs.
          </p>
        </div>
        <div className="surface-card p-5 border-[#A7F3D0] bg-[#ECFDF5]/60 space-y-2">
          <div className="font-mono text-[10.5px] font-bold text-[#059669]">CLUSTER 2 · CONSENSUS QUORUM</div>
          <h2 className="text-sm font-extrabold text-[#0B1F16]">Gemini Router + 4 Verifier Voters</h2>
          <p className="text-xs text-[#0B1F16] leading-relaxed">
            Smart Router (Flash fast-path vs. Pro deep reasoning) coordinates unanimous quorum across{' '}
            <b>Budget/Loop</b>, <b>CaMeL Provenance</b>, <b>AttriGuard Drift</b> &amp; <b>FinePrint/Homoglyph</b>.
          </p>
        </div>
        <div className="vault-card-metal p-5 text-white space-y-2">
          <div className="font-mono text-[10.5px] font-bold text-[#6EE7B7]">CLUSTER 3 · ZERO-LLM CUSTODY</div>
          <h2 className="text-sm font-extrabold text-white">Deterministic AP2 Vault &amp; 60s Mint</h2>
          <p className="text-xs text-white/80 leading-relaxed">
            No LLM ever executes inside Cluster 3. Deterministic Python signs Ed25519 mandates, mints 60s exact-rupee
            Luhn PANs (±₹0.00 lock), commits SQLite WAL &amp; auto-shreds after 1 charge.
          </p>
        </div>
      </div>

      {/* Interactive 5-Node End-to-End Flow */}
      <div className="surface-card p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-[#E2EBE5] pb-3">
          <div className="flex items-center gap-2">
            <Workflow className="w-4 h-4 text-[#059669]" />
            <h2 className="text-sm font-bold text-[#0B1F16]">End-to-End Integration Sequence (Click Any Step)</h2>
          </div>
          <span className="font-mono text-[10.5px] text-[#849B8E]">PROTOCOL CHAIN</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-2.5">
          {FLOW_NODES.map((n, idx) => {
            const active = selectedNode.id === n.id;
            return (
              <div key={n.id} className="flex items-center gap-2">
                <button
                  onClick={() => setSelectedNode(n)}
                  className={`flex-1 text-left rounded-xl border p-3.5 transition ${
                    active
                      ? 'bg-[#ECFDF5] border-[#059669]'
                      : 'bg-[#F7FAF8] border-[#E2EBE5] hover:bg-white'
                  }`}
                >
                  <div className="font-mono text-[10px] font-bold text-[#059669]">STEP {n.step}</div>
                  <div className="text-xs font-bold text-[#0B1F16] mt-1">{n.title}</div>
                  <div className="text-[11px] text-[#526B5D] mt-0.5">{n.sub}</div>
                </button>
                {idx < FLOW_NODES.length - 1 && (
                  <ArrowRight className="hidden md:block w-4 h-4 text-[#849B8E] shrink-0" />
                )}
              </div>
            );
          })}
        </div>

        <div className="rounded-xl bg-[#0D261C] text-white p-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="font-mono text-[10.5px] text-[#6EE7B7] font-semibold">
              SELECTED HOP · STEP {selectedNode.step} ({selectedNode.title.toUpperCase()})
            </div>
            <div className="text-xs sm:text-sm text-white/95 mt-1 leading-relaxed">{selectedNode.detail}</div>
          </div>
        </div>
      </div>

      {/* Live Today vs Production Adapters Table */}
      <div className="surface-card p-5 space-y-4">
        <div className="flex items-center gap-2 border-b border-[#E2EBE5] pb-3">
          <Layers className="w-4 h-4 text-[#059669]" />
          <h2 className="text-sm font-bold text-[#0B1F16]">Honest Component Boundary: Running Live vs. Production Adapters</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#E2EBE5] font-mono text-[10.5px] text-[#526B5D]">
                <th className="py-2.5 pr-4">SYSTEM LAYER</th>
                <th className="py-2.5 pr-4 text-[#059669]">RUNNING LIVE TODAY IN REPO</th>
                <th className="py-2.5">DROP-IN PRODUCTION ADAPTER</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2EBE5]">
              {HONESTY_ROWS.map((r) => (
                <tr key={r.layer} className="align-top">
                  <td className="py-3 pr-4 font-bold text-[#0B1F16] whitespace-nowrap">{r.layer}</td>
                  <td className="py-3 pr-4 text-[#0B1F16]">{r.live}</td>
                  <td className="py-3 text-[#526B5D]">{r.prod}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Interactive MCP Console + Live A2A Card & Client Snippet */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-7 surface-card p-5 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E2EBE5] pb-3">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-[#059669]" />
              <h2 className="text-sm font-bold text-[#0B1F16]">Live MCP JSON-RPC 2.0 Inspector (POST /mcp)</h2>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => onRunMcp({ jsonrpc: '2.0', id: 'list-1', method: 'tools/list' })}
                className="rounded-lg border border-[#E2EBE5] bg-[#F7FAF8] hover:bg-[#ECFDF5] px-3 py-1.5 text-xs font-semibold text-[#0B1F16]"
              >
                tools/list
              </button>
              <button
                onClick={() => onRunMcp(null)}
                className="rounded-lg bg-[#059669] hover:bg-[#047857] text-white px-3.5 py-1.5 text-xs font-semibold"
              >
                Call Tool Live
              </button>
            </div>
          </div>

          <textarea
            rows={9}
            value={mcpPayload}
            onChange={(e) => setMcpPayload(e.target.value)}
            className="w-full rounded-xl border border-[#E2EBE5] bg-[#F7FAF8] p-3 font-mono text-[11px] text-[#0B1F16]"
          />

          {mcpResult && (
            <pre className="rounded-xl bg-[#0D261C] text-[#D1FAE5] p-3.5 font-mono text-[11px] max-h-56 overflow-auto">
              {JSON.stringify(mcpResult, null, 2)}
            </pre>
          )}
        </div>

        <div className="lg:col-span-5 space-y-4">
          <div className="surface-card p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-[#0B1F16]">Connect Claude Desktop / Cursor</h2>
              <button
                onClick={copySnippet}
                className="inline-flex items-center gap-1 rounded-lg border border-[#E2EBE5] bg-[#F7FAF8] px-2.5 py-1 text-[11px] font-semibold text-[#0B1F16]"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-[#059669]" /> : <Copy className="w-3.5 h-3.5 text-[#526B5D]" />}
                {copied ? 'Copied' : 'Copy JSON'}
              </button>
            </div>
            <pre className="rounded-xl bg-[#F7FAF8] border border-[#E2EBE5] p-3 font-mono text-[11px] text-[#0B1F16] overflow-x-auto">
              {MCP_SNIPPET}
            </pre>
          </div>

          <div className="surface-card p-5 space-y-2.5">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-[#0B1F16]">A2A Discovery Card</h2>
              <span className="font-mono text-[10px] font-semibold text-[#059669]">
                GET /.well-known/agent.json
              </span>
            </div>
            <pre className="rounded-xl bg-[#F7FAF8] border border-[#E2EBE5] p-3 font-mono text-[10.5px] text-[#526B5D] max-h-60 overflow-auto">
              {agentCard ? JSON.stringify(agentCard, null, 2) : 'Loading A2A agent card...'}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
