<script>
	const currentYear = new Date().getFullYear();
</script>

<footer class="bg-white border-t border-gray-200 mt-auto">
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<div class="grid grid-cols-1 md:grid-cols-3 gap-8">
			<!-- About -->
			<div>
				<h3 class="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3">
					About
				</h3>
				<p class="text-sm text-gray-600">
					CEH Dataset Discovery provides semantic search capabilities for environmental datasets.
				</p>
			</div>
			
			<!-- Quick Links -->
			<div>
				<h3 class="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3">
					Quick Links
				</h3>
				<ul class="space-y-2">
					<li><a href="/" class="text-sm text-gray-600 hover:text-primary-600">Home</a></li>
					<li><a href="/search" class="text-sm text-gray-600 hover:text-primary-600">Search</a></li>
					<li><a href="/browse" class="text-sm text-gray-600 hover:text-primary-600">Browse</a></li>
					<li><a href="/about" class="text-sm text-gray-600 hover:text-primary-600">About</a></li>
				</ul>
			</div>
			
			<!-- Contact -->
			<div>
				<h3 class="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3">
					Resources
				</h3>
				<ul class="space-y-2">
					<li><a href="http://localhost:8000/docs" target="_blank" class="text-sm text-gray-600 hover:text-primary-600">API Documentation</a></li>
					<li><a href="https://github.com/AkiraAgusta/dsh-etl-search-ai-2025" target="_blank" class="text-sm text-gray-600 hover:text-primary-600">GitHub</a></li>
				</ul>
			</div>
		</div>
		
		<div class="mt-8 pt-8 border-t border-gray-200">
			<p class="text-sm text-gray-500 text-center">
				© {currentYear} CEH Dataset Discovery. Built with Svelte and Tailwind CSS.
			</p>
		</div>
	</div>
</footer>