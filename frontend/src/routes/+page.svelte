<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import Container from '$lib/components/layout/Container.svelte';
	import SearchBar from '$lib/components/search/SearchBar.svelte';
	import Card from '$lib/components/common/Card.svelte';
	import Loading from '$lib/components/common/Loading.svelte';
	import { statsAPI } from '$lib/api/stats';
	import { datasetsAPI } from '$lib/api/datasets';
	
	let searchQuery = '';
	let stats = null;
	let recentDatasets = [];
	let loading = true;
	
	onMount(async () => {
		try {
			// Load stats
			stats = await statsAPI.stats();
			
			// Load recent datasets
			const response = await datasetsAPI.list({
				page: 1,
				page_size: 3,
				sort_by: 'publication_date',
				sort_order: 'desc'
			});
			recentDatasets = response.datasets;
		} catch (error) {
			console.error('Error loading data:', error);
		} finally {
			loading = false;
		}
	});
	
	function handleSearch() {
		if (searchQuery.trim()) {
			goto(`/search?q=${encodeURIComponent(searchQuery)}`);
		}
	}
</script>

<svelte:head>
	<title>Home - CEH Dataset Discovery</title>
</svelte:head>

<!-- Hero Section -->
<section class="bg-gradient-to-br from-primary-50 to-secondary-50 py-16 sm:py-24">
	<Container>
		<div class="text-center">
			<h1 class="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
				Discover Environmental Datasets
			</h1>
			<p class="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
				Search {stats?.total_datasets || '250+'} datasets with AI-powered semantic search
			</p>
			
			<!-- Search Bar -->
			<div class="max-w-3xl mx-auto">
				<SearchBar
					bind:value={searchQuery}
					onSearch={handleSearch}
					large={true}
				/>
			</div>
			
			<!-- Quick Links -->
			<div class="mt-6 flex flex-wrap justify-center gap-4">
				<a href="/search" class="text-primary-600 hover:text-primary-700 font-medium">
					Advanced Search →
				</a>
				<a href="/browse" class="text-primary-600 hover:text-primary-700 font-medium">
					Browse All Datasets →
				</a>
			</div>
		</div>
	</Container>
</section>

<!-- Stats Section -->
{#if stats && !loading}
	<section class="py-12 border-b border-gray-200">
		<Container>
			<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
				<Card>
					<div class="text-center">
						<div class="text-3xl font-bold text-primary-600 mb-2">
							{stats.total_datasets}
						</div>
						<div class="text-sm text-gray-600">Datasets</div>
					</div>
				</Card>
				
				<Card>
					<div class="text-center">
						<div class="text-3xl font-bold text-secondary-600 mb-2">
							{stats.total_keywords}
						</div>
						<div class="text-sm text-gray-600">Keywords</div>
					</div>
				</Card>
				
				<Card>
					<div class="text-center">
						<div class="text-3xl font-bold text-primary-600 mb-2">
							{Object.keys(stats.metadata_formats || {}).length}
						</div>
						<div class="text-sm text-gray-600">Formats</div>
					</div>
				</Card>
			</div>
		</Container>
	</section>
{/if}

<!-- Recent Datasets Section -->
<section class="py-12">
	<Container>
		<h2 class="text-2xl font-bold text-gray-900 mb-6">Recent Datasets</h2>
		
		{#if loading}
			<div class="py-12">
				<Loading text="Loading recent datasets..." />
			</div>
		{:else if recentDatasets.length > 0}
			<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
				{#each recentDatasets as dataset}
					<Card hoverable={true}>
						<h3 class="font-semibold text-gray-900 mb-2">
							<a href="/dataset/{dataset.id}" class="hover:text-primary-600">
								{dataset.title}
							</a>
						</h3>
						<p class="text-sm text-gray-500 mb-3">
							{dataset.file_identifier}
						</p>
						{#if dataset.abstract}
							<p class="text-sm text-gray-600 line-clamp-3">
								{dataset.abstract}
							</p>
						{/if}
						<div class="mt-4">
							<a href="/dataset/{dataset.id}" class="text-sm text-primary-600 hover:text-primary-700 font-medium">
								View Details →
							</a>
						</div>
					</Card>
				{/each}
			</div>
		{:else}
			<Card>
				<p class="text-gray-600 text-center py-8">No recent datasets found.</p>
			</Card>
		{/if}
	</Container>
</section>

<!-- Features Section -->
<section class="py-12 bg-gray-50">
	<Container>
		<h2 class="text-2xl font-bold text-gray-900 mb-8 text-center">Why Use CEH Dataset Discovery?</h2>
		
		<div class="grid grid-cols-1 md:grid-cols-3 gap-8">
			<div class="text-center">
				<div class="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
					<svg class="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
				</div>
				<h3 class="text-lg font-semibold text-gray-900 mb-2">Semantic Search</h3>
				<p class="text-gray-600">Find datasets by meaning, not just keywords. AI-powered search understands context.</p>
			</div>
			
			<div class="text-center">
				<div class="w-16 h-16 bg-secondary-100 rounded-full flex items-center justify-center mx-auto mb-4">
					<svg class="w-8 h-8 text-secondary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
					</svg>
				</div>
				<h3 class="text-lg font-semibold text-gray-900 mb-2">Comprehensive Metadata</h3>
				<p class="text-gray-600">Access complete dataset information including authors, keywords, and spatial extent.</p>
			</div>
			
			<div class="text-center">
				<div class="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
					<svg class="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
					</svg>
				</div>
				<h3 class="text-lg font-semibold text-gray-900 mb-2">Easy Access</h3>
				<p class="text-gray-600">Download datasets in multiple formats. Direct links to original sources.</p>
			</div>
		</div>
	</Container>
</section>