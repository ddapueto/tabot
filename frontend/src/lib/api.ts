let _token: string | null = null;
let _companyId: string | null = null;

export function setAuth(token: string, companyId: string) {
	_token = token;
	_companyId = companyId;
	localStorage.setItem('tabot:token', token);
	localStorage.setItem('tabot:company_id', companyId);
}

export function loadAuth(): boolean {
	_token = localStorage.getItem('tabot:token');
	_companyId = localStorage.getItem('tabot:company_id');
	return !!_token && !!_companyId;
}

export function clearAuth() {
	_token = null;
	_companyId = null;
	localStorage.removeItem('tabot:token');
	localStorage.removeItem('tabot:company_id');
}

export function getCompanyId(): string {
	return _companyId || '';
}

async function request(path: string, options?: RequestInit) {
	const headers: Record<string, string> = { 'Content-Type': 'application/json' };
	if (_token) headers['Authorization'] = `Bearer ${_token}`;

	const res = await fetch(path, { headers, ...options });
	if (res.status === 401) {
		clearAuth();
		window.location.href = '/login';
		throw new Error('Sesion expirada');
	}
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || 'Error de red');
	}
	return res.json();
}

function cid() {
	return _companyId || 'a0000000-0000-0000-0000-000000000001';
}

export const api = {
	// Auth
	login: (email: string, password: string, companyId: string) =>
		request('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password, company_id: companyId }) }),
	register: (data: { email: string; password: string; name: string; company_id: string; role?: string }) =>
		request('/api/auth/register', { method: 'POST', body: JSON.stringify(data) }),
	me: () => request('/api/auth/me'),

	// Dashboard
	getStats: () => request(`/api/dashboard/${cid()}/stats`),
	getRecentLeads: (limit = 10) => request(`/api/dashboard/${cid()}/recent-leads?limit=${limit}`),

	// Leads
	getLeads: (params?: { stage?: string; priority?: string; limit?: number }) => {
		const qs = new URLSearchParams();
		if (params?.stage) qs.set('stage', params.stage);
		if (params?.priority) qs.set('priority', params.priority);
		if (params?.limit) qs.set('limit', String(params.limit));
		return request(`/api/leads/${cid()}?${qs}`);
	},
	getLead: (id: string) => request(`/api/leads/${cid()}/${id}`),
	updateLead: (id: string, data: Record<string, unknown>) =>
		request(`/api/leads/${cid()}/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
	changeStage: (id: string, stage: string, reason?: string) =>
		request(`/api/leads/${cid()}/${id}/stage`, { method: 'POST', body: JSON.stringify({ stage, reason }) }),
	handoff: (id: string, reason: string) =>
		request(`/api/leads/${cid()}/${id}/handoff`, { method: 'POST', body: JSON.stringify({ reason }) }),
	reactivateAi: (id: string) =>
		request(`/api/leads/${cid()}/${id}/reactivate-ai`, { method: 'POST' }),

	// Conversations
	getConversations: (params?: { status?: string; limit?: number }) => {
		const qs = new URLSearchParams();
		if (params?.status) qs.set('status', params.status);
		if (params?.limit) qs.set('limit', String(params.limit));
		return request(`/api/conversations/${cid()}?${qs}`);
	},
	getMessages: (conversationId: string) =>
		request(`/api/conversations/${cid()}/${conversationId}/messages`),
	sendMessage: (conversationId: string, content: string) =>
		request(`/api/conversations/${cid()}/${conversationId}/send`, {
			method: 'POST',
			body: JSON.stringify({ content }),
		}),

	// Catalog
	getProducts: (category?: string) => {
		const qs = category ? `?category=${category}` : '';
		return request(`/api/catalog/${cid()}${qs}`);
	},
};

// SSE real-time connection
export function connectSSE(onEvent: (event: any) => void): EventSource | null {
	const id = cid();
	if (!id) return null;

	const es = new EventSource(`/api/conversations/${id}/events/stream`);
	es.onmessage = (e) => {
		try {
			const data = JSON.parse(e.data);
			if (data.type !== 'ping') onEvent(data);
		} catch { /* ignore parse errors */ }
	};
	es.onerror = () => {
		// Auto-reconnect is built into EventSource
	};
	return es;
}
