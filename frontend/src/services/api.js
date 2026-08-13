const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

function buildUrl(path) {
  if (!API_BASE) return path;
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE}${cleanPath}`;
}

let cachedToken = null;

export async function getAuthToken() {
  if (cachedToken) return cachedToken;

  try {
    const res = await fetch(buildUrl('/api/auth/dev-token'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subject: "dashboard-emr-user",
        facility_id: "FAC-IN-DELHI-01",
        scopes: ["terminology:read", "mapping:read", "fhir:translate", "audit:read"]
      })
    });
    if (!res.ok) throw new Error('Failed to fetch auth token');
    const data = await res.json();
    cachedToken = data.access_token;
    return cachedToken;
  } catch (err) {
    console.error("Auth token error:", err);
    return null;
  }
}

async function authFetch(url, options = {}) {
  const token = await getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers
  };

  const response = await fetch(buildUrl(url), { ...options, headers });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function fetchNamasteConcepts() {
  return authFetch('/api/namaste/concepts');
}

export async function fetchTm2Concepts() {
  return authFetch('/api/tm2/concepts');
}

export async function getConceptMapping(code) {
  return authFetch(`/api/namaste/concept/${encodeURIComponent(code)}/mapping`);
}

export async function translateFhir(parameters) {
  return authFetch('/fhir/$translate', {
    method: 'POST',
    body: JSON.stringify(parameters)
  });
}

export async function fetchAuditLogs() {
  return authFetch('/api/audit/logs');
}
