<script>
	import { page } from '$app/stores';
	
	let mobileMenuOpen = false;
	
	const navItems = [
		{ label: 'Home', href: '/' },
		{ label: 'Search', href: '/search' },
		{ label: 'Browse', href: '/browse' },
		{ label: 'About', href: '/about' }
	];
	
	$: currentPath = $page.url.pathname;
</script>

<nav class="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
		<div class="flex justify-between h-16">
			<!-- Logo and Brand -->
			<div class="flex items-center">
				<a href="/" class="flex items-center space-x-2">
					<div class="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
						<svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
						</svg>
					</div>
					<span class="text-xl font-bold text-gray-900 hidden sm:block">CEH Datasets</span>
				</a>
			</div>
			
			<!-- Desktop Navigation -->
			<div class="hidden md:flex md:items-center md:space-x-1">
				{#each navItems as item}
					{#if item.href === '/'}
						<!-- Home: Exact match only -->
						<a
							href={item.href}
							class="px-3 py-2 rounded-md text-sm font-medium transition-colors"
							class:text-primary-600={currentPath === '/'}
							class:bg-primary-50={currentPath === '/'}
							class:text-gray-700={currentPath !== '/'}
							class:hover:bg-gray-100={currentPath !== '/'}
						>
							{item.label}
						</a>
					{:else}
						<!-- Other pages: Starts with -->
						<a
							href={item.href}
							class="px-3 py-2 rounded-md text-sm font-medium transition-colors"
							class:text-primary-600={currentPath.startsWith(item.href)}
							class:bg-primary-50={currentPath.startsWith(item.href)}
							class:text-gray-700={!currentPath.startsWith(item.href)}
							class:hover:bg-gray-100={!currentPath.startsWith(item.href)}
						>
							{item.label}
						</a>
					{/if}
				{/each}
			</div>
			
			<!-- Mobile menu button -->
			<div class="flex items-center md:hidden">
				<button
					on:click={() => (mobileMenuOpen = !mobileMenuOpen)}
					class="inline-flex items-center justify-center p-2 rounded-md text-gray-700 hover:bg-gray-100"
					aria-label="Toggle menu"
				>
					<svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						{#if mobileMenuOpen}
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						{:else}
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
						{/if}
					</svg>
				</button>
			</div>
		</div>
	</div>
	
	<!-- Mobile menu -->
	{#if mobileMenuOpen}
		<div class="md:hidden border-t border-gray-200">
			<div class="px-2 pt-2 pb-3 space-y-1">
				{#each navItems as item}
					{#if item.href === '/'}
						<!-- Home: Exact match only -->
						<a
							href={item.href}
							on:click={() => (mobileMenuOpen = false)}
							class="block px-3 py-2 rounded-md text-base font-medium"
							class:text-primary-600={currentPath === '/'}
							class:bg-primary-50={currentPath === '/'}
							class:text-gray-700={currentPath !== '/'}
							class:hover:bg-gray-100={currentPath !== '/'}
						>
							{item.label}
						</a>
					{:else}
						<!-- Other pages: Starts with -->
						<a
							href={item.href}
							on:click={() => (mobileMenuOpen = false)}
							class="block px-3 py-2 rounded-md text-base font-medium"
							class:text-primary-600={currentPath.startsWith(item.href)}
							class:bg-primary-50={currentPath.startsWith(item.href)}
							class:text-gray-700={!currentPath.startsWith(item.href)}
							class:hover:bg-gray-100={!currentPath.startsWith(item.href)}
						>
							{item.label}
						</a>
					{/if}
				{/each}
			</div>
		</div>
	{/if}
</nav>