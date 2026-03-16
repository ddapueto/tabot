const BASE = '';

// TODO: Replace with actual company ID from auth
const COMPANY_ID = 'a0000000-0000-0000-0000-000000000001';

async function request(path: string, options?: RequestInit) {
	const res = await fetch(`${BASE}${path}`, {
		headers: { 'Content-Type': 'application/json', ...options?.headers },
		...options
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || 'Error de red');
	}
	return res.json();
}

export const api = {
	// Dashboard
	getStats: () => request(`/api/dashboard/${COMPANY_ID}/stats`),
	getRecentLeads: (limit = 10) => request(`/api/dashboard/${COMPANY_ID}/recent-leads?limit=${limit}`),

	// Leads
	getLeads: (params?: { stage?: string; priority?: string; limit?: number }) => {
		const qs = new URLSearchParams();
		if (params?.stage) qs.set('stage', params.stage);
		if (params?.priority) qs.set('priority', params.priority);
		if (params?.limit) qs.set('limit', String(params.limit));
		return request(`/api/leads/${COMPANY_ID}?${qs}`);
	},
	getLead: (id: string) => request(`/api/leads/${COMPANY_ID}/${id}`),
	updateLead: (id: string, data: Record<string, unknown>) =>
		request(`/api/leads/${COMPANY_ID}/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
	changeStage: (id: string, stage: string, reason?: string) =>
		request(`/api/leads/${COMPANY_ID}/${id}/stage`, {
			method: 'POST',
			body: JSON.stringify({ stage, reason })
		}),
	handoff: (id: string, reason: string) =>
		request(`/api/leads/${COMPANY_ID}/${id}/handoff`, {
			method: 'POST',
			body: JSON.stringify({ reason })
		}),
	reactivateAi: (id: string) =>
		request(`/api/leads/${COMPANY_ID}/${id}/reactivate-ai`, { method: 'POST' }),

	// Conversations
	getConversations: (params?: { status?: string; limit?: number }) => {
		const qs = new URLSearchParams();
		if (params?.status) qs.set('status', params.status);
		if (params?.limit) qs.set('limit', String(params.limit));
		return request(`/api/conversations/${COMPANY_ID}?${qs}`);
	},
	getConversation: (id: string) => request(`/api/conversations/${COMPANY_ID}/${id}`),
	getMessages: (conversationId: string) =>
		request(`/api/conversations/${COMPANY_ID}/${conversationId}/messages`),

	// Catalog
	getProducts: (category?: string) => {
		const qs = category ? `?category=${category}` : '';
		return request(`/api/catalog/${COMPANY_ID}${qs}`);
	},
	getProduct: (id: string) => request(`/api/catalog/${COMPANY_ID}/${id}`),
	createProduct: (data: Record<string, unknown>) =>
		request(`/api/catalog/${COMPANY_ID}`, { method: 'POST', body: JSON.stringify(data) }),
};
