const BASE = '';

async function req(url, opts = {}) {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    ...opts,
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  return data;
}

export const api = {
  getState: () => req('/api/state'),
  getHealth: () => req('/api/health'),
  getScenarios: () => req('/api/scenarios'),
  resetDemo: () => req('/api/reset', { method: 'POST' }),
  toggleAgent: (agentId) => req(`/api/agents/${agentId}/toggle-status`, { method: 'POST' }),
  createMandate: (payload) => req('/api/mandates', { method: 'POST', body: JSON.stringify(payload) }),
  evaluateSpend: (payload) => req('/api/spend/evaluate', { method: 'POST', body: JSON.stringify(payload) }),
  chargeCard: (cardId, payload) => req(`/api/cards/${cardId}/charge`, { method: 'POST', body: JSON.stringify(payload) }),
  resolvePasskey: (challengeId, action) =>
    req(`/api/passkeys/${challengeId}/resolve`, { method: 'POST', body: JSON.stringify({ action }) }),
  runBenchmarks: () => req('/api/benchmarks/run', { method: 'POST' }),
  callMcp: (payload) => req('/mcp', { method: 'POST', body: JSON.stringify(payload) }),
};
