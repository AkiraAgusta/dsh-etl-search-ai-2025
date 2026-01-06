/**
 * Search state management
 */

import { writable, derived } from 'svelte/store';

// Search query
export const searchQuery = writable('');

// Search results
export const searchResults = writable([]);

// Loading state
export const isSearching = writable(false);

// Error state
export const searchError = writable(null);

// Processing time
export const processingTime = writable(0);

// Derived stores
export const hasResults = derived(
	searchResults,
	($results) => $results.length > 0
);

export const resultsCount = derived(
	searchResults,
	($results) => $results.length
);

// Clear search
export function clearSearch() {
	searchQuery.set('');
	searchResults.set([]);
	searchError.set(null);
	processingTime.set(0);
}