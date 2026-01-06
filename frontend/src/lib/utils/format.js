/**
 * Formatting utilities
 */

/**
 * Format date to readable string
 */
export function formatDate(dateString) {
	if (!dateString) return 'N/A';
	
	try {
		const date = new Date(dateString);
		return date.toLocaleDateString('en-GB', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	} catch (error) {
		return dateString;
	}
}

/**
 * Format date to short format
 */
export function formatDateShort(dateString) {
	if (!dateString) return 'N/A';
	
	try {
		const date = new Date(dateString);
		return date.toLocaleDateString('en-GB');
	} catch (error) {
		return dateString;
	}
}

/**
 * Truncate text to specified length
 */
export function truncate(text, length = 100) {
	if (!text) return '';
	if (text.length <= length) return text;
	return text.substring(0, length).trim() + '...';
}

/**
 * Format similarity score as percentage
 */
export function formatScore(score) {
	if (score === null || score === undefined) return 'N/A';
	return `${Math.round(score * 100)}%`;
}

/**
 * Format processing time
 */
export function formatTime(ms) {
	if (!ms) return '0ms';
	if (ms < 1000) return `${Math.round(ms)}ms`;
	return `${(ms / 1000).toFixed(2)}s`;
}

/**
 * Get score color class
 */
export function getScoreColor(score) {
	if (score >= 0.8) return 'text-green-600 bg-green-100';
	if (score >= 0.6) return 'text-blue-600 bg-blue-100';
	if (score >= 0.4) return 'text-yellow-600 bg-yellow-100';
	return 'text-gray-600 bg-gray-100';
}

/**
 * Format ORCID to proper URL
 * Handles cases where ORCID is already a full URL or just the ID
 */
export function formatOrcidUrl(orcid) {
	if (!orcid) return null;
	
	// If already a full URL, return as-is
	if (orcid.startsWith('http://') || orcid.startsWith('https://')) {
		return orcid;
	}
	
	// If it starts with orcid.org/, add https://
	if (orcid.startsWith('orcid.org/')) {
		return `https://${orcid}`;
	}
	
	// Otherwise, it's just the ID, prepend the base URL
	return `https://orcid.org/${orcid}`;
}