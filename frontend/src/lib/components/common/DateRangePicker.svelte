<script>
	import { getDateRanges, formatDateRange, formatDateForAPI } from '$lib/utils/dateRange';
	
	export let startDate = null;
	export let endDate = null;
	export let label = 'Date Range';
	
	let isOpen = false;
	let selectedRange = 'custom';
	let tempStartDate = startDate;
	let tempEndDate = endDate;
	
	const predefinedRanges = getDateRanges();
	
	$: displayText = startDate || endDate
		? formatDateRange(startDate, endDate)
		: 'Select date range';
	
	function selectPredefinedRange(rangeKey) {
		const range = predefinedRanges[rangeKey];
		tempStartDate = range.start;
		tempEndDate = range.end;
		selectedRange = rangeKey;
	}
	
	function applyDateRange() {
		startDate = tempStartDate;
		endDate = tempEndDate;
		isOpen = false;
	}
	
	function clearDateRange() {
		startDate = null;
		endDate = null;
		tempStartDate = null;
		tempEndDate = null;
		selectedRange = 'custom';
		isOpen = false;
	}
	
	function handleClickOutside(event) {
		if (!event.target.closest('.date-range-container')) {
			isOpen = false;
			// Reset temp values if not applied
			tempStartDate = startDate;
			tempEndDate = endDate;
		}
	}
	
	function formatInputDate(date) {
		if (!date) return '';
		return formatDateForAPI(date);
	}
	
	function parseInputDate(dateString) {
		if (!dateString) return null;
		return new Date(dateString);
	}
</script>

<svelte:window on:click={handleClickOutside} />

<div class="date-range-container relative">
	<div class="block text-sm font-medium text-gray-700 mb-2">
		{label}
	</div>
	
	<!-- Trigger button -->
	<button
		on:click={() => (isOpen = !isOpen)}
		class="w-full px-3 py-2 text-left border border-gray-300 rounded-lg hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white"
	>
		<div class="flex items-center justify-between">
			<span class="text-sm" class:text-gray-500={!startDate && !endDate} class:text-gray-900={startDate || endDate}>
				{displayText}
			</span>
			<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
			</svg>
		</div>
	</button>
	
	<!-- Dropdown - Fixed z-index to appear above results -->
	{#if isOpen}
		<div class="absolute z-[100] mt-1 bg-white border border-gray-300 rounded-lg shadow-lg w-96">
			<div class="p-4">
				<!-- Predefined ranges -->
				<div class="mb-4">
					<h4 class="text-sm font-medium text-gray-700 mb-2">Quick Select</h4>
					<div class="grid grid-cols-2 gap-2">
						{#each Object.entries(predefinedRanges) as [key, range]}
							<button
								on:click={() => selectPredefinedRange(key)}
								class="px-3 py-2 text-sm rounded-md border transition-colors"
								class:border-primary-500={selectedRange === key}
								class:bg-primary-50={selectedRange === key}
								class:text-primary-700={selectedRange === key}
								class:border-gray-300={selectedRange !== key}
								class:hover:bg-gray-50={selectedRange !== key}
							>
								{range.label}
							</button>
						{/each}
					</div>
				</div>
				
				<!-- Custom date inputs -->
				<div class="mb-4">
					<h4 class="text-sm font-medium text-gray-700 mb-2">Custom Range</h4>
					<div class="grid grid-cols-2 gap-3">
						<div>
							<label for="start-date-input" class="block text-xs text-gray-600 mb-1">Start Date</label>
							<input
								id="start-date-input"
								type="date"
								value={formatInputDate(tempStartDate)}
								on:change={(e) => {
									tempStartDate = parseInputDate(e.target.value);
									selectedRange = 'custom';
								}}
								class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
							/>
						</div>
						<div>
							<label for="end-date-input" class="block text-xs text-gray-600 mb-1">End Date</label>
							<input
								id="end-date-input"
								type="date"
								value={formatInputDate(tempEndDate)}
								on:change={(e) => {
									tempEndDate = parseInputDate(e.target.value);
									selectedRange = 'custom';
								}}
								min={formatInputDate(tempStartDate)}
								class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
							/>
						</div>
					</div>
				</div>
				
				<!-- Actions -->
				<div class="flex items-center justify-between pt-3 border-t border-gray-200">
					<button
						on:click={clearDateRange}
						class="text-sm text-gray-600 hover:text-gray-800"
					>
						Clear
					</button>
					<div class="flex gap-2">
						<button
							on:click={() => {
								isOpen = false;
								tempStartDate = startDate;
								tempEndDate = endDate;
							}}
							class="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
						>
							Cancel
						</button>
						<button
							on:click={applyDateRange}
							class="px-4 py-2 text-sm bg-primary-600 text-white rounded-md hover:bg-primary-700"
						>
							Apply
						</button>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>