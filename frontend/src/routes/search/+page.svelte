<script>
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import Container from '$lib/components/layout/Container.svelte';
	import SearchBar from '$lib/components/search/SearchBar.svelte';
	import ResultCard from '$lib/components/search/ResultCard.svelte';
	import Loading from '$lib/components/common/Loading.svelte';
	import Card from '$lib/components/common/Card.svelte';
	import { searchAPI } from '$lib/api/search';
	import { formatTime } from '$lib/utils/format';
	
	let searchQuery = '';
	let results = [];
	let loading = false;
	let error = null;
	let processingTime = 0;
	let hasSearched = false;
	let initialLoad = true;
	
	// Load query from URL only on mount or navigation
	onMount(() => {
		const urlQuery = $page.url.searchParams.get('q');
		if (urlQuery) {
			searchQuery = urlQuery;
			performSearch();
		}
		initialLoad = false;
	});
	
	// Watch for external navigation (e.g., from home page)
	$: if (!initialLoad && $page.url.searchParams.get('q') !== searchQuery) {
		const urlQuery = $page.url.searchParams.get('q');
		if (urlQuery && !hasSearched) {
			searchQuery = urlQuery;
			performSearch();
		}
	}
	
	async function performSearch() {
		if (!searchQuery.trim()) return;
		
		loading = true;
		error = null;
		hasSearched = true;
		
		try {
			const response = await searchAPI.semantic(searchQuery.trim(), 20);
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
		performSearch();
	}
</script>

<svelte:head>
	<title>Search - CEH Dataset Discovery</title>
</svelte:head>

<div class="py-8">
	<Container size="lg">
		<!-- Search Bar -->
		<div class="mb-8">
			<SearchBar
				bind:value={searchQuery}
				onSearch={handleSearch}
				{loading}
			/>
		</div>
		
		<!-- Results Header -->
		{#if hasSearched && !loading}
			<div class="mb-6">
				<div class="flex items-center justify-between">
					<div>
						<h2 class="text-xl font-semibold text-gray-900">
							Search Results
						</h2>
						<p class="text-sm text-gray-600 mt-1">
							Found {results.length} {results.length === 1 ? 'dataset' : 'datasets'}
							{#if processingTime}
								<span class="text-gray-400">• {formatTime(processingTime)}</span>
							{/if}
						</p>
					</div>
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
					<button
						on:click={performSearch}
						class="text-primary-600 hover:text-primary-700 font-medium"
					>
						Try Again
					</button>
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
					</p>
					<div class="space-y-2 text-sm text-gray-600 max-w-md mx-auto">
						<p>Try:</p>
						<ul class="list-disc list-inside text-left">
							<li>Using different keywords</li>
							<li>Checking for typos</li>
							<li>Using more general terms</li>
							<li>Browsing all datasets</li>
						</ul>
					</div>
					<div class="mt-6">
						<a href="/browse" class="text-primary-600 hover:text-primary-700 font-medium">
							Browse All Datasets →
						</a>
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
		
		<!-- Initial State (No Search Yet) -->
		{:else if !hasSearched}
			<Card>
				<div class="text-center py-12">
					<svg class="w-16 h-16 text-primary-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
					<h3 class="text-xl font-semibold text-gray-900 mb-2">Start Searching</h3>
					<p class="text-gray-600 mb-6">
						Enter a search query to find datasets using AI-powered semantic search
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
	</Container>
</div>