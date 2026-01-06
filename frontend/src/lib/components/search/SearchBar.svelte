<script>
	import Button from '../common/Button.svelte';
	
	export let value = '';
	export let placeholder = 'Search datasets...';
	export let loading = false;
	export let onSearch = () => {};
	export let large = false;
	
	function handleKeydown(event) {
		if (event.key === 'Enter' && value.trim()) {
			onSearch();
		}
	}
	
	function handleClear() {
		value = '';
	}
</script>

<div class="relative">
	<div class="relative">
		<!-- Search Icon -->
		<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
			<svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
			</svg>
		</div>
		
		<!-- Input -->
		<input
			type="text"
			{placeholder}
			bind:value
			on:keydown={handleKeydown}
			class="w-full pl-10 pr-20 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all"
			class:py-2={!large}
			class:py-4={large}
			class:text-base={!large}
			class:text-lg={large}
		/>
		
		<!-- Clear Button -->
		{#if value}
			<button
				on:click={handleClear}
				class="absolute inset-y-0 right-20 pr-3 flex items-center text-gray-400 hover:text-gray-600"
			>
				<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		{/if}
		
		<!-- Search Button -->
		<div class="absolute inset-y-0 right-0 flex items-center pr-2">
			<Button
				on:click={onSearch}
				disabled={!value.trim() || loading}
				{loading}
				size={large ? 'lg' : 'md'}
			>
				Search
			</Button>
		</div>
	</div>
</div>