<script lang="ts">
	import '../app.css';

	let { children } = $props();

	const navItems = [
		{ href: '/', label: 'Dashboard', icon: '📊' },
		{ href: '/leads', label: 'Leads', icon: '👥' },
		{ href: '/conversations', label: 'Conversaciones', icon: '💬' },
		{ href: '/catalog', label: 'Catálogo', icon: '📦' },
	];
</script>

<div class="flex h-screen">
	<nav class="w-56 bg-surface-light border-r border-white/10 flex flex-col">
		<div class="p-4 border-b border-white/10">
			<h1 class="text-xl font-bold text-primary">🤖 Tabot</h1>
			<p class="text-xs text-white/40 mt-1">Asistente de ventas IA</p>
		</div>
		<div class="flex-1 p-2 space-y-1">
			{#each navItems as item}
				<a
					href={item.href}
					class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-white/70 hover:text-white hover:bg-white/5 transition-colors"
				>
					<span>{item.icon}</span>
					<span>{item.label}</span>
				</a>
			{/each}
		</div>
		<div class="p-4 border-t border-white/10 text-xs text-white/30">
			Tabot v0.1.0
		</div>
	</nav>

	<main class="flex-1 overflow-auto">
		{@render children()}
	</main>
</div>
