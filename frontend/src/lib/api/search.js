/**
 * Search API endpoints
 */

import apiClient from './client';

export const searchAPI = {
	/**
	 * Semantic search
	 */
	semantic: async (query, topK = 10) => {
		return apiClient.post('/search/semantic', {
			query,
			top_k: topK
		});
	},

	/**
	 * Enriched semantic search (includes metadata)
	 */
	semanticEnriched: async (query, topK = 10) => {
		return apiClient.post('/search/semantic/enriched', {
			query,
			top_k: topK
		});
	},

	/**
	 * Hybrid search with filters
	 */
	hybrid: async (params) => {
		return apiClient.post('/search/hybrid', params);
	}
};