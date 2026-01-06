/**
 * Statistics API endpoints
 */

import apiClient from './client';

export const statsAPI = {
	/**
	 * Get system health
	 */
	health: async () => {
		return apiClient.get('/health');
	},

	/**
	 * Get database statistics
	 */
	stats: async () => {
		return apiClient.get('/stats');
	}
};