<script lang="ts">
	import '../app.css';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { loadAuth, clearAuth } from '$lib/api';
	import { goto } from '$app/navigation';
	import { getThemes, getThemeKey, setTheme, initTheme } from '$lib/theme.svelte';

	let { children } = $props();
	let isLoginPage = $derived(page.url.pathname.startsWith('/login'));
	let collapsed = $state(false);
	let showThemePicker = $state(false);

	const navItems = [
		{ href: '/', label: 'Dashboard', icon: '📊', match: (p: string) => p === '/' },
		{ href: '/leads', label: 'Leads', icon: '👥', match: (p: string) => p.startsWith('/leads') },
		{ href: '/conversations', label: 'Inbox', icon: '💬', match: (p: string) => p.startsWith('/conversations') },
		{ href: '/catalog', label: 'Catálogo', icon: '📦', match: (p: string) => p.startsWith('/catalog') },
		{ href: '/follow-ups', label: 'Follow-ups', icon: '📬', match: (p: string) => p.startsWith('/follow-ups') },
		{ href: '/analytics', label: 'Analytics', icon: '📈', match: (p: string) => p.startsWith('/analytics') },
		{ href: '/settings', label: 'Config', icon: '⚙️', match: (p: string) => p.startsWith('/settings') },
	];

	const themes = getThemes();

	onMount(() => {
		initTheme();
		if (!isLoginPage && !loadAuth()) goto('/login');
	});

	function logout() { clearAuth(); goto('/login'); }

	function handleKeydown(e: KeyboardEvent) {
		if ((e.metaKey || e.ctrlKey) && e.key === 'b') { e.preventDefault(); collapsed = !collapsed; }
	}

	function pickTheme(key: string) {
		setTheme(key as any);
		showThemePicker = false;
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if isLoginPage}
	{@render children()}
{:else}
	<div class="flex h-screen overflow-hidden">
		<!-- Sidebar -->
		<nav
			class="bg-surface border-r border-theme-subtle flex flex-col shrink-0 transition-all duration-250 ease-out"
			style="width: {collapsed ? '64px' : '220px'}"
		>
			<div class="p-4 border-b border-theme-subtle flex items-center gap-3 min-h-14">
				<button onclick={() => collapsed = !collapsed} class="text-xl shrink-0 hover:scale-110 transition-transform cursor-pointer" title="Cmd+B">🤖</button>
				{#if !collapsed}
					<div class="animate-fade-in">
						<h1 class="text-base font-semibold" style="color: var(--color-accent)">Tabot</h1>
						<p class="text-[10px] text-tertiary -mt-0.5">Ventas con IA</p>
					</div>
				{/if}
			</div>

			<div class="flex-1 p-2 space-y-0.5 overflow-auto">
				{#each navItems as item}
					{@const active = item.match(page.url.pathname)}
					<a
						href={item.href}
						class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-150"
						style={active ? `background: var(--color-accent-muted); color: var(--color-accent); font-weight: 500;` : `color: var(--color-text-secondary);`}
						title={collapsed ? item.label : undefined}
					>
						<span class="text-base shrink-0 w-5 text-center">{item.icon}</span>
						{#if !collapsed}<span class="truncate">{item.label}</span>{/if}
					</a>
				{/each}
			</div>

			<!-- Theme Switcher + Logout -->
			<div class="p-2 border-t border-theme-subtle space-y-0.5">
				<!-- Theme button -->
				<div class="relative">
					<button
						onclick={() => showThemePicker = !showThemePicker}
						class="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-secondary hover:text-primary transition-colors"
						title={collapsed ? 'Cambiar tema' : undefined}
					>
						<span class="text-base shrink-0 w-5 text-center">🎨</span>
						{#if !collapsed}<span>Tema</span>{/if}
					</button>

					<!-- Theme picker popup -->
					{#if showThemePicker}
						<div class="absolute bottom-12 left-2 right-2 glass rounded-xl p-2 space-y-1 z-50 animate-fade-in" style="min-width: 180px;">
							{#each Object.entries(themes) as [key, theme]}
								{@const isActive = getThemeKey() === key}
								<button
									onclick={() => pickTheme(key)}
									class="w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all duration-150 flex items-center gap-3"
									style={isActive ? `background: var(--color-accent-muted); color: var(--color-accent);` : `color: var(--color-text-secondary);`}
								>
									<div class="flex gap-1 shrink-0">
										<span class="w-3 h-3 rounded-full" style="background: {theme.base}; border: 1px solid {theme.border};"></span>
										<span class="w-3 h-3 rounded-full" style="background: {theme.surface}; border: 1px solid {theme.border};"></span>
										<span class="w-3 h-3 rounded-full" style="background: {theme.elevated}; border: 1px solid {theme.border};"></span>
									</div>
									<div>
										<p class="font-medium text-xs">{theme.label}</p>
										<p class="text-[10px]" style="color: var(--color-text-tertiary);">{theme.desc}</p>
									</div>
									{#if isActive}
										<span class="ml-auto text-[10px]" style="color: var(--color-accent);">✓</span>
									{/if}
								</button>
							{/each}
						</div>
					{/if}
				</div>

				<button
					onclick={logout}
					class="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-tertiary hover:text-secondary transition-colors"
					title={collapsed ? 'Cerrar sesión' : undefined}
				>
					<span class="text-base shrink-0 w-5 text-center">🚪</span>
					{#if !collapsed}<span>Salir</span>{/if}
				</button>
			</div>
		</nav>

		<main class="flex-1 overflow-auto bg-base">
			{@render children()}
		</main>
	</div>
{/if}
