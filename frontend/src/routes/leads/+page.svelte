<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';

	let leads = $state<any[]>([]);
	let selectedLead = $state<any>(null);
	let filterStage = $state('');
	let loading = $state(true);

	const stages = ['', 'new', 'interested', 'qualified', 'negotiating', 'visiting', 'closing', 'won', 'lost'];

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

	const priorityIcon: Record<string, string> = {
		urgent: '🔴', high: '🟠', medium: '🟡', low: '⚪'
	};

	async function loadLeads() {
		loading = true;
		try {
			leads = await api.getLeads({ stage: filterStage || undefined, limit: 100 });
		} finally {
			loading = false;
		}
	}

	async function selectLead(lead: any) {
		selectedLead = await api.getLead(lead.id);
	}

	async function doHandoff() {
		if (!selectedLead) return;
		const reason = prompt('Razon del handoff:');
		if (!reason) return;
		await api.handoff(selectedLead.id, reason);
		await loadLeads();
		selectedLead = null;
	}

	async function doReactivateAi() {
		if (!selectedLead) return;
		await api.reactivateAi(selectedLead.id);
		selectedLead = await api.getLead(selectedLead.id);
	}

	onMount(loadLeads);

	$effect(() => {
		filterStage;
		loadLeads();
	});
</script>

<div class="flex h-full">
	<!-- Lead list -->
	<div class="w-96 border-r border-white/10 flex flex-col">
		<div class="p-4 border-b border-white/10 space-y-3">
			<h2 class="text-lg font-semibold">Leads</h2>
			<select bind:value={filterStage} class="w-full bg-surface-lighter border border-white/10 rounded-lg px-3 py-2 text-sm">
				{#each stages as s}
					<option value={s}>{s || 'Todos'}</option>
				{/each}
			</select>
		</div>
		<div class="flex-1 overflow-auto divide-y divide-white/5">
			{#each leads as lead}
				<button
					onclick={() => selectLead(lead)}
					class="w-full text-left px-4 py-3 hover:bg-white/5 transition-colors {selectedLead?.id === lead.id ? 'bg-white/10' : ''}"
				>
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-2">
							<span>{priorityIcon[lead.priority] || '⚪'}</span>
							<span class="text-sm font-medium">{lead.name || 'Sin nombre'}</span>
						</div>
						<span class="text-xs font-mono text-primary">{lead.score}</span>
					</div>
					<div class="flex items-center gap-2 mt-1">
						<span class="text-xs px-2 py-0.5 rounded-full {stageBadge[lead.stage] || ''}">{lead.stage}</span>
						<span class="text-xs text-white/30">{lead.source_channel || ''}</span>
					</div>
				</button>
			{/each}
			{#if leads.length === 0 && !loading}
				<p class="p-4 text-white/40 text-sm">No hay leads</p>
			{/if}
		</div>
	</div>

	<!-- Lead detail -->
	<div class="flex-1 p-6">
		{#if selectedLead}
			<div class="space-y-6">
				<div class="flex items-center justify-between">
					<div>
						<h2 class="text-xl font-semibold">{selectedLead.name || 'Sin nombre'}</h2>
						<p class="text-sm text-white/40 mt-1">
							{selectedLead.whatsapp_phone || selectedLead.instagram_username || selectedLead.email || 'Sin contacto'}
						</p>
					</div>
					<div class="flex gap-2">
						<button onclick={doHandoff} class="px-3 py-1.5 bg-orange-500/20 text-orange-400 rounded-lg text-sm hover:bg-orange-500/30">
							Handoff Humano
						</button>
						<button onclick={doReactivateAi} class="px-3 py-1.5 bg-primary/20 text-primary rounded-lg text-sm hover:bg-primary/30">
							Reactivar IA
						</button>
					</div>
				</div>

				<div class="grid grid-cols-2 gap-4">
					<div class="bg-white/5 rounded-xl p-4 space-y-3">
						<h3 class="text-sm font-medium text-white/60">Scoring</h3>
						<div class="flex items-center gap-4">
							<span class="text-4xl font-bold text-primary">{selectedLead.score}</span>
							<div>
								<p class="text-sm capitalize">{selectedLead.priority}</p>
								<p class="text-xs text-white/40">{selectedLead.stage}</p>
							</div>
						</div>
					</div>
					<div class="bg-white/5 rounded-xl p-4 space-y-3">
						<h3 class="text-sm font-medium text-white/60">Interes</h3>
						<div class="space-y-1 text-sm">
							{#if selectedLead.budget_range}
								<p>Presupuesto: {selectedLead.budget_range}</p>
							{/if}
							{#if selectedLead.timeline}
								<p>Timeline: {selectedLead.timeline}</p>
							{/if}
							{#if selectedLead.needs_summary}
								<p class="text-white/60">{selectedLead.needs_summary}</p>
							{/if}
							{#if !selectedLead.budget_range && !selectedLead.timeline}
								<p class="text-white/30">Sin datos de interes aun</p>
							{/if}
						</div>
					</div>
				</div>

				<div class="bg-white/5 rounded-xl p-4 space-y-2">
					<h3 class="text-sm font-medium text-white/60">Datos de contacto</h3>
					<div class="grid grid-cols-2 gap-2 text-sm">
						<p>Canal: <span class="text-white/70">{selectedLead.source_channel || '-'}</span></p>
						<p>Ciudad: <span class="text-white/70">{selectedLead.city || '-'}</span></p>
						<p>Email: <span class="text-white/70">{selectedLead.email || '-'}</span></p>
						<p>Telefono: <span class="text-white/70">{selectedLead.whatsapp_phone || '-'}</span></p>
					</div>
				</div>

				{#if selectedLead.tags && selectedLead.tags.length > 0}
					<div class="flex gap-1">
						{#each selectedLead.tags as tag}
							<span class="text-xs px-2 py-1 bg-white/10 rounded-full">{tag}</span>
						{/each}
					</div>
				{/if}
			</div>
		{:else}
			<div class="flex items-center justify-center h-full text-white/30">
				Selecciona un lead para ver detalles
			</div>
		{/if}
	</div>
</div>
