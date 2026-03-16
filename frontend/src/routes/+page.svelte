<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';

	let stats = $state<any>(null);
	let recentLeads = $state<any[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			[stats, recentLeads] = await Promise.all([
				api.getStats(),
				api.getRecentLeads(10)
			]);
		} catch (e) {
			console.error('Error loading dashboard:', e);
		} finally {
			loading = false;
		}
	});

	const stageBadge: Record<string, string> = {
		new: 'bg-blue-500/20 text-blue-400',
		interested: 'bg-green-500/20 text-green-400',
		qualified: 'bg-yellow-500/20 text-yellow-400',
		negotiating: 'bg-orange-500/20 text-orange-400',
		visiting: 'bg-purple-500/20 text-purple-400',
		closing: 'bg-red-500/20 text-red-400',
		won: 'bg-emerald-500/20 text-emerald-400',
		lost: 'bg-gray-500/20 text-gray-400',
	};

	const priorityColor: Record<string, string> = {
		urgent: 'text-red-400', high: 'text-orange-400', medium: 'text-yellow-400', low: 'text-gray-400',
	};
</script>

<div class="p-6 space-y-6">
	<h2 class="text-2xl font-semibold">Dashboard</h2>

	{#if loading}
		<div class="text-white/50">Cargando...</div>
	{:else if stats}
		<div class="grid grid-cols-4 gap-4">
			<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-4">
				<p class="text-sm text-white/50">Total Leads</p>
				<p class="text-3xl font-bold text-primary mt-1">{stats.total_leads}</p>
			</div>
			<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-4">
				<p class="text-sm text-white/50">Conversaciones</p>
				<p class="text-3xl font-bold text-primary mt-1">{stats.total_conversations}</p>
			</div>
			<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-4">
				<p class="text-sm text-white/50">Mensajes</p>
				<p class="text-3xl font-bold text-primary mt-1">{stats.messages.total}</p>
				<p class="text-xs text-white/40 mt-1">{stats.messages.inbound} in / {stats.messages.outbound} out</p>
			</div>
			<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-4">
				<p class="text-sm text-white/50">Respuestas IA</p>
				<p class="text-3xl font-bold text-accent mt-1">{stats.messages.ai_responses}</p>
			</div>
		</div>

		{#if stats.leads_by_stage && Object.keys(stats.leads_by_stage).length > 0}
		<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-4">
			<h3 class="text-sm font-medium text-white/60 mb-3">Pipeline de Ventas</h3>
			<div class="flex gap-2">
				{#each Object.entries(stats.leads_by_stage) as [stage, count]}
					<div class="flex-1 text-center p-2 rounded-lg bg-white/5">
						<div class="text-lg font-bold">{count}</div>
						<div class="text-xs text-white/50 capitalize">{stage}</div>
					</div>
				{/each}
			</div>
		</div>
		{/if}

		<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl">
			<div class="p-4 border-b border-white/10">
				<h3 class="text-sm font-medium text-white/60">Leads Recientes</h3>
			</div>
			<div class="divide-y divide-white/5">
				{#each recentLeads as lead}
					<a href="/leads" class="flex items-center justify-between px-4 py-3 hover:bg-white/5 transition-colors">
						<div class="flex items-center gap-3">
							<div class="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-sm font-bold">
								{(lead.name || '?')[0]}
							</div>
							<div>
								<p class="text-sm font-medium">{lead.name || 'Sin nombre'}</p>
								<p class="text-xs text-white/40">{lead.source_channel || ''}</p>
							</div>
						</div>
						<div class="flex items-center gap-3">
							<span class="text-sm font-mono {priorityColor[lead.priority] || ''}">{lead.score}</span>
							<span class="text-xs px-2 py-0.5 rounded-full {stageBadge[lead.stage] || 'bg-gray-500/20'}">{lead.stage}</span>
						</div>
					</a>
				{/each}
			</div>
		</div>
	{/if}
</div>
