<script>
	export let variant = 'primary'; // primary, secondary, outline
	export let size = 'md'; // sm, md, lg
	export let disabled = false;
	export let type = 'button';
	export let loading = false;
	export let fullWidth = false;

	let className = '';
	export { className as class };

	const variants = {
		primary: 'btn-primary',
		secondary: 'btn-secondary',
		outline: 'border border-primary-600 text-primary-600 hover:bg-primary-50'
	};

	const sizes = {
		sm: 'px-3 py-1.5 text-sm',
		md: 'px-4 py-2',
		lg: 'px-6 py-3 text-lg'
	};
</script>

<button
	{type}
	{disabled}
	on:click
	class="btn {variants[variant]} {sizes[size]} {fullWidth ? 'w-full' : ''} {className}"
	{...$$restProps}
	class:opacity-50={loading}
	class:cursor-wait={loading}
>
	{#if loading}
		<svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
			<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
			<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
		</svg>
	{/if}
	<slot />
</button>