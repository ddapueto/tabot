<script lang="ts">
	import { onMount } from 'svelte';
	import { getCompanyId } from '$lib/api';

	let sequences = $state<Record<string, any>>({});
	let followups = $state<any[]>([]);
	let loading = $state(true);

	const statusBadge: Record<string, string> = {
		pending: 'bg-yellow-500/20 text-yellow-400',
		sent: 'bg-green-500/20 text-green-400',
		cancelled: 'bg-gray-500/20 text-gray-400',
		skipped: 'bg-red-500/20 text-red-400',
		failed: 'bg-red-500/20 text-red-400',
	};

	onMount(async () => {
		const cid = getCompanyId();
		try {
			const [seqData, fuData] = await Promise.all([
				fetch(`/api/follow-ups/${cid}/sequences`).then(r => r.json()),
				fetch(`/api/follow-ups/${cid}/pending`).then(r => r.json()),
			]);
			sequences = seqData;
			followups = fuData;
		} finally {
			loading = false;
		}
	});

	function formatDate(iso: string) {
		return new Date(iso).toLocaleString('es-UY', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
	}
</script>

<div class="p-6 space-y-6">
	<h2 class="text-2xl font-semibold">Follow-ups</h2>

	{#if loading}
		<div class="text-white/50">Cargando...</div>
	{:else}
		<!-- Sequences -->
		<div>
			<h3 class="text-sm font-medium text-white/60 mb-3">Secuencias Disponibles</h3>
			<div class="grid grid-cols-2 gap-4">
				{#each Object.entries(sequences) as [key, seq]}
					<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-4">
						<div class="flex items-center justify-between mb-2">
							<h4 class="font-medium">{seq.name}</h4>
							<span class="text-xs text-white/40">{seq.steps_count} pasos</span>
						</div>
						<p class="text-sm text-white/50 mb-3">{seq.description}</p>
						<div class="space-y-1">
							{#each seq.steps as step, i}
								<div class="flex items-center gap-2 text-xs">
									<span class="w-5 h-5 rounded-full bg-primary/20 text-primary flex items-center justify-center font-mono">{i + 1}</span>
									<span class="text-white/40">+{step.delay_hours}h</span>
									<span class="text-white/60 truncate">{step.message.slice(0, 60)}...</span>
								</div>
							{/each}
						</div>
					</div>
				{/each}
			</div>
		</div>

		<!-- Active follow-ups -->
		<div>
			<h3 class="text-sm font-medium text-white/60 mb-3">Follow-ups Activos ({followups.length})</h3>
			{#if followups.length === 0}
				<div class="bg-white/5 border border-white/10 rounded-xl p-8 text-center">
					<p class="text-4xl mb-2">📬</p>
					<p class="text-white/40">No hay follow-ups programados</p>
					<p class="text-xs text-white/30 mt-1">Se crean automaticamente cuando un lead no responde</p>
				</div>
			{:else}
				<div class="bg-white/5 border border-white/10 rounded-xl divide-y divide-white/5">
					{#each followups as fu}
						<div class="px-4 py-3 flex items-center justify-between">
							<div class="flex-1">
								<div class="flex items-center gap-2">
									<span class="text-sm font-medium">{fu.sequence_key}</span>
									<span class="text-xs text-white/40">paso {fu.step_index + 1}</span>
								</div>
								<p class="text-xs text-white/50 mt-0.5 truncate max-w-md">{fu.message}</p>
							</div>
							<div class="flex items-center gap-3">
								<span class="text-xs text-white/30">{formatDate(fu.scheduled_at)}</span>
								<span class="text-xs px-2 py-0.5 rounded-full {statusBadge[fu.status] || 'bg-gray-500/20'}">{fu.status}</span>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{/if}
</div>
