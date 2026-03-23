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

export const api = {
	// Auth (no requiere token)
	login: (email: string, password: string, companyId: string) =>
		request('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password, company_id: companyId }) }),
	register: (data: { email: string; password: string; name: string; company_id: string; role?: string }) =>
		request('/api/auth/register', { method: 'POST', body: JSON.stringify(data) }),
	me: () => request('/api/auth/me'),

	// Dashboard (auth required — company_id from JWT)
	getStats: () => request('/api/dashboard/stats'),
	getRecentLeads: (limit = 10) => request(`/api/dashboard/recent-leads?limit=${limit}`),

	// Leads
	getLeads: (params?: { stage?: string; priority?: string; search?: string; limit?: number }) => {
		const qs = new URLSearchParams();
		if (params?.stage) qs.set('stage', params.stage);
		if (params?.priority) qs.set('priority', params.priority);
		if (params?.search) qs.set('search', params.search);
		if (params?.limit) qs.set('limit', String(params.limit));
		return request(`/api/leads/?${qs}`);
	},
	getLead: (id: string) => request(`/api/leads/${id}`),
	updateLead: (id: string, data: Record<string, unknown>) =>
		request(`/api/leads/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
	changeStage: (id: string, stage: string, reason?: string) =>
		request(`/api/leads/${id}/stage`, { method: 'POST', body: JSON.stringify({ stage, reason }) }),
	handoff: (id: string, reason: string) =>
		request(`/api/leads/${id}/handoff`, { method: 'POST', body: JSON.stringify({ reason }) }),
	reactivateAi: (id: string) =>
		request(`/api/leads/${id}/reactivate-ai`, { method: 'POST' }),

	// Conversations
	getConversations: (params?: { status?: string; limit?: number }) => {
		const qs = new URLSearchParams();
		if (params?.status) qs.set('status', params.status);
		if (params?.limit) qs.set('limit', String(params.limit));
		return request(`/api/conversations/?${qs}`);
	},
	getMessages: (conversationId: string) =>
		request(`/api/conversations/${conversationId}/messages`),
	sendMessage: (conversationId: string, content: string) =>
		request(`/api/conversations/${conversationId}/send`, {
			method: 'POST', body: JSON.stringify({ content }),
		}),

	// Catalog
	getProducts: (category?: string) =>
		request(`/api/catalog/${category ? `?category=${category}` : ''}`),

	// Analytics
	getAnalytics: (endpoint: string, days = 30) =>
		request(`/api/analytics/${endpoint}?days=${days}`),

	// Settings
	getSettings: () => request('/api/settings/'),
	updateSettings: (data: Record<string, unknown>) =>
		request('/api/settings/', { method: 'PATCH', body: JSON.stringify(data) }),
	updateAIConfig: (data: Record<string, unknown>) =>
		request('/api/settings/ai', { method: 'PATCH', body: JSON.stringify(data) }),
	getKBItems: (source?: string) =>
		request(`/api/kb/${source ? `?source=${source}` : ''}`),
	addKBItem: (data: { title: string; content: string; source?: string }) =>
		request('/api/kb/', { method: 'POST', body: JSON.stringify(data) }),
	deleteKBItem: (id: string) =>
		request(`/api/kb/${id}`, { method: 'DELETE' }),
	getKBHealth: () => request('/api/kb/health'),
	syncCatalog: () => request('/api/kb/sync-catalog', { method: 'POST' }),
};

// SSE — conversations use company_id in URL (no auth for SSE)
export function connectSSE(onEvent: (event: any) => void): EventSource | null {
	const id = _companyId;
	if (!id) return null;
	const es = new EventSource(`/api/conversations/${id}/events/stream`);
	es.onmessage = (e) => {
		try {
			const data = JSON.parse(e.data);
			if (data.type !== 'ping') onEvent(data);
		} catch { /* ignore */ }
	};
	return es;
}
