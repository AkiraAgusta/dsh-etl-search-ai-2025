<script>
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import Container from '$lib/components/layout/Container.svelte';
	import Card from '$lib/components/common/Card.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import Loading from '$lib/components/common/Loading.svelte';
	import Button from '$lib/components/common/Button.svelte';
	import { datasetsAPI } from '$lib/api/datasets';
	import { formatDate, formatDateShort, formatOrcidUrl } from '$lib/utils/format';
	
	let dataset = null;
	let keywords = [];
	let contacts = [];
	let resources = [];
	let metadataDocuments = [];
	let loading = true;
	let error = null;
	let activeTab = 'overview';
	let selectedMetadataFormat = 'json';
	
	$: datasetId = $page.params.id;
	
	onMount(async () => {
		await loadDataset();
	});
	
	async function loadDataset() {
		loading = true;
		error = null;
		
		try {
			// Load all dataset information
			[dataset, keywords, contacts, resources, metadataDocuments] = await Promise.all([
				datasetsAPI.get(datasetId),
				datasetsAPI.getKeywords(datasetId),
				datasetsAPI.getContacts(datasetId),
				datasetsAPI.getResources(datasetId),
				datasetsAPI.getMetadata(datasetId)
			]);
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}
	
	function getMetadataContent(format) {
		const doc = metadataDocuments.documents?.find(d => d.format === format);
		return doc?.content || 'No metadata available in this format';
	}
	
	function copyToClipboard(text) {
		navigator.clipboard.writeText(text);
		// You could add a toast notification here
	}
</script>

<svelte:head>
	<title>{dataset?.title || 'Loading...'} - CEH Dataset Discovery</title>
</svelte:head>

<div class="py-8">
	<Container size="lg">
		<!-- Loading State -->
		{#if loading}
			<div class="py-16">
				<Loading text="Loading dataset..." size="lg" />
			</div>
		
		<!-- Error State -->
		{:else if error}
			<Card>
				<div class="text-center py-12">
					<svg class="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<h3 class="text-xl font-semibold text-gray-900 mb-2">Dataset Not Found</h3>
					<p class="text-gray-600 mb-6">{error}</p>
					<a href="/search" class="text-primary-600 hover:text-primary-700 font-medium">
						← Back to Search
					</a>
				</div>
			</Card>
		
		<!-- Dataset Content -->
		{:else if dataset}
			<!-- Breadcrumb -->
			<div class="mb-6">
				<nav class="flex text-sm text-gray-500">
					<a href="/" class="hover:text-primary-600">Home</a>
					<span class="mx-2">/</span>
					<a href="/search" class="hover:text-primary-600">Search</a>
					<span class="mx-2">/</span>
					<span class="text-gray-900">Dataset</span>
				</nav>
			</div>
			
			<!-- Header -->
			<div class="mb-8">
				<h1 class="text-3xl font-bold text-gray-900 mb-2">
					{dataset.title}
				</h1>
				<p class="text-gray-600 mb-4">
					ID: <code class="bg-gray-100 px-2 py-1 rounded">{dataset.file_identifier}</code>
				</p>
				{#if dataset.publication_date}
					<p class="text-sm text-gray-500">
						Published: {formatDate(dataset.publication_date)}
					</p>
				{/if}
			</div>
			
			<!-- Tabs -->
			<div class="border-b border-gray-200 mb-6">
				<nav class="-mb-px flex space-x-8">
					<button
						on:click={() => activeTab = 'overview'}
						class="py-4 px-1 border-b-2 font-medium text-sm transition-colors"
						class:border-primary-600={activeTab === 'overview'}
						class:text-primary-600={activeTab === 'overview'}
						class:border-transparent={activeTab !== 'overview'}
						class:text-gray-500={activeTab !== 'overview'}
						class:hover:text-gray-700={activeTab !== 'overview'}
					>
						Overview
					</button>
					<button
						on:click={() => activeTab = 'metadata'}
						class="py-4 px-1 border-b-2 font-medium text-sm transition-colors"
						class:border-primary-600={activeTab === 'metadata'}
						class:text-primary-600={activeTab === 'metadata'}
						class:border-transparent={activeTab !== 'metadata'}
						class:text-gray-500={activeTab !== 'metadata'}
						class:hover:text-gray-700={activeTab !== 'metadata'}
					>
						Metadata
					</button>
					<button
						on:click={() => activeTab = 'downloads'}
						class="py-4 px-1 border-b-2 font-medium text-sm transition-colors"
						class:border-primary-600={activeTab === 'downloads'}
						class:text-primary-600={activeTab === 'downloads'}
						class:border-transparent={activeTab !== 'downloads'}
						class:text-gray-500={activeTab !== 'downloads'}
						class:hover:text-gray-700={activeTab !== 'downloads'}
					>
						Downloads
					</button>
				</nav>
			</div>
			
			<!-- Tab Content -->
			<div class="space-y-6">
				<!-- Overview Tab -->
				{#if activeTab === 'overview'}
					<!-- Description -->
					{#if dataset.abstract}
						<Card>
							<h2 class="text-lg font-semibold text-gray-900 mb-3">Description</h2>
							<p class="text-gray-700 whitespace-pre-line">{dataset.abstract}</p>
						</Card>
					{/if}
					
					<!-- Details -->
					<Card>
						<h2 class="text-lg font-semibold text-gray-900 mb-4">Details</h2>
						<dl class="grid grid-cols-1 md:grid-cols-2 gap-4">
							{#if dataset.publication_date}
								<div>
									<dt class="text-sm font-medium text-gray-500">Publication Date</dt>
									<dd class="text-sm text-gray-900 mt-1">{formatDate(dataset.publication_date)}</dd>
								</div>
							{/if}
							
							{#if dataset.file_identifier}
								<div>
									<dt class="text-sm font-medium text-gray-500">File Identifier</dt>
									<dd class="text-sm text-gray-900 mt-1">{dataset.file_identifier}</dd>
								</div>
							{/if}
							
							{#if dataset.spatial_extent}
								<div>
									<dt class="text-sm font-medium text-gray-500">Spatial Coverage</dt>
									<dd class="text-sm text-gray-900 mt-1">
										{dataset.spatial_extent.south}°N - {dataset.spatial_extent.north}°N,
										{dataset.spatial_extent.west}°W - {dataset.spatial_extent.east}°E
									</dd>
								</div>
							{/if}
							
							{#if dataset.temporal_extent}
								<div>
									<dt class="text-sm font-medium text-gray-500">Temporal Coverage</dt>
									<dd class="text-sm text-gray-900 mt-1">
										{formatDateShort(dataset.temporal_extent.start)} to {formatDateShort(dataset.temporal_extent.end)}
									</dd>
								</div>
							{/if}
						</dl>
					</Card>
					
					<!-- Keywords -->
					{#if keywords.keywords?.length > 0}
						<Card>
							<h2 class="text-lg font-semibold text-gray-900 mb-4">
								Keywords ({keywords.total})
							</h2>
							<div class="flex flex-wrap gap-2">
								{#each keywords.keywords as keyword}
									<Badge variant="default">
										{keyword.keyword}
										{#if keyword.type}
											<span class="text-xs text-gray-500 ml-1">({keyword.type})</span>
										{/if}
									</Badge>
								{/each}
							</div>
						</Card>
					{/if}
					
					<!-- Contacts -->
					{#if contacts.contacts?.length > 0}
						<Card>
							<h2 class="text-lg font-semibold text-gray-900 mb-4">
								Authors & Contacts ({contacts.total})
							</h2>
							<div class="space-y-4">
								{#each contacts.contacts as contact}
									<div class="border-l-4 border-primary-500 pl-4">
										<div class="font-medium text-gray-900">
											{contact.name || 'Unknown'}
											{#if contact.role}
												<span class="text-sm text-gray-500 font-normal">({contact.role})</span>
											{/if}
										</div>
										{#if contact.organization}
											<div class="text-sm text-gray-600 mt-1">{contact.organization}</div>
										{/if}
										{#if contact.email}
											<a href="mailto:{contact.email}" class="text-sm text-primary-600 hover:text-primary-700 mt-1 block">
												{contact.email}
											</a>
										{/if}
										{#if contact.orcid}
											<a href={formatOrcidUrl(contact.orcid)} target="_blank" class="text-sm text-gray-600 hover:text-primary-600 mt-1 block">
												ORCID: {contact.orcid}
											</a>
										{/if}
									</div>
								{/each}
							</div>
						</Card>
					{/if}
				
				<!-- Metadata Tab -->
				{:else if activeTab === 'metadata'}
					<Card>
						<h2 class="text-lg font-semibold text-gray-900 mb-4">Metadata Formats</h2>
						
						<!-- Format Tabs -->
						<div class="flex space-x-2 mb-4">
							{#each ['json', 'xml', 'jsonld', 'rdf'] as format}
								<button
									on:click={() => selectedMetadataFormat = format}
									class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
									class:bg-primary-600={selectedMetadataFormat === format}
									class:text-white={selectedMetadataFormat === format}
									class:bg-gray-100={selectedMetadataFormat !== format}
									class:text-gray-700={selectedMetadataFormat !== format}
									class:hover:bg-gray-200={selectedMetadataFormat !== format}
								>
									{format.toUpperCase()}
								</button>
							{/each}
						</div>
						
						<!-- Metadata Content -->
						<div class="relative">
							<pre class="bg-gray-50 border border-gray-200 rounded-lg p-4 overflow-x-auto text-sm"><code>{getMetadataContent(selectedMetadataFormat)}</code></pre>
							<div class="mt-4 flex gap-2">
								<Button
									size="sm"
									variant="secondary"
									on:click={() => copyToClipboard(getMetadataContent(selectedMetadataFormat))}
								>
									<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
									</svg>
									Copy
								</Button>
							</div>
						</div>
					</Card>
				
				<!-- Downloads Tab -->
				{:else if activeTab === 'downloads'}
					{#if resources.resources?.length > 0}
						<Card>
							<h2 class="text-lg font-semibold text-gray-900 mb-4">
								Available Resources ({resources.total})
							</h2>
							<div class="space-y-3">
								{#each resources.resources as resource}
									<div class="flex items-start justify-between p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors">
										<div class="flex-1">
											<div class="font-medium text-gray-900">
												{resource.description || 'Download Resource'}
											</div>
											{#if resource.function}
												<div class="text-sm text-gray-500 mt-1">
													Type: {resource.function}
												</div>
											{/if}
											<div class="text-sm text-gray-600 mt-1 break-all">
												{resource.url}
											</div>
										</div>
										<a
											href={resource.url}
											target="_blank"
											rel="noopener noreferrer"
											class="ml-4 flex-shrink-0"
										>
											<Button size="sm">
												<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
												</svg>
												Download
											</Button>
										</a>
									</div>
								{/each}
							</div>
						</Card>
					{:else}
						<Card>
							<p class="text-center text-gray-600 py-8">No download resources available for this dataset.</p>
						</Card>
					{/if}
				{/if}
			</div>
		{/if}
	</Container>
</div>