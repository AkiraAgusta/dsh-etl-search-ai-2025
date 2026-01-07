<script>
	export let variant = 'text'; // 'text', 'title', 'paragraph', 'card', 'circle'
	export let count = 1;
	export let height = null;
	export let width = null;
	
	const variants = {
		text: 'h-4 w-full',
		title: 'h-6 w-3/4',
		paragraph: 'h-4 w-full',
		card: 'h-48 w-full',
		circle: 'h-12 w-12 rounded-full'
	};
	
	$: classes = [
		'animate-pulse bg-gray-200 rounded',
		variants[variant],
		height ? `h-${height}` : '',
		width ? `w-${width}` : ''
	].filter(Boolean).join(' ');
</script>

{#if variant === 'paragraph'}
	<div class="space-y-2">
		{#each Array(count) as _, i}
			<div class={classes} style="width: {i === count - 1 ? '75%' : '100%'}"></div>
		{/each}
	</div>
{:else}
	{#each Array(count) as _}
		<div class={classes}></div>
	{/each}
{/if}

<style>
	@keyframes pulse {
		0%, 100% {
			opacity: 1;
		}
		50% {
			opacity: 0.5;
		}
	}
	
	.animate-pulse {
		animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
	}
</style>