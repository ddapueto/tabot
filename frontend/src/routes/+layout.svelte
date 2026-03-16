<script lang="ts">
	import '../app.css';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { loadAuth, clearAuth } from '$lib/api';
	import { goto } from '$app/navigation';

	let { children } = $props();
	let isLoginPage = $derived(page.url.pathname.startsWith('/login'));
	let collapsed = $state(false);

	const navItems = [
		{ href: '/', label: 'Dashboard', icon: '📊', match: (p: string) => p === '/' },
		{ href: '/leads', label: 'Leads', icon: '👥', match: (p: string) => p.startsWith('/leads') },
		{ href: '/conversations', label: 'Inbox', icon: '💬', match: (p: string) => p.startsWith('/conversations'), badge: true },
		{ href: '/catalog', label: 'Catálogo', icon: '📦', match: (p: string) => p.startsWith('/catalog') },
		{ href: '/follow-ups', label: 'Follow-ups', icon: '📬', match: (p: string) => p.startsWith('/follow-ups') },
		{ href: '/analytics', label: 'Analytics', icon: '📈', match: (p: string) => p.startsWith('/analytics') },
		{ href: '/settings', label: 'Config', icon: '⚙️', match: (p: string) => p.startsWith('/settings') },
	];

	onMount(() => {
		if (!isLoginPage && !loadAuth()) goto('/login');
	});

	function logout() {
		clearAuth();
		goto('/login');
	}

	function handleKeydown(e: KeyboardEvent) {
		// Cmd+B to toggle sidebar
		if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
			e.preventDefault();
			collapsed = !collapsed;
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if isLoginPage}
	{@render children()}
{:else}
	<div class="flex h-screen overflow-hidden">
		<!-- Sidebar -->
		<nav
			class="bg-surface border-r border-white/[0.06] flex flex-col shrink-0 transition-all duration-250 ease-out"
			style="width: {collapsed ? '64px' : '220px'}"
		>
			<!-- Logo -->
			<div class="p-4 border-b border-white/[0.06] flex items-center gap-3 min-h-14">
				<button onclick={() => collapsed = !collapsed} class="text-xl shrink-0 hover:scale-110 transition-transform cursor-pointer" title="Cmd+B">
					🤖
				</button>
				{#if !collapsed}
					<div class="animate-fade-in">
						<h1 class="text-base font-semibold text-accent">Tabot</h1>
						<p class="text-[10px] text-zinc-500 -mt-0.5">Ventas con IA</p>
					</div>
				{/if}
			</div>

			<!-- Nav items -->
			<div class="flex-1 p-2 space-y-0.5">
				{#each navItems as item}
					{@const active = item.match(page.url.pathname)}
					<a
						href={item.href}
						class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-150 {active
							? 'bg-accent/10 text-accent font-medium'
							: 'text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04]'}"
						title={collapsed ? item.label : undefined}
					>
						<span class="text-base shrink-0 w-5 text-center">{item.icon}</span>
						{#if !collapsed}
							<span class="truncate">{item.label}</span>
						{/if}
					</a>
				{/each}
			</div>

			<!-- Footer -->
			<div class="p-2 border-t border-white/[0.06]">
				<button
					onclick={logout}
					class="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.04] transition-colors"
					title={collapsed ? 'Cerrar sesión' : undefined}
				>
					<span class="text-base shrink-0 w-5 text-center">🚪</span>
					{#if !collapsed}
						<span>Salir</span>
					{/if}
				</button>
			</div>
		</nav>

		<!-- Main -->
		<main class="flex-1 overflow-auto bg-base">
			{@render children()}
		</main>
	</div>
{/if}
