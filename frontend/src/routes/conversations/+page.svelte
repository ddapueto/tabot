<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';

	let conversations = $state<any[]>([]);
	let selectedConv = $state<any>(null);
	let messages = $state<any[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			conversations = await api.getConversations({ limit: 50 });
		} finally {
			loading = false;
		}
	});

	async function selectConversation(conv: any) {
		selectedConv = conv;
		messages = await api.getMessages(conv.id);
	}

	function formatTime(iso: string) {
		return new Date(iso).toLocaleTimeString('es-UY', { hour: '2-digit', minute: '2-digit' });
	}
</script>

<div class="flex h-full">
	<!-- Conversation list -->
	<div class="w-80 border-r border-white/10 flex flex-col">
		<div class="p-4 border-b border-white/10">
			<h2 class="text-lg font-semibold">Conversaciones</h2>
		</div>
		<div class="flex-1 overflow-auto divide-y divide-white/5">
			{#each conversations as conv}
				<button
					onclick={() => selectConversation(conv)}
					class="w-full text-left px-4 py-3 hover:bg-white/5 transition-colors {selectedConv?.id === conv.id ? 'bg-white/10' : ''}"
				>
					<div class="flex items-center justify-between">
						<span class="text-sm font-medium">{conv.channel}</span>
						<span class="text-xs px-2 py-0.5 rounded-full {conv.ai_enabled ? 'bg-primary/20 text-primary' : 'bg-orange-500/20 text-orange-400'}">
							{conv.ai_enabled ? 'IA' : 'Humano'}
						</span>
					</div>
					<p class="text-xs text-white/40 mt-1">{conv.status} · {conv.topic || 'Sin tema'}</p>
				</button>
			{/each}
		</div>
	</div>

	<!-- Chat viewer -->
	<div class="flex-1 flex flex-col">
		{#if selectedConv}
			<div class="p-4 border-b border-white/10 flex justify-between items-center">
				<div>
					<h3 class="font-medium">Conversacion #{selectedConv.id.slice(0, 8)}</h3>
					<p class="text-xs text-white/40">{selectedConv.channel} · {selectedConv.status}</p>
				</div>
				<span class="text-xs px-2 py-1 rounded-full {selectedConv.ai_enabled ? 'bg-primary/20 text-primary' : 'bg-orange-500/20 text-orange-400'}">
					{selectedConv.ai_enabled ? '🤖 IA activa' : '👤 Modo humano'}
				</span>
			</div>

			<div class="flex-1 overflow-auto p-4 space-y-3">
				{#each messages as msg}
					<div class="flex {msg.direction === 'inbound' ? 'justify-start' : 'justify-end'}">
						<div class="max-w-[70%] rounded-2xl px-4 py-2 {msg.direction === 'inbound' ? 'bg-white/10 rounded-bl-none' : 'bg-primary/20 rounded-br-none'}">
							<p class="text-sm whitespace-pre-wrap">{msg.content || '(media)'}</p>
							<div class="flex items-center gap-2 mt-1">
								<span class="text-[10px] text-white/30">{formatTime(msg.created_at)}</span>
								{#if msg.sender_type === 'ai'}
									<span class="text-[10px] text-primary/60">🤖 {msg.ai_model || 'IA'}</span>
								{/if}
								{#if msg.ai_tools_used && msg.ai_tools_used.length > 0}
									<span class="text-[10px] text-accent/60">🔧 {msg.ai_tools_used.join(', ')}</span>
								{/if}
							</div>
						</div>
					</div>
				{/each}
			</div>
		{:else}
			<div class="flex-1 flex items-center justify-center text-white/30">
				Selecciona una conversacion
			</div>
		{/if}
	</div>
</div>
