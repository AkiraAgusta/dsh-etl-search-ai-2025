<script>
	import Badge from './Badge.svelte';
	
	export let options = []; // Array of strings or objects with {value, label}
	export let selected = []; // Array of selected values
	export let placeholder = 'Select options...';
	export let label = '';
	export let maxDisplay = 3; // Max tags to display before "+X more"
	
	let isOpen = false;
	let searchQuery = '';
	
	$: filteredOptions = searchQuery
		? options.filter(opt => {
				const optValue = typeof opt === 'string' ? opt : opt.label;
				return optValue.toLowerCase().includes(searchQuery.toLowerCase());
		  })
		: options;
	
	$: availableOptions = filteredOptions.filter(opt => {
		const optValue = typeof opt === 'string' ? opt : opt.value;
		return !selected.includes(optValue);
	});
	
	function toggleOption(option) {
		const value = typeof option === 'string' ? option : option.value;
		
		if (selected.includes(value)) {
			selected = selected.filter(s => s !== value);
		} else {
			selected = [...selected, value];
		}
	}
	
	function removeSelected(value) {
		selected = selected.filter(s => s !== value);
	}
	
	function clearAll() {
		selected = [];
	}
	
	function handleClickOutside(event) {
		if (!event.target.closest('.multi-select-container')) {
			isOpen = false;
		}
	}
	
	function getLabel(value) {
		const option = options.find(opt => 
			(typeof opt === 'string' ? opt : opt.value) === value
		);
		return typeof option === 'string' ? option : option?.label || value;
	}
</script>

<svelte:window on:click={handleClickOutside} />

<div class="multi-select-container">
	{#if label}
		<div class="block text-sm font-medium text-gray-700 mb-2">
			{label}
			{#if selected.length > 0}
				<span class="text-gray-500">({selected.length})</span>
			{/if}
		</div>
	{/if}
	
	<!-- Selected tags -->
	{#if selected.length > 0}
		<div class="flex flex-wrap gap-2 mb-2">
			{#each selected.slice(0, maxDisplay) as value}
				<Badge variant="primary" size="sm">
					{getLabel(value)}
					<button
						on:click={() => removeSelected(value)}
						class="ml-1 hover:text-primary-900"
					>
						<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</Badge>
			{/each}
			
			{#if selected.length > maxDisplay}
				<Badge variant="default" size="sm">
					+{selected.length - maxDisplay} more
				</Badge>
			{/if}
			
			<button
				on:click={clearAll}
				class="text-xs text-gray-500 hover:text-gray-700 underline"
			>
				Clear all
			</button>
		</div>
	{/if}
	
	<!-- Dropdown trigger -->
	<button
		on:click={() => (isOpen = !isOpen)}
		class="w-full px-3 py-2 text-left border border-gray-300 rounded-lg hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
	>
		<div class="flex items-center justify-between">
			<span class="text-gray-500 text-sm">
				{selected.length > 0 ? `${selected.length} selected` : placeholder}
			</span>
			<svg
				class="w-5 h-5 text-gray-400 transition-transform"
				class:rotate-180={isOpen}
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
			</svg>
		</div>
	</button>
	
	<!-- Dropdown menu -->
	{#if isOpen}
		<div class="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-64 overflow-hidden">
			<!-- Search input -->
			<div class="p-2 border-b border-gray-200">
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="Search..."
					class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
				/>
			</div>
			
			<!-- Options list -->
			<div class="overflow-y-auto max-h-48">
				{#if availableOptions.length > 0}
					{#each availableOptions as option}
						{@const value = typeof option === 'string' ? option : option.value}
						{@const label = typeof option === 'string' ? option : option.label}
						
						<button
							on:click={() => toggleOption(option)}
							class="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 flex items-center justify-between group"
						>
							<span class="text-gray-700">{label}</span>
							<svg class="w-4 h-4 text-primary-600 opacity-0 group-hover:opacity-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
							</svg>
						</button>
					{/each}
				{:else}
					<div class="px-3 py-4 text-sm text-gray-500 text-center">
						{searchQuery ? 'No results found' : 'No more options'}
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.multi-select-container {
		position: relative;
	}
</style>