<script>
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import Container from '$lib/components/layout/Container.svelte';
	import SearchBar from '$lib/components/search/SearchBar.svelte';
	import ResultCard from '$lib/components/search/ResultCard.svelte';
	import FilterPanel from '$lib/components/filters/FilterPanel.svelte';
	import FilterChips from '$lib/components/filters/FilterChips.svelte';
	import Loading from '$lib/components/common/Loading.svelte';
	import Card from '$lib/components/common/Card.svelte';
	import Button from '$lib/components/common/Button.svelte';
	import { searchAPI } from '$lib/api/search';
	import { filters, buildFilterParams, hasActiveFilters, resetFilters } from '$lib/stores/filters';
	import { formatTime } from '$lib/utils/format';
	
	let searchQuery = '';
	let results = [];
	let loading = false;
	let error = null;
	let processingTime = 0;
	let hasSearched = false;
	let initialLoad = true;
	let showFilters = false;
	
	// Export functionality
	let exporting = false;
	
	// Load query from URL only on mount or navigation
	onMount(() => {
		// Reset filters first to clear any previous state
		resetFilters();
		
		// Check if there's a query in the URL and load it
		const urlQuery = $page.url.searchParams.get('q');
		if (urlQuery) {
			searchQuery = urlQuery;
			$filters.query = urlQuery;
			performSearch();
		}
		initialLoad = false;
	});
	
	// Watch for external navigation
	$: if (!initialLoad && $page.url.searchParams.get('q') !== searchQuery) {
		const urlQuery = $page.url.searchParams.get('q');
		if (urlQuery && !hasSearched) {
			searchQuery = urlQuery;
			$filters.query = urlQuery;
			performSearch();
		}
	}
	
	async function performSearch() {
		if (!searchQuery.trim() && !$hasActiveFilters) return;
		
		loading = true;
		error = null;
		hasSearched = true;
		
		try {
			// Use hybrid search if filters are active, otherwise semantic search
			let response;
			
			if ($hasActiveFilters) {
				// Build parameters for hybrid search
				const params = buildFilterParams($filters);
				params.query = searchQuery.trim();
				params.top_k = 20;			
				response = await searchAPI.hybrid(params);
			} else {
				// Simple semantic search
				response = await searchAPI.semantic(searchQuery.trim(), 20);
			}
			
			results = response.results;
			processingTime = response.processing_time_ms;
			
			// Update URL
			const url = new URL($page.url);
			url.searchParams.set('q', searchQuery);
			goto(url, { replaceState: true, noScroll: true });
		} catch (err) {
			error = err.message;
			results = [];
		} finally {
			loading = false;
		}
	}
	
	function handleSearch() {
		hasSearched = false;
		$filters.query = searchQuery;
		performSearch();
	}
	
	function handleApplyFilters() {
		hasSearched = false;
		performSearch();
	}
	
	function toggleFilters() {
		showFilters = !showFilters;
	}
	
	async function exportResults() {
		if (results.length === 0) return;
		
		exporting = true;
		try {
			// Create CSV content
			const headers = ['Rank', 'Title', 'File ID', 'Score', 'Abstract', 'Publication Date', 'Keywords'];
			const rows = results.map((result, i) => [
				i + 1,
				result.title,
				result.file_identifier,
				result.similarity_score ? (result.similarity_score * 100).toFixed(1) + '%' : 'N/A',
				result.abstract?.replace(/"/g, '""') || '',
				result.publication_date || '',
				result.keywords?.join('; ') || ''
			]);
			
			const csvContent = [
				headers.join(','),
				...rows.map(row => row.map(cell => `"${cell}"`).join(','))
			].join('\n');
			
			// Create download
			const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
			const link = document.createElement('a');
			const url = URL.createObjectURL(blob);
			link.setAttribute('href', url);
			link.setAttribute('download', `search-results-${new Date().toISOString().split('T')[0]}.csv`);
			link.style.visibility = 'hidden';
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
		} catch (err) {
			console.error('Export error:', err);
			alert('Failed to export results');
		} finally {
			exporting = false;
		}
	}
</script>

<svelte:head>
	<title>Search - CEH Dataset Discovery</title>
</svelte:head>

<div class="py-8">
	<Container size="lg">
		<div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
			<!-- Filter sidebar (desktop) -->
			<div class="hidden lg:block">
				<div class="sticky top-24 z-10">
					<FilterPanel onApplyFilters={handleApplyFilters} showApplyButton={true} />
				</div>
			</div>
			
			<!-- Main content -->
			<div class="lg:col-span-3 relative z-0">
				<!-- Search Bar -->
				<div class="mb-6">
					<SearchBar
						bind:value={searchQuery}
						onSearch={handleSearch}
						{loading}
					/>
				</div>
				
				<!-- Mobile filter toggle -->
				<div class="lg:hidden mb-4">
					<Button
						on:click={toggleFilters}
						variant="secondary"
						class="w-full"
					>
						<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
						</svg>
						Filters
						{#if $hasActiveFilters}
							<span class="ml-1">({$filters.authors.length + $filters.organizations.length + $filters.keywords.length + $filters.formats.length + ($filters.startDate || $filters.endDate ? 1 : 0)})</span>
						{/if}
					</Button>
					
					{#if showFilters}
						<div class="mt-4">
							<FilterPanel onApplyFilters={handleApplyFilters} showApplyButton={true} />
						</div>
					{/if}
				</div>
				
				<!-- Filter chips -->
				{#if $hasActiveFilters}
					<div class="mb-6">
						<FilterChips />
					</div>
				{/if}
				
				<!-- Results Header -->
				{#if hasSearched && !loading}
					<div class="mb-6">
						<div class="flex items-center justify-between flex-wrap gap-4">
							<div>
								<h2 class="text-xl font-semibold text-gray-900">
									Search Results
								</h2>
								<p class="text-sm text-gray-600 mt-1">
									Found {results.length} {results.length === 1 ? 'dataset' : 'datasets'}
									{#if processingTime}
										<span class="text-gray-400">• {formatTime(processingTime)}</span>
									{/if}
									{#if $hasActiveFilters}
										<span class="text-primary-600">• Filtered</span>
									{/if}
								</p>
							</div>
							
							{#if results.length > 0}
								<Button
									on:click={exportResults}
									variant="secondary"
									size="sm"
									loading={exporting}
								>
									<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
									</svg>
									Export CSV
								</Button>
							{/if}
						</div>
					</div>
				{/if}
				
				<!-- Loading State -->
				{#if loading}
					<div class="py-16">
						<Loading text="Searching datasets..." size="lg" />
					</div>
				
				<!-- Error State -->
				{:else if error}
					<Card>
						<div class="text-center py-8">
							<svg class="w-12 h-12 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							<h3 class="text-lg font-semibold text-gray-900 mb-2">Search Error</h3>
							<p class="text-gray-600 mb-4">{error}</p>
							<Button on:click={performSearch}>
								Try Again
							</Button>
						</div>
					</Card>
				
				<!-- No Results -->
				{:else if hasSearched && results.length === 0}
					<Card>
						<div class="text-center py-12">
							<svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							<h3 class="text-xl font-semibold text-gray-900 mb-2">No Results Found</h3>
							<p class="text-gray-600 mb-6">
								No datasets found for <strong>"{searchQuery}"</strong>
								{#if $hasActiveFilters}
									<br />with the applied filters
								{/if}
							</p>
							<div class="space-y-2 text-sm text-gray-600 max-w-md mx-auto">
								<p>Try:</p>
								<ul class="list-disc list-inside text-left">
									<li>Using different keywords</li>
									<li>Removing some filters</li>
									<li>Using more general terms</li>
									<li>Checking for typos</li>
								</ul>
							</div>
						</div>
					</Card>
				
				<!-- Results List -->
				{:else if results.length > 0}
					<div class="space-y-4">
						{#each results as result, i}
							<ResultCard {result} rank={i + 1} />
						{/each}
					</div>
				
				<!-- Initial State -->
				{:else if !hasSearched}
					<Card>
						<div class="text-center py-12">
							<svg class="w-16 h-16 text-primary-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
							</svg>
							<h3 class="text-xl font-semibold text-gray-900 mb-2">Start Searching</h3>
							<p class="text-gray-600 mb-6">
								Enter a search query and optionally apply filters for more precise results
							</p>
							<div class="space-y-2 text-sm text-gray-600 max-w-md mx-auto">
								<p class="font-medium">Example searches:</p>
								<div class="flex flex-wrap justify-center gap-2">
									<button
										on:click={() => { searchQuery = 'soil carbon content'; performSearch(); }}
										class="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-sm"
									>
										soil carbon content
									</button>
									<button
										on:click={() => { searchQuery = 'water quality monitoring'; performSearch(); }}
										class="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-sm"
									>
										water quality monitoring
									</button>
									<button
										on:click={() => { searchQuery = 'biodiversity surveys'; performSearch(); }}
										class="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-sm"
									>
										biodiversity surveys
									</button>
								</div>
							</div>
						</div>
					</Card>
				{/if}
			</div>
		</div>
	</Container>
</div>