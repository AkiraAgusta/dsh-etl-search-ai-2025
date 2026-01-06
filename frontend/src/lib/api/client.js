/**
 * API Client for CEH Dataset Discovery
 * 
 * Provides centralized HTTP client with error handling
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
	baseURL: API_BASE_URL,
	headers: {
		'Content-Type': 'application/json'
	},
	timeout: 30000
});

// Request interceptor
apiClient.interceptors.request.use(
	(config) => {
		return config;
	},
	(error) => {
		return Promise.reject(error);
	}
);

// Response interceptor
apiClient.interceptors.response.use(
	(response) => response.data,
	(error) => {
		console.error('API Error:', error.response?.data || error.message);
		
		// Format error message
		const errorMessage = error.response?.data?.detail || 
		                     error.response?.data?.error || 
		                     error.message || 
		                     'An unexpected error occurred';
		
		return Promise.reject(new Error(errorMessage));
	}
);

export default apiClient;