# Frontend Architecture - AI Conversation

## Frontend Technology Stack Discussion

### Me:
For the frontend, the requirements specify using either Svelte or Vue. I've chosen Svelte with SvelteKit. Before we start implementing, help me design the frontend architecture. What are the key architectural patterns we should follow for a search and discovery application?

### Claude:
Excellent choice! SvelteKit provides great developer experience and performance. Let's design a clean, maintainable frontend architecture.

**Frontend Architecture Principles:**

**1. Component-Based Architecture**

```
src/
├── lib/
│   ├── components/           # Reusable UI components
│   │   ├── common/          # Generic components (Button, Card, Input)
│   │   ├── layout/          # Layout components (Header, Footer, Container)
│   │   ├── search/          # Search-specific components
│   │   └── filters/         # Filter components
│   ├── api/                 # API client layer
│   ├── stores/              # Svelte stores (state management)
│   └── utils/               # Utility functions
└── routes/                  # SvelteKit pages/routes
    ├── +layout.svelte       # Root layout
    ├── +page.svelte         # Home page
    ├── search/              # Search page
    ├── dataset/[id]/        # Dataset detail (dynamic route)
    └── browse/              # Browse/explore page
```

**2. Key Architectural Patterns:**

**a) Presentation Layer (Components)**
- **Atomic Design**: Build from atoms → molecules → organisms
- **Single Responsibility**: Each component does one thing
- **Composability**: Combine small components into larger ones

**b) Data Layer (API Client)**
- **Separation**: API logic separate from components
- **Abstraction**: Hide HTTP details behind clean interfaces
- **Error Handling**: Centralized error handling

**c) State Management (Svelte Stores)**
- **Reactive**: Svelte's reactive stores for global state
- **Derived State**: Computed values from base state
- **Minimal**: Only store what's truly global

**d) Routing (SvelteKit)**
- **File-based**: Routes defined by directory structure
- **SSR-ready**: Server-side rendering support
- **Progressive Enhancement**: Works without JavaScript

---

## Component Hierarchy Design

### Me:
Help me design the component hierarchy. I want to ensure components are reusable and follow best practices.

### Claude:
Absolutely! Let's design a component hierarchy using Atomic Design principles.

**Component Hierarchy:**

```
Common Components (Atoms/Molecules)
├── Button.svelte           # Reusable button with variants
├── Input.svelte            # Form input with validation
├── Card.svelte             # Container card
├── Badge.svelte            # Label/tag component
├── Loading.svelte          # Loading spinner
├── Modal.svelte            # Modal dialog
└── Toast.svelte            # Notification toast

Layout Components (Organisms)
├── Navigation.svelte       # Top navigation bar
├── Footer.svelte           # Page footer
└── Container.svelte        # Content container with responsive sizing

Search Components (Organisms)
├── SearchBar.svelte        # Main search input
├── ResultCard.svelte       # Individual search result
└── ResultList.svelte       # List of search results (optional)

Filter Components (Organisms)
├── FilterPanel.svelte      # Complete filter sidebar
├── FilterChips.svelte      # Active filter chips/tags
└── DateRangePicker.svelte  # Date range selection
```

**Design Principles:**

**1. Atoms (Basic Building Blocks):**

```svelte
<!-- Button.svelte -->
<script>
  export let variant = 'primary'; // primary, secondary, outline
  export let size = 'md'; // sm, md, lg
  export let disabled = false;
  export let loading = false;
  export let type = 'button';
  
  // Computed CSS classes based on props
  $: classes = `btn btn-${variant} btn-${size}`;
</script>

<button
  class={classes}
  {disabled}
  {type}
  on:click
  class:loading
>
  {#if loading}
    <span class="spinner"></span>
  {/if}
  <slot />
</button>

<style>
  /* Tailwind utility classes or custom styles */
  .btn {
    @apply px-4 py-2 rounded font-medium transition-colors;
  }
  
  .btn-primary {
    @apply bg-primary-600 text-white hover:bg-primary-700;
  }
  
  .btn-secondary {
    @apply bg-gray-200 text-gray-800 hover:bg-gray-300;
  }
</style>
```

**2. Molecules (Simple Combinations):**

```svelte
<!-- Input.svelte -->
<script>
  export let value = '';
  export let placeholder = '';
  export let type = 'text';
  export let error = '';
  export let label = '';
  
  // Two-way binding support
  function handleInput(e) {
    value = e.target.value;
  }
</script>

<div class="input-group">
  {#if label}
    <label class="input-label">{label}</label>
  {/if}
  
  <input
    {type}
    {placeholder}
    {value}
    on:input={handleInput}
    class:error={!!error}
    class="input-field"
  />
  
  {#if error}
    <span class="error-message">{error}</span>
  {/if}
</div>
```

**3. Organisms (Complex Components):**

```svelte
<!-- SearchBar.svelte -->
<script>
  import Button from '../common/Button.svelte';
  import Input from '../common/Input.svelte';
  
  export let value = '';
  export let onSearch = () => {};
  export let loading = false;
  export let placeholder = 'Search datasets...';
  
  function handleSubmit(e) {
    e.preventDefault();
    if (value.trim()) {
      onSearch();
    }
  }
</script>

<form on:submit={handleSubmit} class="search-bar">
  <div class="search-input-wrapper">
    <Input
      bind:value
      {placeholder}
      type="search"
    />
    
    <Button
      type="submit"
      {loading}
      variant="primary"
    >
      {#if loading}
        Searching...
      {:else}
        Search
      {/if}
    </Button>
  </div>
</form>
```

**Key Design Decisions:**

1. **Props vs Slots:**
   - Use props for data and configuration
   - Use slots for content composition

2. **Event Handling:**
   - Use `on:click` for event forwarding (allows parent to handle)
   - Export callback functions when component needs to control behavior

3. **Styling Strategy:**
   - Tailwind CSS for utility classes
   - Component-scoped styles for complex styling
   - CSS variables for theming

4. **State Management:**
   - Local state in component (using `let`)
   - Global state in stores (for cross-component data)
   - Props for parent-child communication

---

## API Client Architecture

### Me:
How should I structure the API client layer? I want clean separation between the frontend and backend communication.

### Claude:
Excellent question! Let's create a clean API abstraction layer.

**API Client Architecture:**

```javascript
// lib/api/client.js
/**
 * Base API client with common configuration.
 * Provides centralized error handling and request configuration.
 */

import axios from 'axios';

// Base configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance with defaults
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (for auth tokens, logging, etc.)
apiClient.interceptors.request.use(
  (config) => {
    // Add timestamp for debugging
    config.metadata = { startTime: new Date() };
    console.log(`[API] ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor (for error handling, logging, etc.)
apiClient.interceptors.response.use(
  (response) => {
    // Calculate request duration
    const duration = new Date() - response.config.metadata.startTime;
    console.log(`[API] ✓ ${response.config.url} (${duration}ms)`);
    
    // Return just the data
    return response.data;
  },
  (error) => {
    // Log error
    console.error(`[API] ✗ ${error.config?.url}`, error.message);
    
    // Transform error into user-friendly message
    const errorMessage = error.response?.data?.detail || error.message || 'An error occurred';
    return Promise.reject(new Error(errorMessage));
  }
);

export default apiClient;
```

**Domain-Specific API Modules:**

```javascript
// lib/api/search.js
/**
 * Search API endpoints.
 * Provides clean interface for search operations.
 */

import apiClient from './client';

export const searchAPI = {
  /**
   * Semantic search for datasets.
   * 
   * @param {string} query - Search query
   * @param {number} topK - Number of results to return
   * @returns {Promise<Object>} Search results with metadata
   */
  semantic: async (query, topK = 10) => {
    return apiClient.post('/search/semantic', {
      query,
      top_k: topK
    });
  },

  /**
   * Enriched semantic search (includes full metadata).
   * 
   * @param {string} query - Search query
   * @param {number} topK - Number of results
   * @returns {Promise<Object>} Enriched search results
   */
  semanticEnriched: async (query, topK = 10) => {
    return apiClient.post('/search/semantic/enriched', {
      query,
      top_k: topK
    });
  },

  /**
   * Hybrid search with filters.
   * 
   * @param {Object} params - Search parameters
   * @param {string} params.query - Search query
   * @param {number} params.top_k - Number of results
   * @param {Array} params.authors - Filter by authors
   * @param {Array} params.keywords - Filter by keywords
   * @param {string} params.start_date - Filter by start date
   * @param {string} params.end_date - Filter by end date
   * @returns {Promise<Object>} Filtered search results
   */
  hybrid: async (params) => {
    return apiClient.post('/search/hybrid', params);
  }
};
```

```javascript
// lib/api/datasets.js
/**
 * Dataset API endpoints.
 * CRUD operations for datasets.
 */

import apiClient from './client';

export const datasetsAPI = {
  /**
   * Get dataset by ID.
   */
  getById: async (id) => {
    return apiClient.get(`/datasets/${id}`);
  },

  /**
   * List all datasets with pagination.
   */
  list: async (page = 1, pageSize = 20) => {
    return apiClient.get('/datasets', {
      params: { page, page_size: pageSize }
    });
  },

  /**
   * Get dataset metadata formats.
   */
  getMetadata: async (id, format = 'json') => {
    return apiClient.get(`/datasets/${id}/metadata/${format}`);
  }
};
```

```javascript
// lib/api/stats.js
/**
 * Statistics API endpoints.
 */

import apiClient from './client';

export const statsAPI = {
  /**
   * Get database statistics.
   */
  getStats: async () => {
    return apiClient.get('/stats');
  }
};
```

**Benefits of This Architecture:**

1. **Centralized Configuration**: All API settings in one place
2. **Type Safety**: JSDoc comments provide IDE autocomplete
3. **Error Handling**: Consistent error transformation
4. **Logging**: Automatic request/response logging
5. **Testability**: Easy to mock API modules
6. **Maintainability**: One place to update API contracts

**Usage in Components:**

```svelte
<script>
  import { searchAPI } from '$lib/api/search';
  
  let query = '';
  let results = [];
  let loading = false;
  let error = null;
  
  async function performSearch() {
    loading = true;
    error = null;
    
    try {
      const response = await searchAPI.semantic(query, 20);
      results = response.results;
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }
</script>
```

---

## State Management with Svelte Stores

### Me:
How should I handle state management? The application needs to manage search state, filter state, and potentially user preferences. What's the best approach with Svelte?

### Claude:
Great question! Svelte's stores are perfect for this. Let's design a clean state management system.

**State Management Strategy:**

**1. Writable Stores (Base State):**

```javascript
// lib/stores/search.js
/**
 * Search state management.
 * Manages search query, results, and loading states.
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

// Search history (for recent searches)
export const searchHistory = writable([]);

/**
 * Add search to history.
 */
export function addToHistory(query) {
  searchHistory.update(history => {
    // Add to beginning, limit to 10 items, remove duplicates
    const updated = [query, ...history.filter(q => q !== query)].slice(0, 10);
    
    // Persist to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('searchHistory', JSON.stringify(updated));
    }
    
    return updated;
  });
}

/**
 * Clear search history.
 */
export function clearHistory() {
  searchHistory.set([]);
  if (typeof window !== 'undefined') {
    localStorage.removeItem('searchHistory');
  }
}

/**
 * Load search history from localStorage.
 */
export function loadHistory() {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('searchHistory');
    if (stored) {
      try {
        searchHistory.set(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to load search history:', e);
      }
    }
  }
}
```

**2. Derived Stores (Computed State):**

```javascript
// lib/stores/filters.js
/**
 * Filter state management with computed values.
 */

import { writable, derived } from 'svelte/store';

// Create writable store for filters
function createFiltersStore() {
  const { subscribe, set, update } = writable({
    query: '',
    authors: [],
    organizations: [],
    keywords: [],
    formats: [],
    startDate: null,
    endDate: null
  });

  return {
    subscribe,
    set,
    update,
    
    // Helper methods
    addAuthor: (author) => update(f => ({
      ...f,
      authors: [...f.authors, author]
    })),
    
    removeAuthor: (author) => update(f => ({
      ...f,
      authors: f.authors.filter(a => a !== author)
    })),
    
    addKeyword: (keyword) => update(f => ({
      ...f,
      keywords: [...f.keywords, keyword]
    })),
    
    removeKeyword: (keyword) => update(f => ({
      ...f,
      keywords: f.keywords.filter(k => k !== keyword)
    })),
    
    setDateRange: (start, end) => update(f => ({
      ...f,
      startDate: start,
      endDate: end
    })),
    
    reset: () => set({
      query: '',
      authors: [],
      organizations: [],
      keywords: [],
      formats: [],
      startDate: null,
      endDate: null
    })
  };
}

export const filters = createFiltersStore();

// Derived store: check if any filters are active
export const hasActiveFilters = derived(
  filters,
  $filters => {
    return $filters.authors.length > 0 ||
           $filters.organizations.length > 0 ||
           $filters.keywords.length > 0 ||
           $filters.formats.length > 0 ||
           $filters.startDate !== null ||
           $filters.endDate !== null;
  }
);

// Derived store: count active filters
export const activeFilterCount = derived(
  filters,
  $filters => {
    let count = 0;
    count += $filters.authors.length;
    count += $filters.organizations.length;
    count += $filters.keywords.length;
    count += $filters.formats.length;
    if ($filters.startDate || $filters.endDate) count += 1;
    return count;
  }
);

/**
 * Build API parameters from filter state.
 */
export function buildFilterParams($filters) {
  const params = {};
  
  if ($filters.authors.length > 0) {
    params.authors = $filters.authors;
  }
  
  if ($filters.organizations.length > 0) {
    params.organizations = $filters.organizations;
  }
  
  if ($filters.keywords.length > 0) {
    params.keywords = $filters.keywords;
  }
  
  if ($filters.formats.length > 0) {
    params.formats = $filters.formats;
  }
  
  if ($filters.startDate) {
    params.start_date = $filters.startDate;
  }
  
  if ($filters.endDate) {
    params.end_date = $filters.endDate;
  }
  
  return params;
}

/**
 * Reset all filters.
 */
export function resetFilters() {
  filters.reset();
}
```

**3. Usage in Components:**

```svelte
<script>
  import { filters, hasActiveFilters, activeFilterCount } from '$lib/stores/filters';
  import { searchQuery, searchResults, isSearching } from '$lib/stores/search';
  
  // Subscribe to stores ($ prefix for auto-subscription)
  $: query = $searchQuery;
  $: results = $searchResults;
  $: loading = $isSearching;
  $: hasFilters = $hasActiveFilters;
  $: filterCount = $activeFilterCount;
  
  // Update store
  function updateQuery(value) {
    searchQuery.set(value);
  }
  
  function addFilter(type, value) {
    if (type === 'author') {
      filters.addAuthor(value);
    } else if (type === 'keyword') {
      filters.addKeyword(value);
    }
  }
</script>

<div>
  <p>Query: {query}</p>
  <p>Results: {results.length}</p>
  <p>Active Filters: {filterCount}</p>
  
  {#if hasFilters}
    <button on:click={() => resetFilters()}>Clear Filters</button>
  {/if}
</div>
```

**Store Benefits:**

1. **Reactive**: Automatic UI updates when state changes
2. **Global**: Access state from any component
3. **Derived**: Computed values automatically update
4. **Minimal**: Only store what needs to be shared
5. **Type-Safe**: Can add TypeScript for full type safety

**When to Use Stores vs Props:**

| Use Stores | Use Props |
|------------|-----------|
| Search query | Component-specific text |
| Filter state | Button variant/size |
| User preferences | Display mode toggle |
| Global UI state | Local form state |

This architecture provides clean, predictable state management!