<script lang="ts">
	import '../app.css';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { loadAuth, clearAuth } from '$lib/api';
	import { goto } from '$app/navigation';

	let { children } = $props();
	let isLoginPage = $derived(page.url.pathname.startsWith('/login'));

	const navItems = [
		{ href: '/', label: 'Dashboard', icon: '📊' },
		{ href: '/leads', label: 'Leads', icon: '👥' },
		{ href: '/conversations', label: 'Inbox', icon: '💬' },
		{ href: '/catalog', label: 'Catálogo', icon: '📦' },
		{ href: '/follow-ups', label: 'Follow-ups', icon: '📬' },
	];

	onMount(() => {
		if (!isLoginPage && !loadAuth()) {
			goto('/login');
		}
	});

	function logout() {
		clearAuth();
		goto('/login');
	}
</script>

{#if isLoginPage}
	{@render children()}
{:else}
	<div class="flex h-screen">
		<nav class="w-56 bg-surface-light border-r border-white/10 flex flex-col shrink-0">
			<div class="p-4 border-b border-white/10">
				<h1 class="text-xl font-bold text-primary">🤖 Tabot</h1>
				<p class="text-xs text-white/40 mt-1">Asistente de ventas IA</p>
			</div>
			<div class="flex-1 p-2 space-y-1">
				{#each navItems as item}
					{@const active = page.url.pathname === item.href || (item.href !== '/' && page.url.pathname.startsWith(item.href))}
					<a
						href={item.href}
						class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors {active ? 'bg-primary/10 text-primary font-medium' : 'text-white/60 hover:text-white hover:bg-white/5'}"
					>
						<span>{item.icon}</span>
						<span>{item.label}</span>
					</a>
				{/each}
			</div>
			<div class="p-3 border-t border-white/10">
				<button onclick={logout} class="w-full text-left text-xs text-white/30 hover:text-white/60 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors">
					Cerrar sesion
				</button>
			</div>
		</nav>

		<main class="flex-1 overflow-auto">
			{@render children()}
		</main>
	</div>
{/if}
