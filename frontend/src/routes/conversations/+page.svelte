<script lang="ts">
	import { onMount, onDestroy, tick } from 'svelte';
	import { api, connectSSE } from '$lib/api';
	import { formatTime, formatDate, formatRelative, initials, priorityConfig, channelConfig } from '$lib/utils';

	let conversations = $state<any[]>([]);
	let selectedConv = $state<any>(null);
	let messages = $state<any[]>([]);
	let messageInput = $state('');
	let loading = $state(true);
	let sending = $state(false);
	let chatContainer = $state<HTMLDivElement>(null!);
	let eventSource: EventSource | null = null;

	onMount(async () => {
		try {
			conversations = await api.getConversations({ limit: 50 });
		} finally {
			loading = false;
		}
		eventSource = connectSSE((event) => {
			if (event.type === 'new_message') {
				const idx = conversations.findIndex(c => c.id === event.conversation_id);
				if (idx >= 0) conversations = [conversations[idx], ...conversations.slice(0, idx), ...conversations.slice(idx + 1)];
				if (selectedConv && event.conversation_id === selectedConv.id) {
					messages = [...messages, event.message];
					scrollToBottom();
				}
			}
		});
	});

	onDestroy(() => eventSource?.close());

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
		const temp = { id: 'temp-' + Date.now(), direction: 'outbound', sender_type: 'human', content, created_at: new Date().toISOString(), _sending: true };
		messages = [...messages, temp];
		await tick();
		scrollToBottom();
		try {
			const result = await api.sendMessage(selectedConv.id, content);
			messages = messages.map(m => m.id === temp.id ? { ...result, direction: 'outbound', sender_type: 'human' } : m);
		} catch {
			messages = messages.map(m => m.id === temp.id ? { ...m, _failed: true, _sending: false } : m);
		} finally {
			sending = false;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
	}

	function scrollToBottom() {
		setTimeout(() => { if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight; }, 50);
	}
</script>

<div class="flex h-full">
	<!-- Col 1: Conversation list -->
	<div class="w-80 border-r border-white/[0.06] flex flex-col bg-surface shrink-0">
		<div class="px-4 py-3 border-b border-white/[0.06]">
			<h2 class="text-sm font-semibold text-zinc-300">Inbox</h2>
			<p class="text-[11px] text-zinc-600">{conversations.length} conversaciones</p>
		</div>

		<div class="flex-1 overflow-auto">
			{#if loading}
				<div class="p-3 space-y-2">
					{#each [1,2,3,4,5] as _}<div class="skeleton h-16 rounded-lg"></div>{/each}
				</div>
			{:else}
				{#each conversations as conv}
					{@const prio = priorityConfig[conv.lead_priority]}
					{@const ch = channelConfig[conv.channel]}
					<button
						onclick={() => selectConversation(conv)}
						class="w-full text-left px-4 py-3 border-b border-white/[0.03] transition-all duration-150 {selectedConv?.id === conv.id ? 'bg-accent/[0.06] border-l-2 border-l-accent' : 'hover:bg-white/[0.02]'}"
					>
						<div class="flex items-center gap-3">
							<div class="relative shrink-0">
								<div class="w-10 h-10 rounded-full bg-accent/15 flex items-center justify-center text-[11px] font-semibold text-accent">
									{initials(conv.lead_name)}
								</div>
								<span class="absolute -bottom-0.5 -right-0.5 text-[10px]">{ch?.icon || '💬'}</span>
							</div>
							<div class="flex-1 min-w-0">
								<div class="flex items-center justify-between">
									<span class="text-sm font-medium text-zinc-200 truncate">{conv.lead_name || 'Sin nombre'}</span>
									<span class="text-[10px] text-zinc-600 shrink-0">{formatRelative(conv.updated_at)}</span>
								</div>
								<div class="flex items-center gap-1.5 mt-0.5">
									<span class="w-1.5 h-1.5 rounded-full {prio?.dot || 'bg-zinc-600'} shrink-0"></span>
									<span class="text-[11px] text-zinc-500 truncate">{conv.lead_phone || conv.channel}</span>
									{#if !conv.ai_enabled}
										<span class="text-[9px] px-1 py-px bg-amber-500/15 text-amber-400 rounded shrink-0">manual</span>
									{/if}
								</div>
							</div>
							<span class="text-[11px] font-mono {prio?.text || 'text-zinc-600'} shrink-0">{conv.lead_score}</span>
						</div>
					</button>
				{/each}
				{#if conversations.length === 0}
					<div class="p-8 text-center animate-fade-in">
						<p class="text-3xl mb-2 opacity-30">💬</p>
						<p class="text-sm text-zinc-500">Sin conversaciones</p>
						<p class="text-[11px] text-zinc-600 mt-1">Esperando mensajes...</p>
					</div>
				{/if}
			{/if}
		</div>
	</div>

	<!-- Col 2: Chat -->
	<div class="flex-1 flex flex-col min-w-0">
		{#if selectedConv}
			<!-- Header -->
			<div class="px-5 py-3 border-b border-white/[0.06] flex items-center justify-between bg-surface">
				<div class="flex items-center gap-3">
					<div class="w-9 h-9 rounded-full bg-accent/15 flex items-center justify-center text-[11px] font-semibold text-accent">
						{initials(selectedConv.lead_name)}
					</div>
					<div>
						<p class="text-sm font-medium text-zinc-200">{selectedConv.lead_name || 'Sin nombre'}</p>
						<p class="text-[11px] text-zinc-500">{selectedConv.lead_phone || ''} · {selectedConv.channel}</p>
					</div>
				</div>
				<span class="text-[10px] px-2 py-1 rounded-full {selectedConv.ai_enabled ? 'bg-accent/10 text-accent border border-accent/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}">
					{selectedConv.ai_enabled ? '🤖 IA activa' : '👤 Manual'}
				</span>
			</div>

			<!-- Messages -->
			<div bind:this={chatContainer} class="flex-1 overflow-auto px-4 py-3 space-y-0.5" style="background: #0b0b12;">
				{#each messages as msg, i}
					{@const showDate = i === 0 || formatDate(msg.created_at) !== formatDate(messages[i-1]?.created_at)}
					{@const sameAuthor = i > 0 && messages[i-1].sender_type === msg.sender_type && messages[i-1].direction === msg.direction}

					{#if showDate}
						<div class="flex justify-center py-3">
							<span class="text-[10px] text-zinc-600 bg-white/[0.03] px-3 py-1 rounded-full">{formatDate(msg.created_at)}</span>
						</div>
					{/if}

					<div class="flex {msg.direction === 'inbound' ? 'justify-start' : 'justify-end'} {sameAuthor ? 'mt-0.5' : 'mt-2'}">
						<div class="max-w-[65%] px-3.5 py-2 {msg.direction === 'inbound' ? 'bubble-received' : msg.sender_type === 'ai' ? 'bubble-ai' : 'bubble-sent'} {msg._sending ? 'opacity-60' : ''} {msg._failed ? 'border border-red-500/30' : ''}">
							{#if msg.sender_type === 'ai' && !sameAuthor}
								<p class="text-[10px] text-accent/50 font-medium mb-0.5">🤖 Tabot IA</p>
							{:else if msg.sender_type === 'human' && msg.direction === 'outbound' && !sameAuthor}
								<p class="text-[10px] text-blue-400/50 font-medium mb-0.5">👤 Vendedor</p>
							{/if}
							<p class="text-[13.5px] leading-[19px] text-zinc-200 whitespace-pre-wrap">{msg.content || '(media)'}</p>
							<div class="flex items-center justify-end gap-1.5 mt-1 -mb-0.5">
								<span class="text-[10px] text-zinc-600">{formatTime(msg.created_at)}</span>
								{#if msg.direction === 'outbound'}
									<span class="text-[10px] {msg._sending ? 'text-zinc-600' : msg._failed ? 'text-red-400' : 'text-accent/40'}">
										{msg._sending ? '⏳' : msg._failed ? '✕' : '✓✓'}
									</span>
								{/if}
							</div>
						</div>
					</div>
				{/each}
			</div>

			<!-- Input -->
			<div class="px-4 py-3 border-t border-white/[0.06] bg-surface">
				<div class="flex items-end gap-2">
					<div class="flex-1 bg-elevated rounded-2xl px-4 py-2.5 border border-white/[0.06] focus-within:border-accent/30 transition-colors">
						<textarea
							bind:value={messageInput}
							onkeydown={handleKeydown}
							placeholder="Escribe un mensaje..."
							rows="1"
							class="w-full bg-transparent text-sm text-zinc-200 placeholder-zinc-600 resize-none focus:outline-none"
							style="max-height: 96px;"
						></textarea>
					</div>
					<button
						onclick={sendMessage}
						disabled={!messageInput.trim() || sending}
						class="w-10 h-10 rounded-full bg-accent flex items-center justify-center text-black transition-all duration-150 disabled:opacity-20 hover:bg-accent-hover hover:shadow-lg hover:shadow-accent/20 active:scale-95 shrink-0"
					>
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
					</button>
				</div>
			</div>
		{:else}
			<div class="flex-1 flex flex-col items-center justify-center gap-3 animate-fade-in">
				<div class="w-16 h-16 rounded-full bg-accent/[0.06] flex items-center justify-center">
					<span class="text-3xl opacity-40">💬</span>
				</div>
				<p class="text-sm text-zinc-400">Selecciona una conversacion</p>
				<p class="text-[11px] text-zinc-600">O espera un mensaje nuevo</p>
			</div>
		{/if}
	</div>

	<!-- Col 3: Contact panel -->
	{#if selectedConv}
		<div class="w-72 border-l border-white/[0.06] overflow-auto bg-surface shrink-0 animate-slide-in">
			<div class="p-5 text-center border-b border-white/[0.06]">
				<div class="w-16 h-16 rounded-full bg-accent/15 flex items-center justify-center text-xl font-bold text-accent mx-auto">
					{initials(selectedConv.lead_name)}
				</div>
				<p class="font-medium mt-3 text-zinc-200">{selectedConv.lead_name || 'Sin nombre'}</p>
				<p class="text-[11px] text-zinc-500 mt-0.5">{selectedConv.lead_phone || selectedConv.lead_instagram || ''}</p>
			</div>

			<div class="p-4 space-y-3">
				<!-- Score -->
				{#if selectedConv}
				{@const prio = priorityConfig[selectedConv.lead_priority]}
				<div class="bg-white/[0.02] rounded-lg p-3 border border-white/[0.04]">
					<p class="text-[10px] text-zinc-500 uppercase tracking-wider font-medium">Score</p>
					<div class="flex items-center gap-3 mt-1.5">
						<span class="text-3xl font-bold text-accent">{selectedConv.lead_score}</span>
						<div class="flex items-center gap-1.5">
							<span class="w-2 h-2 rounded-full {prio?.dot || ''}"></span>
							<span class="text-xs text-zinc-400 capitalize">{prio?.label || ''}</span>
						</div>
					</div>
				</div>
				{/if}

				<!-- Channel -->
				{#if selectedConv}
				{@const ch = channelConfig[selectedConv.channel]}
				<div class="bg-white/[0.02] rounded-lg p-3 border border-white/[0.04]">
					<p class="text-[10px] text-zinc-500 uppercase tracking-wider font-medium">Canal</p>
					<p class="text-sm mt-1.5">{ch?.icon} {ch?.label || selectedConv.channel}</p>
					<div class="flex items-center gap-2 mt-2">
						<span class="text-[10px] text-zinc-600">Estado: {selectedConv.status}</span>
						<span class="text-[10px] text-zinc-600">IA: {selectedConv.ai_enabled ? '✓' : '✕'}</span>
					</div>
				</div>
				{/if}

				<a href="/leads" class="block text-center text-[11px] px-3 py-2 bg-white/[0.03] hover:bg-white/[0.06] rounded-lg transition-colors text-zinc-400 hover:text-zinc-300 border border-white/[0.04]">
					Ver perfil completo →
				</a>
			</div>
		</div>
	{/if}
</div>
