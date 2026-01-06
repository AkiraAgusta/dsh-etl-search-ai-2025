<script>
	import Container from '$lib/components/layout/Container.svelte';
	import Card from '$lib/components/common/Card.svelte';
</script>

<svelte:head>
	<title>About - CEH Dataset Discovery</title>
</svelte:head>

<div class="py-8">
	<Container>
		<h1 class="text-3xl font-bold text-gray-900 mb-6">About CEH Dataset Discovery</h1>
		
		<div class="space-y-6">
			<Card>
				<h2 class="text-xl font-semibold text-gray-900 mb-3">What is This?</h2>
				<p class="text-gray-700">
					CEH Dataset Discovery is an AI-powered semantic search system for environmental datasets.
					It uses vector embeddings and similarity search to help researchers find relevant datasets
					based on meaning, not just keywords.
				</p>
			</Card>
			
			<Card>
				<h2 class="text-xl font-semibold text-gray-900 mb-3">How It Works</h2>
				<div class="space-y-3 text-gray-700">
					<p><strong>1. Semantic Search:</strong> We use AI to understand the meaning of your query and match it with relevant datasets.</p>
					<p><strong>2. Vector Similarity:</strong> Dataset titles and abstracts are converted to numerical vectors, allowing precise similarity matching.</p>
					<p><strong>3. Comprehensive Metadata:</strong> Access complete information including authors, keywords, spatial/temporal coverage, and download links.</p>
				</div>
			</Card>
			
			<Card>
				<h2 class="text-xl font-semibold text-gray-900 mb-3">Technology Stack</h2>
				<div class="grid grid-cols-2 gap-4 text-sm">
					<div>
						<h3 class="font-semibold text-gray-900 mb-2">Frontend</h3>
						<ul class="space-y-1 text-gray-600">
							<li>• Svelte + SvelteKit</li>
							<li>• Tailwind CSS</li>
							<li>• Axios</li>
						</ul>
					</div>
					<div>
						<h3 class="font-semibold text-gray-900 mb-2">Backend</h3>
						<ul class="space-y-1 text-gray-600">
							<li>• Python + FastAPI</li>
							<li>• FAISS</li>
							<li>• Sentence Transformers</li>
						</ul>
					</div>
				</div>
			</Card>
			
			<Card>
				<h2 class="text-xl font-semibold text-gray-900 mb-3">Contact</h2>
				<p class="text-gray-700">
					For questions or feedback, please contact <a href="mailto:akiraagusta@gmail.com" class="text-primary-600 hover:text-primary-700 font-medium">akiraagusta@gmail.com</a>.
				</p>
			</Card>
		</div>
	</Container>
</div>