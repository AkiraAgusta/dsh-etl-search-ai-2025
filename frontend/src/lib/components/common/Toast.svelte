<script>
	import { fly } from 'svelte/transition';
	import { writable } from 'svelte/store';
	
	// Toast store
	export const toasts = writable([]);
	
	// Add toast
	export function addToast(message, type = 'info', duration = 3000) {
		const id = Date.now() + Math.random();
		const toast = { id, message, type, duration };
		
		toasts.update(t => [...t, toast]);
		
		if (duration > 0) {
			setTimeout(() => {
				removeToast(id);
			}, duration);
		}
		
		return id;
	}
	
	// Remove toast
	export function removeToast(id) {
		toasts.update(t => t.filter(toast => toast.id !== id));
	}
	
	// Toast types
	const types = {
		success: {
			icon: 'M5 13l4 4L19 7',
			bgColor: 'bg-green-50',
			borderColor: 'border-green-500',
			textColor: 'text-green-800',
			iconColor: 'text-green-500'
		},
		error: {
			icon: 'M6 18L18 6M6 6l12 12',
			bgColor: 'bg-red-50',
			borderColor: 'border-red-500',
			textColor: 'text-red-800',
			iconColor: 'text-red-500'
		},
		warning: {
			icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
			bgColor: 'bg-yellow-50',
			borderColor: 'border-yellow-500',
			textColor: 'text-yellow-800',
			iconColor: 'text-yellow-500'
		},
		info: {
			icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
			bgColor: 'bg-blue-50',
			borderColor: 'border-blue-500',
			textColor: 'text-blue-800',
			iconColor: 'text-blue-500'
		}
	};
</script>

<div class="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
	{#each $toasts as toast (toast.id)}
		<div
			transition:fly={{ x: 300, duration: 300 }}
			class="flex items-start gap-3 p-4 rounded-lg shadow-lg border-l-4 {types[toast.type].bgColor} {types[toast.type].borderColor}"
		>
			<svg class="w-6 h-6 {types[toast.type].iconColor} flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={types[toast.type].icon} />
			</svg>
			
			<p class="flex-1 text-sm {types[toast.type].textColor}">
				{toast.message}
			</p>
			
			<button
				on:click={() => removeToast(toast.id)}
				class="flex-shrink-0 {types[toast.type].textColor} hover:opacity-75"
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>
	{/each}
</div>