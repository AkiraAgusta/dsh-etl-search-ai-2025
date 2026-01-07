<script>
	import Badge from '../common/Badge.svelte';
	import { filters, resetFilters, removeAuthor, removeOrganization, removeKeyword, removeFormat, setDateRange } from '$lib/stores/filters';
	import { formatDateRange } from '$lib/utils/dateRange';
	
	$: hasFilters = $filters.authors.length > 0 ||
		$filters.organizations.length > 0 ||
		$filters.keywords.length > 0 ||
		$filters.startDate ||
		$filters.endDate ||
		$filters.formats.length > 0;
</script>

{#if hasFilters}
	<div class="flex flex-wrap items-center gap-2">
		<span class="text-sm font-medium text-gray-700">Active filters:</span>
		
		<!-- Author filters -->
		{#each $filters.authors as author}
			<Badge variant="primary" size="sm">
				<span class="mr-1">Author:</span>
				{author}
				<button
					on:click={() => removeAuthor(author)}
					class="ml-1 hover:text-primary-900"
					aria-label="Remove {author} filter"
				>
					<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</Badge>
		{/each}
		
		<!-- Organization filters -->
		{#each $filters.organizations as org}
			<Badge variant="secondary" size="sm">
				<span class="mr-1">Org:</span>
				{org}
				<button
					on:click={() => removeOrganization(org)}
					class="ml-1 hover:text-secondary-900"
					aria-label="Remove {org} filter"
				>
					<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</Badge>
		{/each}
		
		<!-- Keyword filters -->
		{#each $filters.keywords as keyword}
			<Badge variant="success" size="sm">
				<span class="mr-1">Keyword:</span>
				{keyword}
				<button
					on:click={() => removeKeyword(keyword)}
					class="ml-1 hover:text-green-900"
					aria-label="Remove {keyword} filter"
				>
					<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</Badge>
		{/each}
		
		<!-- Date range filter -->
		{#if $filters.startDate || $filters.endDate}
			<Badge variant="warning" size="sm">
				<span class="mr-1">Date:</span>
				{formatDateRange($filters.startDate, $filters.endDate)}
				<button
					on:click={() => setDateRange(null, null)}
					class="ml-1 hover:text-yellow-900"
					aria-label="Remove date filter"
				>
					<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</Badge>
		{/if}
		
		<!-- Format filters -->
		{#each $filters.formats as format}
			<Badge variant="default" size="sm">
				<span class="mr-1">Format:</span>
				{format}
				<button
					on:click={() => removeFormat(format)}
					class="ml-1 hover:text-gray-900"
					aria-label="Remove {format} filter"
				>
					<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</Badge>
		{/each}
		
		<!-- Clear all button -->
		<button
			on:click={resetFilters}
			class="text-sm text-gray-600 hover:text-gray-800 underline"
		>
			Clear all
		</button>
	</div>
{/if}