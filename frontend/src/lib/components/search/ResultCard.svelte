<script>
	import { goto } from '$app/navigation';
	import Card from '../common/Card.svelte';
	import Badge from '../common/Badge.svelte';
	import Button from '../common/Button.svelte';
	import { truncate, formatDateShort, formatScore, getScoreColor } from '$lib/utils/format';
	
	export let result;
	export let rank = 1;
	
	function viewDetails() {
		goto(`/dataset/${result.dataset_id}`);
	}
	
	function handleKeydown(event) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			viewDetails();
		}
	}
</script>

<Card hoverable={true}>
	<!-- Header -->
	<div class="flex items-start justify-between gap-4 mb-3">
		<div class="flex-1">
			<div class="flex items-center gap-2 mb-1">
				<span class="text-sm font-medium text-gray-500">#{rank}</span>
				{#if result.similarity_score !== undefined}
					<Badge size="sm" customClass={getScoreColor(result.similarity_score)}>
						{formatScore(result.similarity_score)} match
					</Badge>
				{/if}
			</div>
			<!-- Make title a button for accessibility -->
			<button
				on:click={viewDetails}
				on:keydown={handleKeydown}
				class="text-lg font-semibold text-gray-900 hover:text-primary-600 text-left w-full"
			>
				{result.title}
			</button>
			<p class="text-sm text-gray-500 mt-1">
				ID: {result.file_identifier}
			</p>
		</div>
	</div>
	
	<!-- Abstract -->
	{#if result.abstract}
		<p class="text-gray-600 mb-4">
			{truncate(result.abstract, 200)}
		</p>
	{/if}
	
	<!-- Metadata -->
	<div class="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-gray-500 mb-4">
		{#if result.publication_date}
			<div class="flex items-center gap-1">
				<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
				</svg>
				<span>{formatDateShort(result.publication_date)}</span>
			</div>
		{/if}
	</div>
	
	<!-- Keywords -->
	{#if result.keywords && result.keywords.length > 0}
		<div class="flex flex-wrap gap-2 mb-4">
			{#each result.keywords.slice(0, 5) as keyword}
				<Badge variant="default" size="sm">{keyword}</Badge>
			{/each}
			{#if result.keywords.length > 5}
				<Badge variant="default" size="sm">+{result.keywords.length - 5} more</Badge>
			{/if}
		</div>
	{/if}
	
	<!-- Actions -->
	<div class="flex gap-2">
		<Button on:click={viewDetails}>
			View Details
		</Button>
	</div>
</Card>