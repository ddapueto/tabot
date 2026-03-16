<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';

	let products = $state<any[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			products = await api.getProducts();
		} finally {
			loading = false;
		}
	});
</script>

<div class="p-6 space-y-6">
	<div class="flex items-center justify-between">
		<h2 class="text-2xl font-semibold">Catálogo</h2>
		<span class="text-sm text-white/40">{products.length} productos</span>
	</div>

	{#if loading}
		<div class="text-white/50">Cargando...</div>
	{:else}
		<div class="grid grid-cols-3 gap-4">
			{#each products as product}
				<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden">
					{#if product.image_urls && product.image_urls.length > 0}
						<div class="h-40 bg-white/5 flex items-center justify-center text-white/20">
							📷 {product.name}
						</div>
					{/if}
					<div class="p-4 space-y-2">
						<div class="flex items-center justify-between">
							<h3 class="font-medium">{product.name}</h3>
							<span class="text-xs px-2 py-0.5 rounded-full bg-white/10">{product.category || 'General'}</span>
						</div>
						<p class="text-sm text-white/60">{product.short_desc || product.description || ''}</p>
						{#if product.price}
							<p class="text-lg font-bold text-primary">${Number(product.price).toLocaleString()} {product.price_currency}</p>
						{:else}
							<p class="text-sm text-white/40">Consultar precio</p>
						{/if}
						{#if product.specs}
							<div class="flex flex-wrap gap-1">
								{#each Object.entries(product.specs) as [key, val]}
									<span class="text-[10px] px-1.5 py-0.5 bg-white/5 rounded text-white/50">{key}: {val}</span>
								{/each}
							</div>
						{/if}
						{#if product.features && product.features.length > 0}
							<div class="flex flex-wrap gap-1">
								{#each product.features.slice(0, 4) as feat}
									<span class="text-[10px] px-1.5 py-0.5 bg-primary/10 text-primary/70 rounded">✓ {feat}</span>
								{/each}
							</div>
						{/if}
						<div class="flex items-center gap-2 text-xs text-white/30 pt-1">
							<span class={product.is_active ? 'text-green-400' : 'text-red-400'}>
								{product.is_active ? '● Activo' : '● Inactivo'}
							</span>
							<span>{product.in_stock ? 'En stock' : 'Sin stock'}</span>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
