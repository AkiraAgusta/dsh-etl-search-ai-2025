<script>
	export let value = '';
	export let placeholder = '';
	export let type = 'text';
	export let disabled = false;
	export let error = '';
	export let icon = null;
</script>

<div class="relative">
	{#if icon}
		<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
			<svelte:component this={icon} class="h-5 w-5 text-gray-400" />
		</div>
	{/if}
	
	<!-- Use separate inputs for different types -->
	{#if type === 'text'}
		<input
			type="text"
			{placeholder}
			{disabled}
			bind:value
			on:input
			on:change
			on:keydown
			on:focus
			on:blur
			class="input"
			class:pl-10={icon}
			class:border-red-500={error}
			class:focus:ring-red-200={error}
		/>
	{:else if type === 'email'}
		<input
			type="email"
			{placeholder}
			{disabled}
			bind:value
			on:input
			on:change
			on:keydown
			on:focus
			on:blur
			class="input"
			class:pl-10={icon}
			class:border-red-500={error}
			class:focus:ring-red-200={error}
		/>
	{:else if type === 'password'}
		<input
			type="password"
			{placeholder}
			{disabled}
			bind:value
			on:input
			on:change
			on:keydown
			on:focus
			on:blur
			class="input"
			class:pl-10={icon}
			class:border-red-500={error}
			class:focus:ring-red-200={error}
		/>
	{:else if type === 'number'}
		<input
			type="number"
			{placeholder}
			{disabled}
			bind:value
			on:input
			on:change
			on:keydown
			on:focus
			on:blur
			class="input"
			class:pl-10={icon}
			class:border-red-500={error}
			class:focus:ring-red-200={error}
		/>
	{:else}
		<!-- Fallback for any other type -->
		<input
			type="text"
			{placeholder}
			{disabled}
			bind:value
			on:input
			on:change
			on:keydown
			on:focus
			on:blur
			class="input"
			class:pl-10={icon}
			class:border-red-500={error}
			class:focus:ring-red-200={error}
		/>
	{/if}
	
	{#if error}
		<p class="mt-1 text-sm text-red-600">{error}</p>
	{/if}
</div>