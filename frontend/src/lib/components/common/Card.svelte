<script>
	export let hoverable = false;
	export let padding = 'p-6';
</script>

<div
	class="card {padding}"
	class:hover:shadow-md={hoverable}
	class:hover:border-primary-300={hoverable}
	class:transform={hoverable}
	class:hover:-translate-y-0.5={hoverable}
	class:transition-all={hoverable}
	class:duration-200={hoverable}
>
	<slot />
</div>