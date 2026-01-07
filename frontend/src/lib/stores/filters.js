/**
 * Filter state management
 */
import { writable, derived } from 'svelte/store';

// Filter state
export const filters = writable({
	query: '',
	authors: [],
	organizations: [],
	keywords: [],
	startDate: null,
	endDate: null,
	formats: [],
	spatialExtent: null
});

// Active filters count
export const activeFilterCount = derived(filters, ($filters) => {
	let count = 0;
	if ($filters.authors.length > 0) count++;
	if ($filters.organizations.length > 0) count++;
	if ($filters.keywords.length > 0) count++;
	if ($filters.startDate || $filters.endDate) count++;
	if ($filters.formats.length > 0) count++;
	if ($filters.spatialExtent) count++;
	return count;
});

// Check if any filters are active
export const hasActiveFilters = derived(activeFilterCount, ($count) => $count > 0);

// Reset all filters
export function resetFilters() {
	filters.set({
		query: '',
		authors: [],
		organizations: [],
		keywords: [],
		startDate: null,
		endDate: null,
		formats: [],
		spatialExtent: null
	});
}

// Add author filter
export function addAuthor(author) {
	filters.update(f => ({
		...f,
		authors: [...f.authors, author]
	}));
}

// Remove author filter
export function removeAuthor(author) {
	filters.update(f => ({
		...f,
		authors: f.authors.filter(a => a !== author)
	}));
}

// Add organization filter
export function addOrganization(org) {
	filters.update(f => ({
		...f,
		organizations: [...f.organizations, org]
	}));
}

// Remove organization filter
export function removeOrganization(org) {
	filters.update(f => ({
		...f,
		organizations: f.organizations.filter(o => o !== org)
	}));
}

// Add keyword filter
export function addKeyword(keyword) {
	filters.update(f => ({
		...f,
		keywords: [...f.keywords, keyword]
	}));
}

// Remove keyword filter
export function removeKeyword(keyword) {
	filters.update(f => ({
		...f,
		keywords: f.keywords.filter(k => k !== keyword)
	}));
}

// Set date range
export function setDateRange(startDate, endDate) {
	filters.update(f => ({
		...f,
		startDate,
		endDate
	}));
}

// Add format filter
export function addFormat(format) {
	filters.update(f => ({
		...f,
		formats: [...f.formats, format]
	}));
}

// Remove format filter
export function removeFormat(format) {
	filters.update(f => ({
		...f,
		formats: f.formats.filter(fmt => fmt !== format)
	}));
}

// Set spatial extent
export function setSpatialExtent(extent) {
	filters.update(f => ({
		...f,
		spatialExtent: extent
	}));
}

// Build API parameters from filters
export function buildFilterParams($filters) {
	const params = {};
	
	if ($filters.query) params.query = $filters.query;
	if ($filters.authors.length > 0) params.authors = $filters.authors;
	if ($filters.organizations.length > 0) params.organizations = $filters.organizations;
	if ($filters.keywords.length > 0) params.keywords = $filters.keywords;
	
	// Use date_from and date_to to match backend API expectations
	if ($filters.startDate) params.date_from = formatDate($filters.startDate);
	if ($filters.endDate) params.date_to = formatDate($filters.endDate);
	
	if ($filters.formats.length > 0) params.formats = $filters.formats;
	if ($filters.spatialExtent) params.spatial_extent = $filters.spatialExtent;
	
	return params;
}

// Format date for API
function formatDate(date) {
	if (!date) return null;
	const d = new Date(date);
	const year = d.getFullYear();
	const month = String(d.getMonth() + 1).padStart(2, '0');
	const day = String(d.getDate()).padStart(2, '0');
	return `${year}-${month}-${day}`;
}