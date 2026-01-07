/**
 * Date range utilities for filtering
 */

/**
 * Get predefined date ranges
 */
export function getDateRanges() {
	const now = new Date();
	const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
	
	return {
		'last-7-days': {
			label: 'Last 7 days',
			start: new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000),
			end: today
		},
		'last-30-days': {
			label: 'Last 30 days',
			start: new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000),
			end: today
		},
		'last-90-days': {
			label: 'Last 90 days',
			start: new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000),
			end: today
		},
		'last-year': {
			label: 'Last year',
			start: new Date(today.getFullYear() - 1, today.getMonth(), today.getDate()),
			end: today
		},
		'this-year': {
			label: 'This year',
			start: new Date(today.getFullYear(), 0, 1),
			end: today
		},
		'last-5-years': {
			label: 'Last 5 years',
			start: new Date(today.getFullYear() - 5, today.getMonth(), today.getDate()),
			end: today
		}
	};
}

/**
 * Format date for API (YYYY-MM-DD)
 */
export function formatDateForAPI(date) {
	if (!date) return null;
	const d = new Date(date);
	const year = d.getFullYear();
	const month = String(d.getMonth() + 1).padStart(2, '0');
	const day = String(d.getDate()).padStart(2, '0');
	return `${year}-${month}-${day}`;
}

/**
 * Parse date from API format
 */
export function parseDateFromAPI(dateString) {
	if (!dateString) return null;
	return new Date(dateString);
}

/**
 * Check if date is valid
 */
export function isValidDate(date) {
	return date instanceof Date && !isNaN(date);
}

/**
 * Get date range string for display
 */
export function formatDateRange(startDate, endDate) {
	if (!startDate && !endDate) return 'Any time';
	
	const format = (date) => {
		return date.toLocaleDateString('en-GB', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	};
	
	if (startDate && endDate) {
		return `${format(startDate)} - ${format(endDate)}`;
	} else if (startDate) {
		return `After ${format(startDate)}`;
	} else {
		return `Before ${format(endDate)}`;
	}
}