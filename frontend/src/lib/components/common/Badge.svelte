<script>
	export let variant = 'default'; // default, primary, secondary, success, warning, score, custom
	export let size = 'md'; // sm, md, lg
	export let customClass = ''; // For dynamic color classes

	const variants = {
		default: 'bg-gray-100 text-gray-800',
		primary: 'bg-primary-100 text-primary-800',
		secondary: 'bg-secondary-100 text-secondary-800',
		success: 'bg-green-100 text-green-800',
		warning: 'bg-yellow-100 text-yellow-800',
		score: 'bg-blue-100 text-blue-800'
	};

	const sizes = {
		sm: 'text-xs px-2 py-0.5',
		md: 'text-sm px-2.5 py-0.5',
		lg: 'text-base px-3 py-1'
	};
	
	// Use custom class if provided, otherwise use variant
	$: colorClass = customClass || variants[variant];
</script>

<span class="inline-flex items-center rounded-full font-medium {colorClass} {sizes[size]}">
	<slot />
</span>