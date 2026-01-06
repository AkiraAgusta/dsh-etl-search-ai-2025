/**
 * Dataset API endpoints
 */

import apiClient from './client';

export const datasetsAPI = {
	/**
	 * List datasets with pagination
	 */
	list: async (params = {}) => {
		return apiClient.get('/datasets/', { params });
	},

	/**
	 * Get dataset by ID
	 */
	get: async (id) => {
		return apiClient.get(`/datasets/${id}`);
	},

	/**
	 * Get dataset keywords
	 */
	getKeywords: async (id) => {
		return apiClient.get(`/datasets/${id}/keywords`);
	},

	/**
	 * Get dataset contacts/authors
	 */
	getContacts: async (id) => {
		return apiClient.get(`/datasets/${id}/contacts`);
	},

	/**
	 * Get dataset resources/downloads
	 */
	getResources: async (id) => {
		return apiClient.get(`/datasets/${id}/resources`);
	},

	/**
	 * Get dataset metadata documents
	 */
	getMetadata: async (id, format = null) => {
		const params = format ? { format } : {};
		return apiClient.get(`/datasets/${id}/metadata`, { params });
	}
};