<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import Container from '$lib/components/layout/Container.svelte';
	import Card from '$lib/components/common/Card.svelte';
	import Button from '$lib/components/common/Button.svelte';
	import Loading from '$lib/components/common/Loading.svelte';
	import FilterPanel from '$lib/components/filters/FilterPanel.svelte';
	import FilterChips from '$lib/components/filters/FilterChips.svelte';
	import { datasetsAPI } from '$lib/api/datasets';
	import { filters, hasActiveFilters, resetFilters } from '$lib/stores/filters';
	import { formatDateShort, truncate } from '$lib/utils/format';
	
	let datasets = [];
	let loading = true;
	let error = null;
	
	// Pagination
	let currentPage = 1;
	let pageSize = 12;
	let totalDatasets = 0;
	$: totalPages = Math.ceil(totalDatasets / pageSize);
	$: paginationInfo = {
		from: (currentPage - 1) * pageSize + 1,
		to: Math.min(currentPage * pageSize, totalDatasets),
		total: totalDatasets
	};
	
	// Sorting
	let sortBy = 'publication_date';
	let sortOrder = 'desc';
	const sortOptions = [
		{ value: 'publication_date', label: 'Publication Date' },
		{ value: 'title', label: 'Title' },
		{ value: 'file_identifier', label: 'File ID' }
	];
	
	// Auto-adjust sort order based on sort field
	let previousSortBy = sortBy;
	$: if (sortBy !== previousSortBy) {
		// When changing to title or file_identifier, default to ascending
		if ((sortBy === 'title' || sortBy === 'file_identifier') && previousSortBy === 'publication_date') {
			sortOrder = 'asc';
		}
		// When changing to publication_date, default to descending
		else if (sortBy === 'publication_date' && (previousSortBy === 'title' || previousSortBy === 'file_identifier')) {
			sortOrder = 'desc';
		}
		previousSortBy = sortBy;
	}
	
	// View mode
	let viewMode = 'grid'; // 'grid' or 'list'
	
	// Filter panel
	let showFilters = false;
	
	onMount(() => {
		// Reset filters first to clear any previous state
		resetFilters();
		
		// Load URL parameters if present
		loadFromURL();
		
		// Load datasets
		loadDatasets();
	});
	
	function loadFromURL() {
		const params = $page.url.searchParams;
		currentPage = parseInt(params.get('page') || '1');
		sortBy = params.get('sort') || 'publication_date';
		sortOrder = params.get('order') || 'desc';
		viewMode = params.get('view') || 'grid';
		previousSortBy = sortBy; // Initialize to prevent reactive trigger
	}
	
	async function loadDatasets() {
		loading = true;
		error = null;
		
		try {
			const params = {
				page: currentPage,
				page_size: pageSize,
				sort_by: sortBy,
				sort_order: sortOrder
			};
			
			// Add filter parameters when filters are active
			if ($hasActiveFilters) {
				// Add authors filter
				if ($filters.authors && $filters.authors.length > 0) {
					params.authors = $filters.authors;
				}
				
				// Add organizations filter
				if ($filters.organizations && $filters.organizations.length > 0) {
					params.organizations = $filters.organizations;
				}
				
				// Add keywords filter
				if ($filters.keywords && $filters.keywords.length > 0) {
					params.keywords = $filters.keywords;
				}
				
				// Add date range filters - Use date_from and date_to to match backend API
				if ($filters.startDate) {
					// Format date as YYYY-MM-DD
					const d = new Date($filters.startDate);
					params.date_from = d.toISOString().split('T')[0];
				}
				
				if ($filters.endDate) {
					// Format date as YYYY-MM-DD
					const d = new Date($filters.endDate);
					params.date_to = d.toISOString().split('T')[0];
				}
			}
			
			const response = await datasetsAPI.list(params);
			datasets = response.datasets;
			totalDatasets = response.total;
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}
	
	function updateURL() {
		const url = new URL($page.url);
		url.searchParams.set('page', currentPage.toString());
		url.searchParams.set('sort', sortBy);
		url.searchParams.set('order', sortOrder);
		url.searchParams.set('view', viewMode);
		goto(url, { replaceState: true, noScroll: true });
	}
	
	function handlePageChange(newPage) {
		if (newPage < 1 || newPage > totalPages) return;
		currentPage = newPage;
		updateURL();
		loadDatasets();
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}
	
	function handleSortChange() {
		currentPage = 1;
		updateURL();
		loadDatasets();
	}
	
	function handleViewModeChange(mode) {
		viewMode = mode;
		updateURL();
	}
	
	function handleApplyFilters() {
		currentPage = 1;
		updateURL();
		loadDatasets();
	}
	
	function toggleFilters() {
		showFilters = !showFilters;
	}
	
	// Generate page numbers for pagination
	$: pageNumbers = generatePageNumbers(currentPage, totalPages);
	
	function generatePageNumbers(current, total) {
		const pages = [];
		const maxVisible = 7;
		
		if (total <= maxVisible) {
			for (let i = 1; i <= total; i++) {
				pages.push(i);
			}
		} else {
			// Always show first page
			pages.push(1);
			
			// Calculate range around current page
			let start = Math.max(2, current - 1);
			let end = Math.min(total - 1, current + 1);
			
			// Add ellipsis after first page if needed
			if (start > 2) {
				pages.push('...');
			}
			
			// Add pages around current
			for (let i = start; i <= end; i++) {
				pages.push(i);
			}
			
			// Add ellipsis before last page if needed
			if (end < total - 1) {
				pages.push('...');
			}
			
			// Always show last page
			pages.push(total);
		}
		
		return pages;
	}
</script>

<svelte:head>
	<title>Browse Datasets - CEH Dataset Discovery</title>
</svelte:head>

<div class="py-8">
	<Container size="lg">
		<!-- Header -->
		<div class="mb-6">
			<h1 class="text-3xl font-bold text-gray-900 mb-2">Browse Datasets</h1>
			<p class="text-gray-600">
				Explore all {totalDatasets} datasets in our collection
			</p>
		</div>
		
		<div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
			<!-- Filter sidebar (desktop) -->
			<div class="hidden lg:block">
				<div class="sticky top-24 z-10">
					<FilterPanel onApplyFilters={handleApplyFilters} showApplyButton={true} />
				</div>
			</div>
			
			<!-- Main content -->
			<div class="lg:col-span-3 relative z-0">
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
				
				<!-- Controls bar -->
				<div class="mb-6 flex flex-wrap items-center justify-between gap-4">
					<!-- Sort controls -->
					<div class="flex items-center gap-4">
						<div class="flex items-center gap-2">
							<label for="sort-by" class="text-sm text-gray-700">Sort by:</label>
							<select
								id="sort-by"
								bind:value={sortBy}
								on:change={handleSortChange}
								class="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
							>
								{#each sortOptions as option}
									<option value={option.value}>{option.label}</option>
								{/each}
							</select>
						</div>
						
						<button
							on:click={() => {
								sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
								handleSortChange();
							}}
							class="p-1.5 hover:bg-gray-100 rounded"
							title={sortOrder === 'asc' ? 'Ascending' : 'Descending'}
						>
							<svg class="w-5 h-5 text-gray-600 transition-transform" class:rotate-180={sortOrder === 'desc'} fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
							</svg>
						</button>
					</div>
					
					<!-- View mode toggle -->
					<div class="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
						<button
							on:click={() => handleViewModeChange('grid')}
							class="p-2 rounded transition-colors"
							class:bg-white={viewMode === 'grid'}
							class:shadow-sm={viewMode === 'grid'}
							title="Grid view"
						>
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
							</svg>
						</button>
						<button
							on:click={() => handleViewModeChange('list')}
							class="p-2 rounded transition-colors"
							class:bg-white={viewMode === 'list'}
							class:shadow-sm={viewMode === 'list'}
							title="List view"
						>
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
							</svg>
						</button>
					</div>
				</div>
				
				<!-- Results info -->
				{#if !loading && datasets.length > 0}
					<div class="mb-4 text-sm text-gray-600">
						Showing {paginationInfo.from}–{paginationInfo.to} of {paginationInfo.total} datasets
					</div>
				{/if}
				
				<!-- Loading state -->
				{#if loading}
					<div class="py-16">
						<Loading text="Loading datasets..." size="lg" />
					</div>
				
				<!-- Error state -->
				{:else if error}
					<Card>
						<div class="text-center py-8">
							<svg class="w-12 h-12 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							<h3 class="text-lg font-semibold text-gray-900 mb-2">Error Loading Datasets</h3>
							<p class="text-gray-600 mb-4">{error}</p>
							<Button on:click={loadDatasets}>Try Again</Button>
						</div>
					</Card>
				
				<!-- No results -->
				{:else if datasets.length === 0}
					<Card>
						<div class="text-center py-12">
							<svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
							</svg>
							<h3 class="text-xl font-semibold text-gray-900 mb-2">No Datasets Found</h3>
							<p class="text-gray-600">
								{#if $hasActiveFilters}
									No datasets match your filters. Try removing some filters.
								{:else}
									No datasets available at this time.
								{/if}
							</p>
						</div>
					</Card>
				
				<!-- Grid view -->
				{:else if viewMode === 'grid'}
					<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
						{#each datasets as dataset}
							<Card hoverable={true}>
								<div class="flex flex-col h-full">
									<h3 class="font-semibold text-gray-900 mb-2 line-clamp-2">
										<a href="/dataset/{dataset.id}" class="hover:text-primary-600">
											{dataset.title}
										</a>
									</h3>
									<p class="text-xs text-gray-500 mb-3">
										{dataset.file_identifier}
									</p>
									{#if dataset.abstract}
										<p class="text-sm text-gray-600 mb-4 line-clamp-3 flex-grow">
											{truncate(dataset.abstract, 150)}
										</p>
									{/if}
									{#if dataset.publication_date}
										<div class="text-xs text-gray-500 mb-3">
											{formatDateShort(dataset.publication_date)}
										</div>
									{/if}
									<a href="/dataset/{dataset.id}" class="text-sm text-primary-600 hover:text-primary-700 font-medium">
										View Details →
									</a>
								</div>
							</Card>
						{/each}
					</div>
				
				<!-- List view -->
				{:else}
					<div class="space-y-4">
						{#each datasets as dataset}
							<Card hoverable={true}>
								<div class="flex items-start justify-between gap-4">
									<div class="flex-1">
										<h3 class="font-semibold text-gray-900 mb-1">
											<a href="/dataset/{dataset.id}" class="hover:text-primary-600">
												{dataset.title}
											</a>
										</h3>
										<p class="text-sm text-gray-500 mb-2">
											{dataset.file_identifier}
										</p>
										{#if dataset.abstract}
											<p class="text-sm text-gray-600 mb-3">
												{truncate(dataset.abstract, 200)}
											</p>
										{/if}
										<div class="flex items-center gap-4 text-xs text-gray-500">
											{#if dataset.publication_date}
												<span>{formatDateShort(dataset.publication_date)}</span>
											{/if}
										</div>
									</div>
									<a href="/dataset/{dataset.id}">
										<Button size="sm">View</Button>
									</a>
								</div>
							</Card>
						{/each}
					</div>
				{/if}
				
				<!-- Pagination -->
				{#if !loading && totalPages > 1}
					<div class="mt-8 flex items-center justify-between">
						<!-- Previous button -->
						<Button
							on:click={() => handlePageChange(currentPage - 1)}
							disabled={currentPage === 1}
							variant="secondary"
							size="sm"
						>
							<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
							</svg>
							Previous
						</Button>
						
						<!-- Page numbers -->
						<div class="flex items-center gap-1">
							{#each pageNumbers as pageNum}
								{#if pageNum === '...'}
									<span class="px-3 py-1 text-gray-500">...</span>
								{:else}
									<button
										on:click={() => handlePageChange(pageNum)}
										class="px-3 py-1 rounded transition-colors"
										class:bg-primary-600={currentPage === pageNum}
										class:text-white={currentPage === pageNum}
										class:hover:bg-gray-100={currentPage !== pageNum}
										class:text-gray-700={currentPage !== pageNum}
									>
										{pageNum}
									</button>
								{/if}
							{/each}
						</div>
						
						<!-- Next button -->
						<Button
							on:click={() => handlePageChange(currentPage + 1)}
							disabled={currentPage === totalPages}
							variant="secondary"
							size="sm"
						>
							Next
							<svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
							</svg>
						</Button>
					</div>
				{/if}
			</div>
		</div>
	</Container>
</div>