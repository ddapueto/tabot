<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';

	let funnel = $state<any>(null);
	let responseTimes = $state<any>(null);
	let aiStats = $state<any>(null);
	let topProducts = $state<any>(null);
	let scoringDist = $state<any>(null);
	let leadsOverTime = $state<any>(null);
	let loading = $state(true);

	onMount(async () => {
		try {
			const results = await Promise.all([
				api.getAnalytics('conversion-funnel'),
				api.getAnalytics('response-times'),
				api.getAnalytics('ai-stats'),
				api.getAnalytics('top-products'),
				api.getAnalytics('scoring-distribution'),
				api.getAnalytics('leads-over-time'),
			]);
			[funnel, responseTimes, aiStats, topProducts, scoringDist, leadsOverTime] = results;
		} catch (e) {
			console.error('Error loading analytics:', e);
		} finally {
			loading = false;
		}
	});

	function formatSeconds(s: number): string {
		if (s < 60) return `${Math.round(s)}s`;
		if (s < 3600) return `${Math.round(s / 60)}min`;
		return `${(s / 3600).toFixed(1)}h`;
	}
</script>

<div class="p-6 space-y-6">
	<h2 class="text-2xl font-semibold">Analytics</h2>

	{#if loading}
		<div class="text-white/50">Cargando metricas...</div>
	{:else}
		<!-- Row 1: Key metrics -->
		<div class="grid grid-cols-4 gap-4">
			<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-4">
				<p class="text-xs text-white/50">Tasa de Conversion</p>
				<p class="text-3xl font-bold text-primary mt-1">{funnel?.conversion_rate || 0}%</p>
				<p class="text-xs text-white/30 mt-1">{funnel?.total_leads || 0} leads totales</p>
			</div>
			<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-4">
				<p class="text-xs text-white/50">Tiempo Respuesta Prom.</p>
				<p class="text-3xl font-bold text-primary mt-1">{formatSeconds(responseTimes?.avg_response_seconds || 0)}</p>
				<p class="text-xs text-white/30 mt-1">min {formatSeconds(responseTimes?.min_response_seconds || 0)} / max {formatSeconds(responseTimes?.max_response_seconds || 0)}</p>
			</div>
			<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-4">
				<p class="text-xs text-white/50">Mensajes IA</p>
				<p class="text-3xl font-bold text-accent mt-1">{aiStats?.ai_messages || 0}</p>
				<p class="text-xs text-white/30 mt-1">{aiStats?.ai_handle_rate || 0}% manejados por IA</p>
			</div>
			<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-4">
				<p class="text-xs text-white/50">Costo IA Estimado</p>
				<p class="text-3xl font-bold text-green-400 mt-1">${aiStats?.estimated_cost_usd?.toFixed(2) || '0.00'}</p>
				<p class="text-xs text-white/30 mt-1">{((aiStats?.total_tokens_in || 0) + (aiStats?.total_tokens_out || 0)).toLocaleString()} tokens</p>
			</div>
		</div>

		<!-- Row 2: Funnel + Scoring -->
		<div class="grid grid-cols-2 gap-4">
			<!-- Conversion funnel -->
			<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-4">
				<h3 class="text-sm font-medium text-white/60 mb-4">Funnel de Conversion</h3>
				{#if funnel?.funnel}
					<div class="space-y-2">
						{#each funnel.funnel as step}
							{@const maxCount = Math.max(...funnel.funnel.map((s: any) => s.count), 1)}
							{@const width = Math.max((step.count / maxCount) * 100, 4)}
							<div class="flex items-center gap-3">
								<span class="text-xs text-white/50 w-24 text-right capitalize">{step.stage}</span>
								<div class="flex-1 h-6 bg-white/5 rounded-full overflow-hidden">
									<div
										class="h-full rounded-full {step.stage === 'won' ? 'bg-emerald-500' : step.stage === 'lost' ? 'bg-red-500/50' : 'bg-primary/70'}"
										style="width: {width}%"
									></div>
								</div>
								<span class="text-sm font-mono w-8 text-right">{step.count}</span>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Scoring distribution -->
			<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-4">
				<h3 class="text-sm font-medium text-white/60 mb-4">Distribucion de Scores</h3>
				{#if scoringDist}
					{@const total = scoringDist.total || 1}
					<div class="space-y-3">
						<div class="flex items-center gap-3">
							<span class="text-xs w-20">🔴 Urgent</span>
							<div class="flex-1 h-8 bg-white/5 rounded-lg overflow-hidden">
								<div class="h-full bg-red-500/70 rounded-lg flex items-center px-2" style="width: {Math.max(scoringDist.urgent_76_100 / total * 100, 5)}%">
									<span class="text-xs font-bold">{scoringDist.urgent_76_100}</span>
								</div>
							</div>
						</div>
						<div class="flex items-center gap-3">
							<span class="text-xs w-20">🟠 High</span>
							<div class="flex-1 h-8 bg-white/5 rounded-lg overflow-hidden">
								<div class="h-full bg-orange-500/70 rounded-lg flex items-center px-2" style="width: {Math.max(scoringDist.high_51_75 / total * 100, 5)}%">
									<span class="text-xs font-bold">{scoringDist.high_51_75}</span>
								</div>
							</div>
						</div>
						<div class="flex items-center gap-3">
							<span class="text-xs w-20">🟡 Medium</span>
							<div class="flex-1 h-8 bg-white/5 rounded-lg overflow-hidden">
								<div class="h-full bg-yellow-500/70 rounded-lg flex items-center px-2" style="width: {Math.max(scoringDist.medium_26_50 / total * 100, 5)}%">
									<span class="text-xs font-bold">{scoringDist.medium_26_50}</span>
								</div>
							</div>
						</div>
						<div class="flex items-center gap-3">
							<span class="text-xs w-20">⚪ Low</span>
							<div class="flex-1 h-8 bg-white/5 rounded-lg overflow-hidden">
								<div class="h-full bg-gray-500/70 rounded-lg flex items-center px-2" style="width: {Math.max(scoringDist.low_0_25 / total * 100, 5)}%">
									<span class="text-xs font-bold">{scoringDist.low_0_25}</span>
								</div>
							</div>
						</div>
					</div>
				{/if}
			</div>
		</div>

		<!-- Row 3: Top products + AI Stats -->
		<div class="grid grid-cols-2 gap-4">
			<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-4">
				<h3 class="text-sm font-medium text-white/60 mb-3">Productos Mas Consultados</h3>
				{#if topProducts?.products}
					<div class="space-y-2">
						{#each topProducts.products as p}
							{@const maxM = Math.max(...topProducts.products.map((x: any) => x.mentions), 1)}
							<div class="flex items-center justify-between">
								<div class="flex-1">
									<p class="text-sm">{p.name}</p>
									<p class="text-xs text-white/40">{p.category} · ${p.price?.toLocaleString() || 'N/A'}</p>
								</div>
								<div class="flex items-center gap-2">
									<div class="w-20 h-2 bg-white/5 rounded-full overflow-hidden">
										<div class="h-full bg-primary rounded-full" style="width: {(p.mentions / maxM) * 100}%"></div>
									</div>
									<span class="text-xs font-mono text-white/50 w-6 text-right">{p.mentions}</span>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-4">
				<h3 class="text-sm font-medium text-white/60 mb-3">Rendimiento IA</h3>
				{#if aiStats}
					<div class="grid grid-cols-2 gap-4 text-sm">
						<div>
							<p class="text-white/40">Mensajes totales</p>
							<p class="text-xl font-bold">{aiStats.total_messages}</p>
						</div>
						<div>
							<p class="text-white/40">Tasa IA</p>
							<p class="text-xl font-bold text-primary">{aiStats.ai_handle_rate}%</p>
						</div>
						<div>
							<p class="text-white/40">Tokens entrada</p>
							<p class="text-lg font-mono">{aiStats.total_tokens_in.toLocaleString()}</p>
						</div>
						<div>
							<p class="text-white/40">Tokens salida</p>
							<p class="text-lg font-mono">{aiStats.total_tokens_out.toLocaleString()}</p>
						</div>
						<div>
							<p class="text-white/40">Mensajes humanos</p>
							<p class="text-lg">{aiStats.human_messages}</p>
						</div>
						<div>
							<p class="text-white/40">Costo estimado</p>
							<p class="text-lg text-green-400">${aiStats.estimated_cost_usd.toFixed(4)}</p>
						</div>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
