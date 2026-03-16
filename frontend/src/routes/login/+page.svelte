<script lang="ts">
	import { goto } from '$app/navigation';
	import { api, setAuth } from '$lib/api';

	let email = $state('');
	let password = $state('');
	let companyId = $state('a0000000-0000-0000-0000-000000000001');
	let error = $state('');
	let loading = $state(false);
	let mode = $state<'login' | 'register'>('login');
	let name = $state('');

	async function handleSubmit() {
		error = '';
		loading = true;
		try {
			let result;
			if (mode === 'login') {
				result = await api.login(email, password, companyId);
			} else {
				result = await api.register({ email, password, name, company_id: companyId, role: 'admin' });
			}
			setAuth(result.access_token, companyId);
			goto('/');
		} catch (e: any) {
			error = e.message || 'Error de autenticacion';
		} finally {
			loading = false;
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center bg-surface">
	<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 w-full max-w-sm space-y-6">
		<div class="text-center">
			<h1 class="text-2xl font-bold text-primary">🤖 Tabot</h1>
			<p class="text-sm text-white/40 mt-1">Asistente de ventas IA</p>
		</div>

		{#if error}
			<div class="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-2 text-sm text-red-400">
				{error}
			</div>
		{/if}

		<form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-4">
			{#if mode === 'register'}
				<input
					bind:value={name}
					placeholder="Nombre"
					class="w-full bg-surface-lighter border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-primary/50 focus:outline-none"
				/>
			{/if}
			<input
				bind:value={email}
				type="email"
				placeholder="Email"
				class="w-full bg-surface-lighter border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-primary/50 focus:outline-none"
			/>
			<input
				bind:value={password}
				type="password"
				placeholder="Password"
				class="w-full bg-surface-lighter border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-primary/50 focus:outline-none"
			/>
			<input
				bind:value={companyId}
				placeholder="Company ID"
				class="w-full bg-surface-lighter border border-white/10 rounded-lg px-4 py-2.5 text-xs text-white/40 focus:border-primary/50 focus:outline-none"
			/>
			<button
				type="submit"
				disabled={loading}
				class="w-full bg-primary hover:bg-primary-light text-black font-medium rounded-lg py-2.5 text-sm transition-colors disabled:opacity-50"
			>
				{loading ? 'Cargando...' : mode === 'login' ? 'Entrar' : 'Registrarse'}
			</button>
		</form>

		<p class="text-center text-xs text-white/40">
			{#if mode === 'login'}
				No tenes cuenta? <button onclick={() => mode = 'register'} class="text-primary hover:underline">Registrate</button>
			{:else}
				Ya tenes cuenta? <button onclick={() => mode = 'login'} class="text-primary hover:underline">Entrar</button>
			{/if}
		</p>
	</div>
</div>
