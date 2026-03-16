<script lang="ts">
	import { onMount, onDestroy, tick } from 'svelte';
	import { api, connectSSE, getCompanyId } from '$lib/api';

	let conversations = $state<any[]>([]);
	let selectedConv = $state<any>(null);
	let messages = $state<any[]>([]);
	let messageInput = $state('');
	let loading = $state(true);
	let sending = $state(false);
	let chatContainer = $state<HTMLDivElement>(null!);
	let eventSource: EventSource | null = null;

	const channelIcon: Record<string, string> = {
		whatsapp: '💬',
		instagram_dm: '📸',
		instagram_comment: '💬',
		web: '🌐',
	};

	const priorityDot: Record<string, string> = {
		urgent: 'bg-red-400',
		high: 'bg-orange-400',
		medium: 'bg-yellow-400',
		low: 'bg-gray-500',
	};

	onMount(async () => {
		try {
			conversations = await api.getConversations({ limit: 50 });
		} finally {
			loading = false;
		}

		// Connect SSE for real-time updates
		eventSource = connectSSE((event) => {
			if (event.type === 'new_message') {
				// Update conversation list (move to top)
				const idx = conversations.findIndex(c => c.id === event.conversation_id);
				if (idx >= 0) {
					conversations = [conversations[idx], ...conversations.slice(0, idx), ...conversations.slice(idx + 1)];
				}
				// Add message to current chat if it's the selected conversation
				if (selectedConv && event.conversation_id === selectedConv.id) {
					messages = [...messages, event.message];
					scrollToBottom();
				}
			}
		});
	});

	onDestroy(() => {
		eventSource?.close();
	});

	async function selectConversation(conv: any) {
		selectedConv = conv;
		messages = await api.getMessages(conv.id);
		await tick();
		scrollToBottom();
	}

	async function sendMessage() {
		if (!messageInput.trim() || !selectedConv || sending) return;
		const content = messageInput.trim();
		messageInput = '';
		sending = true;

		// Optimistic update
		const optimisticMsg = {
			id: 'temp-' + Date.now(),
			direction: 'outbound',
			sender_type: 'human',
			content,
			created_at: new Date().toISOString(),
			channel_status: 'sending',
		};
		messages = [...messages, optimisticMsg];
		await tick();
		scrollToBottom();

		try {
			const result = await api.sendMessage(selectedConv.id, content);
			// Replace optimistic with real
			messages = messages.map(m => m.id === optimisticMsg.id ? { ...optimisticMsg, ...result, channel_status: 'sent' } : m);
		} catch {
			// Mark as failed
			messages = messages.map(m => m.id === optimisticMsg.id ? { ...m, channel_status: 'failed' } : m);
		} finally {
			sending = false;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	}

	function scrollToBottom() {
		setTimeout(() => {
			if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
		}, 50);
	}

	function formatTime(iso: string) {
		return new Date(iso).toLocaleTimeString('es-UY', { hour: '2-digit', minute: '2-digit' });
	}

	function formatDate(iso: string) {
		const d = new Date(iso);
		const today = new Date();
		if (d.toDateString() === today.toDateString()) return 'Hoy';
		const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
		if (d.toDateString() === yesterday.toDateString()) return 'Ayer';
		return d.toLocaleDateString('es-UY', { day: 'numeric', month: 'short' });
	}
</script>

<div class="flex h-full">
	<!-- Column 1: Conversation list -->
	<div class="w-80 border-r border-white/10 flex flex-col bg-surface">
		<div class="p-4 border-b border-white/10">
			<h2 class="text-lg font-semibold">Inbox</h2>
			<p class="text-xs text-white/40 mt-0.5">{conversations.length} conversaciones</p>
		</div>
		<div class="flex-1 overflow-auto">
			{#each conversations as conv}
				<button
					onclick={() => selectConversation(conv)}
					class="w-full text-left px-4 py-3 border-b border-white/5 hover:bg-white/5 transition-colors {selectedConv?.id === conv.id ? 'bg-white/10 border-l-2 border-l-primary' : ''}"
				>
					<div class="flex items-center gap-3">
						<div class="relative">
							<div class="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-sm font-bold">
								{(conv.lead_name || '?')[0]}
							</div>
							<span class="absolute -bottom-0.5 -right-0.5 text-xs">{channelIcon[conv.channel] || '💬'}</span>
						</div>
						<div class="flex-1 min-w-0">
							<div class="flex items-center justify-between">
								<span class="text-sm font-medium truncate">{conv.lead_name || 'Sin nombre'}</span>
								<span class="text-[10px] text-white/30">{formatDate(conv.updated_at)}</span>
							</div>
							<div class="flex items-center gap-1.5 mt-0.5">
								<span class="w-2 h-2 rounded-full {priorityDot[conv.lead_priority] || 'bg-gray-500'}"></span>
								<span class="text-xs text-white/40 truncate">
									{conv.lead_phone || conv.lead_instagram || conv.channel}
								</span>
								{#if !conv.ai_enabled}
									<span class="text-[10px] px-1 py-0.5 bg-orange-500/20 text-orange-400 rounded">Humano</span>
								{/if}
							</div>
						</div>
						<span class="text-xs font-mono text-primary/70">{conv.lead_score}</span>
					</div>
				</button>
			{/each}
			{#if conversations.length === 0 && !loading}
				<div class="p-8 text-center">
					<p class="text-4xl mb-2">💬</p>
					<p class="text-sm text-white/40">No hay conversaciones</p>
					<p class="text-xs text-white/30 mt-1">Los mensajes aparecerán cuando los clientes escriban</p>
				</div>
			{/if}
		</div>
	</div>

	<!-- Column 2: Chat area -->
	<div class="flex-1 flex flex-col min-w-0">
		{#if selectedConv}
			<!-- Chat header -->
			<div class="px-4 py-3 border-b border-white/10 flex items-center justify-between bg-surface-light">
				<div class="flex items-center gap-3">
					<div class="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center font-bold">
						{(selectedConv.lead_name || '?')[0]}
					</div>
					<div>
						<p class="font-medium">{selectedConv.lead_name || 'Sin nombre'}</p>
						<p class="text-xs text-white/40">
							{selectedConv.lead_phone || selectedConv.lead_instagram || ''} · {selectedConv.channel}
						</p>
					</div>
				</div>
				<div class="flex items-center gap-2">
					<span class="text-xs px-2 py-1 rounded-full {selectedConv.ai_enabled ? 'bg-primary/20 text-primary' : 'bg-orange-500/20 text-orange-400'}">
						{selectedConv.ai_enabled ? '🤖 IA' : '👤 Humano'}
					</span>
				</div>
			</div>

			<!-- Messages -->
			<div bind:this={chatContainer} class="flex-1 overflow-auto p-4 space-y-1" style="background: #0b141a;">
				{#each messages as msg, i}
					{@const showDate = i === 0 || formatDate(msg.created_at) !== formatDate(messages[i-1]?.created_at)}
					{#if showDate}
						<div class="flex justify-center py-2">
							<span class="text-[11px] text-white/40 bg-white/5 px-3 py-1 rounded-full">{formatDate(msg.created_at)}</span>
						</div>
					{/if}
					<div class="flex {msg.direction === 'inbound' ? 'justify-start' : 'justify-end'}">
						<div class="max-w-[65%] px-3 py-1.5 {msg.direction === 'inbound' ? 'bg-[#202c33] rounded-tr-lg rounded-br-lg rounded-bl-lg' : msg.sender_type === 'ai' ? 'bg-[#005c4b] rounded-tl-lg rounded-br-lg rounded-bl-lg' : 'bg-[#1b4a3e] rounded-tl-lg rounded-br-lg rounded-bl-lg'}">
							{#if msg.sender_type === 'ai'}
								<p class="text-[10px] text-primary/60 mb-0.5">🤖 IA</p>
							{:else if msg.sender_type === 'human' && msg.direction === 'outbound'}
								<p class="text-[10px] text-blue-400/60 mb-0.5">👤 Vendedor</p>
							{/if}
							<p class="text-[14.2px] leading-[19px] text-[#e9edef] whitespace-pre-wrap">{msg.content || '(media)'}</p>
							<div class="flex items-center justify-end gap-1 mt-0.5">
								<span class="text-[11px] text-white/30">{formatTime(msg.created_at)}</span>
								{#if msg.direction === 'outbound'}
									{#if msg.channel_status === 'sending'}
										<span class="text-[11px] text-white/20">⏳</span>
									{:else if msg.channel_status === 'failed'}
										<span class="text-[11px] text-red-400">✕</span>
									{:else}
										<span class="text-[11px] text-white/30">✓✓</span>
									{/if}
								{/if}
							</div>
						</div>
					</div>
				{/each}
				{#if messages.length === 0}
					<div class="flex items-center justify-center h-full text-white/20">
						No hay mensajes en esta conversacion
					</div>
				{/if}
			</div>

			<!-- Message input -->
			<div class="px-4 py-3 border-t border-white/10 bg-surface-light">
				<div class="flex items-end gap-2">
					<div class="flex-1 bg-[#2a3942] rounded-xl px-4 py-2">
						<textarea
							bind:value={messageInput}
							onkeydown={handleKeydown}
							placeholder="Escribe un mensaje..."
							rows="1"
							class="w-full bg-transparent text-sm text-[#e9edef] placeholder-white/30 resize-none focus:outline-none"
							style="max-height: 100px;"
						></textarea>
					</div>
					<button
						onclick={sendMessage}
						disabled={!messageInput.trim() || sending}
						class="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-black hover:bg-primary-light transition-colors disabled:opacity-30"
					>
						➤
					</button>
				</div>
			</div>
		{:else}
			<div class="flex-1 flex flex-col items-center justify-center text-white/20 gap-3">
				<span class="text-6xl">💬</span>
				<p class="text-lg">Selecciona una conversacion</p>
				<p class="text-sm">O espera a que llegue un mensaje nuevo</p>
			</div>
		{/if}
	</div>

	<!-- Column 3: Contact panel (shows when conversation selected) -->
	{#if selectedConv}
		<div class="w-72 border-l border-white/10 overflow-auto bg-surface p-4 space-y-4">
			<div class="text-center">
				<div class="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center text-2xl font-bold mx-auto">
					{(selectedConv.lead_name || '?')[0]}
				</div>
				<p class="font-medium mt-2">{selectedConv.lead_name || 'Sin nombre'}</p>
				<p class="text-xs text-white/40">{selectedConv.lead_phone || selectedConv.lead_instagram || ''}</p>
			</div>

			<div class="bg-white/5 rounded-lg p-3 space-y-2">
				<h4 class="text-xs font-medium text-white/50">Scoring</h4>
				<div class="flex items-center gap-3">
					<span class="text-3xl font-bold text-primary">{selectedConv.lead_score}</span>
					<span class="text-xs capitalize px-2 py-0.5 rounded-full {
						selectedConv.lead_priority === 'urgent' ? 'bg-red-500/20 text-red-400' :
						selectedConv.lead_priority === 'high' ? 'bg-orange-500/20 text-orange-400' :
						selectedConv.lead_priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
						'bg-gray-500/20 text-gray-400'
					}">{selectedConv.lead_priority}</span>
				</div>
			</div>

			<div class="bg-white/5 rounded-lg p-3 space-y-2">
				<h4 class="text-xs font-medium text-white/50">Canal</h4>
				<p class="text-sm">{channelIcon[selectedConv.channel]} {selectedConv.channel}</p>
				<p class="text-xs text-white/40">Estado: {selectedConv.status}</p>
				<p class="text-xs text-white/40">IA: {selectedConv.ai_enabled ? 'Activa' : 'Pausada'}</p>
			</div>

			<div class="space-y-2">
				<a
					href="/leads"
					class="block w-full text-center text-xs px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
				>
					Ver perfil del lead →
				</a>
			</div>
		</div>
	{/if}
</div>
