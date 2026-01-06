<script>
	export let size = 'default'; // sm, default, lg, xl, full
	
	const sizes = {
		sm: 'max-w-3xl',
		default: 'max-w-5xl',
		lg: 'max-w-7xl',
		xl: 'max-w-screen-2xl',
		full: 'max-w-full'
	};
</script>

<div class="{sizes[size]} mx-auto px-4 sm:px-6 lg:px-8">
	<slot />
</div>