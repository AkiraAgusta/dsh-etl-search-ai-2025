<script>
	import { onMount } from 'svelte';
	import Container from '$lib/components/layout/Container.svelte';
	import Card from '$lib/components/common/Card.svelte';
	import Loading from '$lib/components/common/Loading.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import { statsAPI } from '$lib/api/stats';
	import { datasetsAPI } from '$lib/api/datasets';
	import { formatDate, truncate } from '$lib/utils/format';
	
	let stats = null;
	let recentDatasets = [];
	let loading = true;
	let error = null;
	
	onMount(async () => {
		await loadDashboard();
	});
	
	async function loadDashboard() {
		loading = true;
		error = null;
		
		try {
			// Load stats and recent datasets
			[stats, recentDatasets] = await Promise.all([
				statsAPI.stats(),
				datasetsAPI.list({
					page: 1,
					page_size: 5,
					sort_by: 'publication_date',
					sort_order: 'desc'
				}).then(r => r.datasets)
			]);
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}
	
	// Calculate percentage for progress bars
	function getPercentage(value, total) {
		return total > 0 ? Math.round((value / total) * 100) : 0;
	}
</script>

<svelte:head>
	<title>Dashboard - CEH Dataset Discovery</title>
</svelte:head>

<div class="py-8">
	<Container size="lg">
		<!-- Header -->
		<div class="mb-8">
			<h1 class="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
			<p class="text-gray-600">Overview of datasets and collection statistics</p>
		</div>
		
		{#if loading}
			<div class="py-16">
				<Loading text="Loading dashboard..." size="lg" />
			</div>
		{:else if error}
			<Card>
				<div class="text-center py-8">
					<svg class="w-12 h-12 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<h3 class="text-lg font-semibold text-gray-900 mb-2">Error Loading Dashboard</h3>
					<p class="text-gray-600 mb-4">{error}</p>
					<button
						on:click={loadDashboard}
						class="text-primary-600 hover:text-primary-700 font-medium"
					>
						Try Again
					</button>
				</div>
			</Card>
		{:else if stats}
			<!-- Stats Grid -->
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
				<!-- Total Datasets -->
				<Card>
					<div class="flex items-center">
						<div class="flex-shrink-0 bg-primary-100 rounded-lg p-3">
							<svg class="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
							</svg>
						</div>
						<div class="ml-4">
							<p class="text-sm text-gray-600">Total Datasets</p>
							<p class="text-2xl font-bold text-gray-900">{stats.total_datasets}</p>
						</div>
					</div>
				</Card>
				
				<!-- Total Keywords -->
				<Card>
					<div class="flex items-center">
						<div class="flex-shrink-0 bg-secondary-100 rounded-lg p-3">
							<svg class="w-8 h-8 text-secondary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
							</svg>
						</div>
						<div class="ml-4">
							<p class="text-sm text-gray-600">Keywords</p>
							<p class="text-2xl font-bold text-gray-900">{stats.total_keywords}</p>
						</div>
					</div>
				</Card>
				
				<!-- Metadata Formats -->
				<Card>
					<div class="flex items-center">
						<div class="flex-shrink-0 bg-green-100 rounded-lg p-3">
							<svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
							</svg>
						</div>
						<div class="ml-4">
							<p class="text-sm text-gray-600">Formats</p>
							<p class="text-2xl font-bold text-gray-900">{Object.keys(stats.metadata_formats || {}).length}</p>
						</div>
					</div>
				</Card>
				
				<!-- Total Contacts -->
				<Card>
					<div class="flex items-center">
						<div class="flex-shrink-0 bg-yellow-100 rounded-lg p-3">
							<svg class="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
							</svg>
						</div>
						<div class="ml-4">
							<p class="text-sm text-gray-600">Contributors</p>
							<p class="text-2xl font-bold text-gray-900">{stats.total_contacts}</p>
						</div>
					</div>
				</Card>
			</div>
			
			<!-- Two column layout -->
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
				<!-- Top Authors -->
				<Card>
					<h2 class="text-lg font-semibold text-gray-900 mb-4">Top Authors</h2>
					{#if stats.top_authors && stats.top_authors.length > 0}
						<div class="space-y-3">
							{#each stats.top_authors.slice(0, 10) as author}
								<div class="flex items-center justify-between">
									<div class="flex-1">
										<p class="text-sm font-medium text-gray-900">{author.name}</p>
										{#if author.organization}
											<p class="text-xs text-gray-500">{author.organization}</p>
										{/if}
									</div>
									<div class="flex items-center gap-3">
										<div class="w-24 bg-gray-200 rounded-full h-2">
											<div
												class="bg-primary-600 h-2 rounded-full"
												style="width: {getPercentage(author.count, stats.top_authors[0].count)}%"
											></div>
										</div>
										<span class="text-sm font-medium text-gray-700 w-8 text-right">{author.count}</span>
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<p class="text-gray-500 text-sm">No author data available</p>
					{/if}
				</Card>
				
				<!-- Top Organizations -->
				<Card>
					<h2 class="text-lg font-semibold text-gray-900 mb-4">Top Organizations</h2>
					{#if stats.top_organizations && stats.top_organizations.length > 0}
						<div class="space-y-3">
							{#each stats.top_organizations.slice(0, 10) as org}
								<div class="flex items-center justify-between">
									<div class="flex-1">
										<p class="text-sm font-medium text-gray-900">{org.name}</p>
									</div>
									<div class="flex items-center gap-3">
										<div class="w-24 bg-gray-200 rounded-full h-2">
											<div
												class="bg-secondary-600 h-2 rounded-full"
												style="width: {getPercentage(org.count, stats.top_organizations[0].count)}%"
											></div>
										</div>
										<span class="text-sm font-medium text-gray-700 w-8 text-right">{org.count}</span>
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<p class="text-gray-500 text-sm">No organization data available</p>
					{/if}
				</Card>
			</div>
			
			<!-- Top Keywords and Metadata Formats -->
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
				<!-- Top Keywords -->
				<Card>
					<h2 class="text-lg font-semibold text-gray-900 mb-4">Popular Keywords</h2>
					{#if stats.top_keywords && stats.top_keywords.length > 0}
						<div class="flex flex-wrap gap-2">
							{#each stats.top_keywords.slice(0, 20) as keyword}
								<Badge
									variant="default"
									size="md"
									customClass="bg-gray-100 text-gray-700 hover:bg-gray-200 cursor-default"
								>
									{keyword.keyword}
									<span class="ml-1.5 text-xs text-gray-500">({keyword.count})</span>
								</Badge>
							{/each}
						</div>
					{:else}
						<p class="text-gray-500 text-sm">No keyword data available</p>
					{/if}
				</Card>
				
				<!-- Metadata Formats -->
				<Card>
					<h2 class="text-lg font-semibold text-gray-900 mb-4">Metadata Formats</h2>
					{#if stats.metadata_formats && Object.keys(stats.metadata_formats).length > 0}
						<div class="space-y-3">
							{#each Object.entries(stats.metadata_formats) as [format, count]}
								<div class="flex items-center justify-between">
									<span class="text-sm font-medium text-gray-900">{format}</span>
									<div class="flex items-center gap-3">
										<div class="w-32 bg-gray-200 rounded-full h-2">
											<div
												class="bg-green-600 h-2 rounded-full"
												style="width: {getPercentage(count, stats.total_datasets)}%"
											></div>
										</div>
										<span class="text-sm font-medium text-gray-700 w-12 text-right">{count}</span>
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<p class="text-gray-500 text-sm">No format data available</p>
					{/if}
				</Card>
			</div>
			
			<!-- Recent Datasets -->
			<Card>
				<h2 class="text-lg font-semibold text-gray-900 mb-4">Recent Datasets</h2>
				{#if recentDatasets.length > 0}
					<div class="space-y-4">
						{#each recentDatasets as dataset}
							<div class="border-l-4 border-primary-500 pl-4 py-2">
								<h3 class="font-medium text-gray-900 mb-1">
									<a href="/dataset/{dataset.id}" class="hover:text-primary-600">
										{dataset.title}
									</a>
								</h3>
								<p class="text-sm text-gray-600 mb-2">
									{truncate(dataset.abstract || '', 120)}
								</p>
								<div class="flex items-center gap-4 text-xs text-gray-500">
									<span>{dataset.file_identifier}</span>
									{#if dataset.publication_date}
										<span>• {formatDate(dataset.publication_date)}</span>
									{/if}
								</div>
							</div>
						{/each}
					</div>
					
					<div class="mt-4 pt-4 border-t border-gray-200">
						<a href="/browse" class="text-primary-600 hover:text-primary-700 font-medium text-sm">
							View all datasets →
						</a>
					</div>
				{:else}
					<p class="text-gray-500 text-sm">No recent datasets</p>
				{/if}
			</Card>
		{/if}
	</Container>
</div>