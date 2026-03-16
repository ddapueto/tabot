<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { stageBadge, priorityConfig, initials, formatRelative } from '$lib/utils';

	let stats = $state<any>(null);
	let recentLeads = $state<any[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			[stats, recentLeads] = await Promise.all([api.getStats(), api.getRecentLeads(10)]);
		} catch (e) {
			console.error(e);
		} finally {
			loading = false;
		}
	});
</script>

<div class="p-6 space-y-6 max-w-7xl mx-auto">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h2 class="text-xl font-semibold">Dashboard</h2>
			<p class="text-sm text-zinc-500 mt-0.5">Resumen de actividad</p>
		</div>
	</div>

	{#if loading}
		<!-- Skeleton -->
		<div class="grid grid-cols-4 gap-4">
			{#each [1,2,3,4] as _}
				<div class="skeleton h-24 rounded-xl"></div>
			{/each}
		</div>
		<div class="skeleton h-32 rounded-xl"></div>
		<div class="skeleton h-64 rounded-xl"></div>
	{:else if stats}
		<!-- Stat cards -->
		<div class="grid grid-cols-4 gap-4 animate-fade-in">
			{#each [
				{ label: 'Total Leads', value: stats.total_leads, accent: true },
				{ label: 'Conversaciones', value: stats.total_conversations },
				{ label: 'Mensajes', value: stats.messages.total, sub: `${stats.messages.inbound} in · ${stats.messages.outbound} out` },
				{ label: 'Respuestas IA', value: stats.messages.ai_responses, glow: true },
			] as card}
				<div class="bg-surface border border-white/[0.06] rounded-xl p-5 transition-all duration-150 hover:border-white/[0.1] hover:-translate-y-0.5">
					<p class="text-xs text-zinc-500 font-medium uppercase tracking-wider">{card.label}</p>
					<p class="text-3xl font-bold mt-2 {card.accent ? 'text-accent' : card.glow ? 'text-emerald-400' : 'text-zinc-100'}">{card.value}</p>
					{#if card.sub}
						<p class="text-[11px] text-zinc-600 mt-1">{card.sub}</p>
					{/if}
				</div>
			{/each}
		</div>

		<!-- Pipeline -->
		{#if stats.leads_by_stage && Object.keys(stats.leads_by_stage).length > 0}
			<div class="bg-surface border border-white/[0.06] rounded-xl p-5 animate-fade-in">
				<h3 class="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-4">Pipeline de Ventas</h3>
				<div class="flex gap-2">
					{#each ['new','interested','qualified','negotiating','visiting','closing','won','lost'] as stage}
						{@const count = stats.leads_by_stage[stage] || 0}
						{#if count > 0}
							<div class="flex-1 text-center p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] transition-all hover:bg-white/[0.04]">
								<div class="text-lg font-bold text-zinc-200">{count}</div>
								<div class="text-[10px] text-zinc-500 capitalize mt-0.5">{stage}</div>
								<div class="w-full h-1 bg-white/[0.04] rounded-full mt-2">
									<div class="h-1 rounded-full bg-accent/60 transition-all" style="width: {stats.total_leads ? (count / stats.total_leads) * 100 : 0}%"></div>
								</div>
							</div>
						{/if}
					{/each}
				</div>
			</div>
		{/if}

		<!-- Priority + Recent leads -->
		<div class="grid grid-cols-5 gap-4 animate-fade-in">
			<!-- Priority breakdown -->
			<div class="col-span-2 bg-surface border border-white/[0.06] rounded-xl p-5">
				<h3 class="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-4">Por Prioridad</h3>
				<div class="space-y-3">
					{#each ['urgent','high','medium','low'] as p}
						{@const count = stats.leads_by_priority[p] || 0}
						{@const config = priorityConfig[p]}
						<div class="flex items-center gap-3">
							<div class="w-2 h-2 rounded-full {config.dot}"></div>
							<span class="text-sm text-zinc-400 w-16">{config.label}</span>
							<div class="flex-1 h-2 bg-white/[0.04] rounded-full overflow-hidden">
								<div class="h-full rounded-full {config.dot} transition-all duration-500" style="width: {(count / (stats.total_leads || 1)) * 100}%"></div>
							</div>
							<span class="text-sm font-mono text-zinc-400 w-6 text-right">{count}</span>
						</div>
					{/each}
				</div>
			</div>

			<!-- Recent leads -->
			<div class="col-span-3 bg-surface border border-white/[0.06] rounded-xl overflow-hidden">
				<div class="px-5 py-3 border-b border-white/[0.06]">
					<h3 class="text-xs font-medium text-zinc-500 uppercase tracking-wider">Leads Recientes</h3>
				</div>
				<div class="divide-y divide-white/[0.04]">
					{#each recentLeads as lead}
						{@const prio = priorityConfig[lead.priority]}
						<a href="/leads" class="flex items-center justify-between px-5 py-3 hover:bg-white/[0.02] transition-colors group">
							<div class="flex items-center gap-3">
								<div class="w-8 h-8 rounded-full bg-accent/15 flex items-center justify-center text-[11px] font-semibold text-accent">
									{initials(lead.name)}
								</div>
								<div>
									<p class="text-sm font-medium text-zinc-200 group-hover:text-white transition-colors">{lead.name || 'Sin nombre'}</p>
									<p class="text-[11px] text-zinc-600">{lead.source_channel || ''} · {formatRelative(lead.created_at)}</p>
								</div>
							</div>
							<div class="flex items-center gap-3">
								<span class="text-sm font-mono {prio?.text || 'text-zinc-500'}">{lead.score}</span>
								<span class="text-[10px] px-2 py-0.5 rounded-full border {stageBadge[lead.stage] || 'bg-zinc-500/10 text-zinc-500'}">{lead.stage}</span>
							</div>
						</a>
					{/each}
				</div>
			</div>
		</div>
	{/if}
</div>
