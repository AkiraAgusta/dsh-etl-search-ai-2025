<script>
	import Navigation from '$lib/components/layout/Navigation.svelte';
	import Footer from '$lib/components/layout/Footer.svelte';
	import '../app.css';
</script>

<svelte:head>
	<title>CEH Dataset Discovery</title>
	<meta name="description" content="Search and discover environmental datasets with AI-powered semantic search" />
</svelte:head>

<div class="flex flex-col min-h-screen">
	<Navigation />
	
	<main class="flex-1">
		<slot />
	</main>
	
	<Footer />
</div>