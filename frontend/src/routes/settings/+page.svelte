<script lang="ts">
	import { onMount } from 'svelte';
	import { getCompanyId } from '$lib/api';

	let settings = $state<any>(null);
	let kbItems = $state<any[]>([]);
	let loading = $state(true);
	let saving = $state(false);
	let toast = $state('');

	// KB form
	let newKbTitle = $state('');
	let newKbContent = $state('');
	let kbFilter = $state('');

	const sources = ['', 'faq', 'manual', 'instagram', 'catalog', 'document', 'website', 'conversation'];

	onMount(async () => {
		const cid = getCompanyId();
		try {
			const [s, kb] = await Promise.all([
				fetch(`/api/settings/${cid}`).then(r => r.json()),
				fetch(`/api/settings/${cid}/knowledge-base`).then(r => r.json()),
			]);
			settings = s;
			kbItems = kb;
		} finally {
			loading = false;
		}
	});

	async function saveSettings() {
		if (!settings) return;
		saving = true;
		const cid = getCompanyId();
		try {
			await fetch(`/api/settings/${cid}`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					name: settings.name,
					business_type: settings.business_type,
					description: settings.description,
					timezone: settings.timezone,
					currency: settings.currency,
				}),
			});
			showToast('Configuracion guardada');
		} finally {
			saving = false;
		}
	}

	async function saveAIConfig() {
		if (!settings) return;
		saving = true;
		const cid = getCompanyId();
		try {
			await fetch(`/api/settings/${cid}/ai`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					ai_personality: settings.ai_personality,
					ai_language: settings.ai_language,
					ai_sales_goal: settings.ai_sales_goal,
					ai_custom_rules: settings.ai_custom_rules,
				}),
			});
			showToast('Configuracion IA guardada');
		} finally {
			saving = false;
		}
	}

	async function addKBItem() {
		if (!newKbTitle || !newKbContent) return;
		const cid = getCompanyId();
		await fetch(`/api/settings/${cid}/knowledge-base`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ title: newKbTitle, content: newKbContent }),
		});
		newKbTitle = '';
		newKbContent = '';
		kbItems = await fetch(`/api/settings/${cid}/knowledge-base`).then(r => r.json());
		showToast('Item agregado al KB');
	}

	async function deleteKBItem(id: string) {
		const cid = getCompanyId();
		await fetch(`/api/settings/${cid}/knowledge-base/${id}`, { method: 'DELETE' });
		kbItems = kbItems.filter(i => i.id !== id);
		showToast('Item desactivado');
	}

	function showToast(msg: string) {
		toast = msg;
		setTimeout(() => toast = '', 3000);
	}

	let filteredKB = $derived(kbFilter ? kbItems.filter(i => i.source === kbFilter) : kbItems);

	const sourceBadge: Record<string, string> = {
		faq: 'bg-blue-500/20 text-blue-400',
		manual: 'bg-green-500/20 text-green-400',
		instagram: 'bg-pink-500/20 text-pink-400',
		catalog: 'bg-yellow-500/20 text-yellow-400',
		document: 'bg-purple-500/20 text-purple-400',
		website: 'bg-cyan-500/20 text-cyan-400',
		conversation: 'bg-orange-500/20 text-orange-400',
	};
</script>

{#if toast}
	<div class="fixed top-4 right-4 z-50 bg-primary/20 border border-primary/30 text-primary px-4 py-2 rounded-lg text-sm backdrop-blur-xl">
		{toast}
	</div>
{/if}

<div class="p-6 space-y-6">
	<h2 class="text-2xl font-semibold">Configuracion</h2>

	{#if loading}
		<div class="text-white/50">Cargando...</div>
	{:else if settings}
		<!-- Company settings -->
		<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-5 space-y-4">
			<h3 class="text-sm font-medium text-white/60">Empresa</h3>
			<div class="grid grid-cols-2 gap-4">
				<div>
					<label class="text-xs text-white/40">Nombre</label>
					<input bind:value={settings.name} class="w-full mt-1 bg-surface-lighter border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-primary/50 focus:outline-none" />
				</div>
				<div>
					<label class="text-xs text-white/40">Tipo de negocio</label>
					<input bind:value={settings.business_type} class="w-full mt-1 bg-surface-lighter border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-primary/50 focus:outline-none" />
				</div>
				<div class="col-span-2">
					<label class="text-xs text-white/40">Descripcion (la IA usa esto)</label>
					<textarea bind:value={settings.description} rows="3" class="w-full mt-1 bg-surface-lighter border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-primary/50 focus:outline-none resize-none"></textarea>
				</div>
			</div>
			<div class="flex items-center gap-3">
				<span class="text-xs text-white/40">Canales:</span>
				<span class="text-xs px-2 py-1 rounded-full {settings.channels.whatsapp ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}">
					WhatsApp {settings.channels.whatsapp ? '✓' : '✕'}
				</span>
				<span class="text-xs px-2 py-1 rounded-full {settings.channels.instagram ? 'bg-pink-500/20 text-pink-400' : 'bg-gray-500/20 text-gray-400'}">
					Instagram {settings.channels.instagram ? '✓' : '✕'}
				</span>
			</div>
			<button onclick={saveSettings} disabled={saving} class="px-4 py-2 bg-primary hover:bg-primary-light text-black text-sm font-medium rounded-lg transition-colors disabled:opacity-50">
				{saving ? 'Guardando...' : 'Guardar cambios'}
			</button>
		</div>

		<!-- AI Config -->
		<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-5 space-y-4">
			<h3 class="text-sm font-medium text-white/60">Agente IA</h3>
			<div class="grid grid-cols-2 gap-4">
				<div class="col-span-2">
					<label class="text-xs text-white/40">Personalidad del bot</label>
					<textarea bind:value={settings.ai_personality} rows="2" class="w-full mt-1 bg-surface-lighter border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-primary/50 focus:outline-none resize-none"></textarea>
				</div>
				<div>
					<label class="text-xs text-white/40">Idioma</label>
					<input bind:value={settings.ai_language} class="w-full mt-1 bg-surface-lighter border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-primary/50 focus:outline-none" />
				</div>
				<div>
					<label class="text-xs text-white/40">Objetivo de ventas</label>
					<input bind:value={settings.ai_sales_goal} class="w-full mt-1 bg-surface-lighter border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-primary/50 focus:outline-none" />
				</div>
				<div class="col-span-2">
					<label class="text-xs text-white/40">Reglas custom (una por linea)</label>
					<textarea bind:value={settings.ai_custom_rules} rows="3" placeholder="Ej: No ofrecer descuentos sin aprobacion del gerente" class="w-full mt-1 bg-surface-lighter border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-primary/50 focus:outline-none resize-none"></textarea>
				</div>
			</div>
			<button onclick={saveAIConfig} disabled={saving} class="px-4 py-2 bg-accent hover:bg-yellow-400 text-black text-sm font-medium rounded-lg transition-colors disabled:opacity-50">
				{saving ? 'Guardando...' : 'Guardar config IA'}
			</button>
		</div>

		<!-- Knowledge Base -->
		<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-5 space-y-4">
			<div class="flex items-center justify-between">
				<h3 class="text-sm font-medium text-white/60">Knowledge Base ({kbItems.length} items)</h3>
				<select bind:value={kbFilter} class="bg-surface-lighter border border-white/10 rounded-lg px-2 py-1 text-xs">
					{#each sources as s}
						<option value={s}>{s || 'Todas las fuentes'}</option>
					{/each}
				</select>
			</div>

			<!-- Add KB item form -->
			<div class="bg-white/5 rounded-lg p-3 space-y-2">
				<input bind:value={newKbTitle} placeholder="Titulo (ej: Politica de devoluciones)" class="w-full bg-surface-lighter border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-primary/50 focus:outline-none" />
				<textarea bind:value={newKbContent} placeholder="Contenido..." rows="2" class="w-full bg-surface-lighter border border-white/10 rounded-lg px-3 py-2 text-sm focus:border-primary/50 focus:outline-none resize-none"></textarea>
				<button onclick={addKBItem} disabled={!newKbTitle || !newKbContent} class="px-3 py-1.5 bg-primary/20 text-primary text-xs rounded-lg hover:bg-primary/30 disabled:opacity-30">
					+ Agregar al KB
				</button>
			</div>

			<!-- KB items list -->
			<div class="divide-y divide-white/5">
				{#each filteredKB as item}
					<div class="py-3 flex items-start justify-between gap-3">
						<div class="flex-1 min-w-0">
							<div class="flex items-center gap-2">
								<span class="text-xs px-1.5 py-0.5 rounded {sourceBadge[item.source] || 'bg-gray-500/20 text-gray-400'}">{item.source}</span>
								<span class="text-sm font-medium truncate">{item.title}</span>
								{#if item.auto_generated}
									<span class="text-[10px] text-white/30">auto</span>
								{/if}
							</div>
							<p class="text-xs text-white/40 mt-1 line-clamp-2">{item.content}</p>
						</div>
						<button onclick={() => deleteKBItem(item.id)} class="text-xs text-red-400/50 hover:text-red-400 shrink-0">
							✕
						</button>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>
