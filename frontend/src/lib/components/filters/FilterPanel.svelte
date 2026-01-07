<script>
	import { onMount } from 'svelte';
	import Card from '../common/Card.svelte';
	import Button from '../common/Button.svelte';
	import MultiSelect from '../common/MultiSelect.svelte';
	import DateRangePicker from '../common/DateRangePicker.svelte';
	import Badge from '../common/Badge.svelte';
	import { filters, resetFilters, activeFilterCount } from '$lib/stores/filters';
	import { statsAPI } from '$lib/api/stats';
	
	export let onApplyFilters = () => {};
	export let showApplyButton = true;
	export let autoApply = false;
	
	let stats = null;
	let loading = true;
	let isExpanded = true;
	
	// Filter options
	$: authorOptions = stats?.top_authors?.map(a => a.name) || [];
	$: organizationOptions = stats?.top_organizations?.map(o => o.name) || [];
	$: keywordOptions = stats?.top_keywords?.map(k => k.keyword) || [];
	$: formatOptions = stats?.metadata_formats ? Object.keys(stats.metadata_formats) : [];
	
	// Debug logging
	$: if (stats) {
		console.log('Stats loaded:', {
			hasTopAuthors: !!stats.top_authors,
			authorCount: stats.top_authors?.length || 0,
			hasTopOrgs: !!stats.top_organizations,
			orgCount: stats.top_organizations?.length || 0,
			hasTopKeywords: !!stats.top_keywords,
			keywordCount: stats.top_keywords?.length || 0,
			statsKeys: Object.keys(stats)
		});
	}
	
	onMount(async () => {
		try {
			stats = await statsAPI.stats();
		} catch (error) {
			console.error('Error loading filter options:', error);
		} finally {
			loading = false;
		}
	});
	
	// Auto-apply filters when they change
	$: if (autoApply && $filters) {
		onApplyFilters();
	}
	
	function handleReset() {
		resetFilters();
		if (autoApply) {
			onApplyFilters();
		}
	}
	
	function handleApply() {
		onApplyFilters();
	}
	
	function toggleExpanded() {
		isExpanded = !isExpanded;
	}
</script>

<Card>
	<!-- Header -->
	<div class="flex items-center justify-between mb-4">
		<div class="flex items-center gap-2">
			<h3 class="text-lg font-semibold text-gray-900">Filters</h3>
			{#if $activeFilterCount > 0}
				<Badge variant="primary" size="sm">
					{$activeFilterCount} active
				</Badge>
			{/if}
		</div>
		
		<div class="flex items-center gap-2">
			{#if $activeFilterCount > 0}
				<button
					on:click={handleReset}
					class="text-sm text-gray-600 hover:text-gray-800"
				>
					Clear all
				</button>
			{/if}
			
			<button
				on:click={toggleExpanded}
				class="p-1 hover:bg-gray-100 rounded"
				aria-label={isExpanded ? 'Collapse filters' : 'Expand filters'}
			>
				<svg
					class="w-5 h-5 text-gray-500 transition-transform"
					class:rotate-180={!isExpanded}
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
				>
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
				</svg>
			</button>
		</div>
	</div>
	
	<!-- Filter options -->
	{#if isExpanded}
		<div class="space-y-4">
			{#if loading}
				<div class="text-center py-8 text-gray-500">
					<svg class="animate-spin h-8 w-8 mx-auto mb-2" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
					</svg>
					Loading filter options...
				</div>
			{:else}
				<!-- Authors -->
				<div>
					<MultiSelect
						bind:selected={$filters.authors}
						options={authorOptions}
						label="Authors"
						placeholder="Select authors..."
						maxDisplay={2}
					/>
				</div>
				
				<!-- Organizations -->
				<div>
					<MultiSelect
						bind:selected={$filters.organizations}
						options={organizationOptions}
						label="Organizations"
						placeholder="Select organizations..."
						maxDisplay={2}
					/>
				</div>
				
				<!-- Keywords -->
				<div>
					<MultiSelect
						bind:selected={$filters.keywords}
						options={keywordOptions}
						label="Keywords"
						placeholder="Select keywords..."
						maxDisplay={3}
					/>
				</div>
				
				<!-- Date Range -->
				<div>
					<DateRangePicker
						bind:startDate={$filters.startDate}
						bind:endDate={$filters.endDate}
						label="Publication Date"
					/>
				</div>
				
				<!-- Formats -->
				<div>
					<div class="block text-sm font-medium text-gray-700 mb-2">
						Metadata Formats
						{#if $filters.formats.length > 0}
							<span class="text-gray-500">({$filters.formats.length})</span>
						{/if}
					</div>
					<div class="space-y-2">
						{#each formatOptions as format}
							<label class="flex items-center">
								<input
									type="checkbox"
									checked={$filters.formats.includes(format)}
									on:change={(e) => {
										if (e.target.checked) {
											$filters.formats = [...$filters.formats, format];
										} else {
											$filters.formats = $filters.formats.filter(f => f !== format);
										}
									}}
									class="h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
								/>
								<span class="ml-2 text-sm text-gray-700">{format}</span>
								{#if stats?.metadata_formats?.[format]}
									<span class="ml-auto text-xs text-gray-500">
										({stats.metadata_formats[format]})
									</span>
								{/if}
							</label>
						{/each}
					</div>
				</div>
				
				<!-- Apply button -->
				{#if showApplyButton && !autoApply}
					<div class="pt-4 border-t border-gray-200">
						<Button
							on:click={handleApply}
							class="w-full"
							disabled={$activeFilterCount === 0}
						>
							<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
							</svg>
							Apply Filters
						</Button>
					</div>
				{/if}
			{/if}
		</div>
	{/if}
</Card>