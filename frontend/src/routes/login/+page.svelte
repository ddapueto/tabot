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
			const result = mode === 'login'
				? await api.login(email, password, companyId)
				: await api.register({ email, password, name, company_id: companyId, role: 'admin' });
			setAuth(result.access_token, companyId);
			goto('/');
		} catch (e: any) {
			error = e.message || 'Error de autenticacion';
		} finally {
			loading = false;
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center bg-base relative overflow-hidden">
	<!-- Background glow -->
	<div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-accent/[0.03] rounded-full blur-3xl"></div>

	<div class="relative glass rounded-2xl p-8 w-full max-w-sm space-y-6 animate-fade-in">
		<div class="text-center">
			<div class="text-4xl mb-2">🤖</div>
			<h1 class="text-xl font-bold text-accent">Tabot</h1>
			<p class="text-xs text-zinc-500 mt-1">Asistente de ventas IA</p>
		</div>

		{#if error}
			<div class="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-2.5 text-sm text-red-400 animate-fade-in">
				{error}
			</div>
		{/if}

		<form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-3">
			{#if mode === 'register'}
				<div>
					<label class="text-[11px] text-zinc-500 font-medium uppercase tracking-wider">Nombre</label>
					<input bind:value={name} placeholder="Tu nombre" class="w-full mt-1 bg-elevated border border-white/[0.08] rounded-lg px-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-600 focus:border-accent/50 focus:outline-none transition-colors" />
				</div>
			{/if}
			<div>
				<label class="text-[11px] text-zinc-500 font-medium uppercase tracking-wider">Email</label>
				<input bind:value={email} type="email" placeholder="tu@empresa.com" class="w-full mt-1 bg-elevated border border-white/[0.08] rounded-lg px-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-600 focus:border-accent/50 focus:outline-none transition-colors" />
			</div>
			<div>
				<label class="text-[11px] text-zinc-500 font-medium uppercase tracking-wider">Password</label>
				<input bind:value={password} type="password" placeholder="••••••••" class="w-full mt-1 bg-elevated border border-white/[0.08] rounded-lg px-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-600 focus:border-accent/50 focus:outline-none transition-colors" />
			</div>
			<div>
				<label class="text-[11px] text-zinc-500 font-medium uppercase tracking-wider">Company ID</label>
				<input bind:value={companyId} class="w-full mt-1 bg-elevated border border-white/[0.08] rounded-lg px-4 py-2.5 text-[11px] text-zinc-500 placeholder-zinc-600 focus:border-accent/50 focus:outline-none transition-colors font-mono" />
			</div>
			<button type="submit" disabled={loading} class="w-full bg-accent hover:bg-accent-hover text-black font-semibold rounded-lg py-2.5 text-sm transition-all duration-150 disabled:opacity-50 hover:shadow-lg hover:shadow-accent/20 active:scale-[0.98]">
				{loading ? '...' : mode === 'login' ? 'Entrar' : 'Registrarse'}
			</button>
		</form>

		<p class="text-center text-xs text-zinc-500">
			{#if mode === 'login'}
				No tenes cuenta? <button onclick={() => mode = 'register'} class="text-accent hover:underline">Registrate</button>
			{:else}
				Ya tenes cuenta? <button onclick={() => mode = 'login'} class="text-accent hover:underline">Entrar</button>
			{/if}
		</p>
	</div>
</div>
