<script>
	import { fade, scale } from 'svelte/transition';
	import Button from './Button.svelte';
	
	export let isOpen = false;
	export let title = '';
	export let size = 'md'; // 'sm', 'md', 'lg', 'xl'
	export let showClose = true;
	export let showFooter = true;
	export let onClose = () => {};
	export let onConfirm = null;
	export let confirmText = 'Confirm';
	export let cancelText = 'Cancel';
	export let confirmVariant = 'primary';
	export let loading = false;
	
	const sizes = {
		sm: 'max-w-md',
		md: 'max-w-lg',
		lg: 'max-w-2xl',
		xl: 'max-w-4xl'
	};
	
	function handleClose() {
		if (!loading) {
			isOpen = false;
			onClose();
		}
	}
	
	function handleBackdropClick(event) {
		if (event.target === event.currentTarget) {
			handleClose();
		}
	}
	
	function handleKeydown(event) {
		if (event.key === 'Escape' && !loading && isOpen) {
			handleClose();
		}
	}
	
	async function handleConfirm() {
		if (onConfirm) {
			await onConfirm();
		}
		if (!loading) {
			handleClose();
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if isOpen}
	<div
		class="fixed inset-0 z-50 overflow-y-auto"
		role="dialog"
		aria-modal="true"
		aria-labelledby="modal-title"
	>
		<!-- Backdrop -->
		<button
			type="button"
			class="fixed inset-0 bg-black bg-opacity-50 transition-opacity cursor-default"
			transition:fade={{ duration: 200 }}
			on:click={handleBackdropClick}
			aria-label="Close modal"
			tabindex="-1"
		></button>
		
		<!-- Modal container -->
		<div class="flex min-h-screen items-center justify-center p-4">
			<div
				class="relative bg-white rounded-lg shadow-xl w-full {sizes[size]}"
				transition:scale={{ duration: 200, start: 0.95 }}
			>
				<!-- Header -->
				<div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
					<h3 id="modal-title" class="text-lg font-semibold text-gray-900">
						{title}
					</h3>
					
					{#if showClose && !loading}
						<button
							on:click={handleClose}
							class="text-gray-400 hover:text-gray-600"
							aria-label="Close modal"
						>
							<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					{/if}
				</div>
				
				<!-- Content -->
				<div class="px-6 py-4">
					<slot />
				</div>
				
				<!-- Footer -->
				{#if showFooter}
					<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
						<slot name="footer">
							<Button
								on:click={handleClose}
								variant="secondary"
								disabled={loading}
							>
								{cancelText}
							</Button>
							
							{#if onConfirm}
								<Button
									on:click={handleConfirm}
									variant={confirmVariant}
									{loading}
								>
									{confirmText}
								</Button>
							{/if}
						</slot>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}