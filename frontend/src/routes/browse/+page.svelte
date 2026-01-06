<script>
	import Container from '$lib/components/layout/Container.svelte';
	import Card from '$lib/components/common/Card.svelte';
</script>

<svelte:head>
	<title>Browse - CEH Dataset Discovery</title>
</svelte:head>

<div class="py-8">
	<Container>
		<h1 class="text-3xl font-bold text-gray-900 mb-6">Browse Datasets</h1>
		
		<Card>
			<div class="text-center py-12">
				<svg class="w-16 h-16 text-primary-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
				</svg>
				<h2 class="text-xl font-semibold text-gray-900 mb-2">Browse Feature</h2>
				<p class="text-gray-600 mb-4">
					This feature will be available
				</p>
				<a href="/search" class="text-primary-600 hover:text-primary-700 font-medium">
					Try Search Instead →
				</a>
			</div>
		</Card>
	</Container>
</div>