# Frontend Architecture

## Overview

The frontend is a modern web application built with **SvelteKit** and **TailwindCSS**, providing an intuitive interface for semantic dataset search and discovery. It follows component-based architecture with clear separation between presentation, state management, and business logic.

## Directory Structure

```
frontend/
├── src/
│   ├── lib/                              # Reusable components
│   │   ├── components/                   # UI components
│   │   │   ├── common/                   # Generic components
│   │   │   │   ├── Button.svelte
│   │   │   │   ├── Card.svelte
│   │   │   │   ├── Input.svelte
│   │   │   │   ├── Modal.svelte
│   │   │   │   ├── Loading.svelte
│   │   │   │   └── Badge.svelte
│   │   │   ├── layout/                   # Layout components
│   │   │   │   ├── Navigation.svelte
│   │   │   │   ├── Footer.svelte
│   │   │   │   └── Container.svelte
│   │   │   ├── search/                   # Search components
│   │   │   │   ├── SearchBar.svelte
│   │   │   │   └── ResultCard.svelte
│   │   │   └── filters/                  # Filter components
│   │   │       ├── FilterPanel.svelte
│   │   │       └── FilterChips.svelte
│   │   ├── stores/                       # State management
│   │   │   ├── search.js
│   │   │   └── filters.js
│   │   ├── api/                          # API client
│   │   │   ├── client.js
│   │   │   ├── datasets.js
│   │   │   ├── search.js
│   │   │   └── stats.js
│   │   └── utils/                        # Utility functions
│   │       ├── format.js
│   │       └── dateRange.js
│   │
│   └── routes/                           # SvelteKit pages
│       ├── +layout.svelte                # Root layout
│       ├── +page.svelte                  # Home (/)
│       ├── search/+page.svelte           # /search
│       ├── browse/+page.svelte           # /browse
│       ├── dataset/[id]/+page.svelte     # /dataset
│       ├── dashboard/+page.svelte        # /dashboard
│       └── about/+page.svelte            # /about
│
├── package.json                          # Dependencies
├── svelte.config.js                      # SvelteKit config
├── vite.config.js                        # Vite config
└── tailwind.config.js                    # TailwindCSS config
```

## Architectural Patterns

### 1. Component-Based Architecture

**Philosophy**: Break UI into reusable, composable components

**Component Hierarchy**:
```
App
├── Layout (Navigation + Footer)
│   └── Page Components
│       ├── SearchPage
│       │   ├── SearchBar
│       │   ├── FilterPanel
│       │   ├── FilterChips
│       │   └── ResultCard (repeated)
│       ├── BrowsePage
│       ├── DashboardPage
│       └── AboutPage
```

**Component Categories**:

1. **Common Components**: Generic, reusable across the app
   - Button, Card, Input, Modal, Toast
   - Skeleton (loading state)
   - Badge, MultiSelect

2. **Layout Components**: Define page structure
   - Navigation: Top navigation bar
   - Footer: Site footer
   - Container: Content wrapper

3. **Feature Components**: Domain-specific
   - SearchBar: Query input with search button
   - ResultCard: Dataset display card
   - FilterPanel: Advanced filter controls
   - FilterChips: Active filter display

**Why This Architecture**: Maximizes code reuse, enables independent testing, and provides clear component responsibilities.

### 2. Reactive State Management

**Tool**: Svelte Stores (built-in state management)

**Store Architecture**:
```javascript
// search.js
export const searchQuery = writable('');
export const searchResults = writable([]);
export const isSearching = writable(false);
export const searchError = writable(null);

// filters.js
export const activeFilters = writable({
  keywords: [],
  dateRange: null,
  spatialBounds: null
});
```

**Reactive Patterns**:
```svelte
<script>
  import { searchQuery, searchResults } from '$lib/stores/search';
  
  // Automatically reacts to store changes
  $: console.log('Query changed:', $searchQuery);
  $: resultCount = $searchResults.length;
</script>

<p>Found {resultCount} results for "{$searchQuery}"</p>
```

**Why Svelte Stores**: Simple API, built-in reactivity, no external dependencies, type-safe with TypeScript.

### 3. API Client Layer

**Purpose**: Abstract backend communication, provide type-safe API

**Client Structure**:
```javascript
// client.js - Base configuration
import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptors for global error handling
client.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error);
    throw error;
  }
);

export default client;
```

**Endpoint Modules**:
```javascript
// search.js
import client from './client';

export const searchAPI = {
  semantic: async (query, topK = 10) => {
    const response = await client.post('/search/semantic', {
      query,
      top_k: topK
    });
    return response.data;
  },
  
  combined: async (query, filters) => {
    const response = await client.post('/search/combined', {
      query,
      filters
    });
    return response.data;
  }
};
```

**Why This Pattern**: Centralized API logic, easy to mock for testing, clear separation from UI components.

## Key Features Implementation

### 1. Semantic Search

**Component**: `SearchBar.svelte`

```svelte
<script>
  import { searchQuery, searchResults, isSearching } from '$lib/stores/search';
  import { searchAPI } from '$lib/api/search';
  
  let query = '';
  
  async function handleSearch() {
    if (!query.trim()) return;
    
    $isSearching = true;
    $searchQuery = query;
    
    try {
      const data = await searchAPI.semantic(query);
      $searchResults = data.results;
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      $isSearching = false;
    }
  }
</script>

<div class="search-bar">
  <input
    bind:value={query}
    on:keydown={(e) => e.key === 'Enter' && handleSearch()}
    placeholder="Search datasets..."
    class="input"
  />
  <button on:click={handleSearch} disabled={$isSearching}>
    {$isSearching ? 'Searching...' : 'Search'}
  </button>
</div>
```

**Features**:
- Real-time query binding
- Loading states
- Keyboard support (Enter to search)
- Error handling

**Why This Design**: Simple, intuitive, provides immediate feedback to users.

### 2. Filter System

**Component**: `FilterPanel.svelte`

```svelte
<script>
  import { activeFilters } from '$lib/stores/filters';
  import MultiSelect from '$lib/components/common/MultiSelect.svelte';
  import DateRangePicker from '$lib/components/common/DateRangePicker.svelte';
  
  let keywordOptions = ['climate', 'hydrology', 'ecology', 'soil'];
  
  function applyFilters() {
    // Trigger filtered search
    dispatchEvent(new CustomEvent('filtersApplied', {
      detail: $activeFilters
    }));
  }
</script>

<aside class="filter-panel">
  <h3>Filters</h3>
  
  <div class="filter-section">
    <label>Keywords</label>
    <MultiSelect
      options={keywordOptions}
      bind:selected={$activeFilters.keywords}
    />
  </div>
  
  <div class="filter-section">
    <label>Date Range</label>
    <DateRangePicker bind:value={$activeFilters.dateRange} />
  </div>
  
  <button on:click={applyFilters}>Apply Filters</button>
</aside>
```

**Features**:
- Multi-select keywords
- Date range picker
- Real-time filter state
- Custom events for communication

**Why This Design**: Separates filter UI from search logic, making both independently testable.

### 3. Result Display

**Component**: `ResultCard.svelte`

```svelte
<script>
  export let dataset;
  export let score = null;
  
  import { formatDate } from '$lib/utils/format';
  import Badge from '$lib/components/common/Badge.svelte';
</script>

<article class="result-card">
  <header>
    <h3>{dataset.title}</h3>
    {#if score}
      <Badge variant="success">Match: {(score * 100).toFixed(1)}%</Badge>
    {/if}
  </header>
  
  <p class="abstract">{dataset.abstract || 'No description available'}</p>
  
  <footer>
    <div class="keywords">
      {#each dataset.keywords.slice(0, 5) as keyword}
        <Badge>{keyword.keyword}</Badge>
      {/each}
    </div>
    
    <div class="metadata">
      <span>Published: {formatDate(dataset.publication_date)}</span>
      <span>{dataset.contacts.length} contacts</span>
    </div>
  </footer>
  
  <a href="/datasets/{dataset.id}" class="view-details">View Details</a>
</article>
```

**Features**:
- Relevance score display
- Truncated abstract
- Keyword badges
- Metadata summary
- Link to detail view

**Why This Design**: Self-contained component that can be used in different contexts (search results, related datasets, etc.).

### 4. Loading States

**Component**: `Skeleton.svelte`

```svelte
<script>
  export let type = 'card'; // 'card', 'list', 'text'
  export let count = 1;
</script>

{#if type === 'card'}
  {#each Array(count) as _}
    <div class="skeleton-card">
      <div class="skeleton-title"></div>
      <div class="skeleton-text"></div>
      <div class="skeleton-text"></div>
      <div class="skeleton-footer"></div>
    </div>
  {/each}
{/if}

<style>
  .skeleton-card {
    background: #f0f0f0;
    border-radius: 8px;
    padding: 1rem;
    animation: pulse 1.5s ease-in-out infinite;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
</style>
```

**Usage**:
```svelte
{#if $isSearching}
  <Skeleton type="card" count={3} />
{:else}
  {#each $searchResults as result}
    <ResultCard dataset={result.dataset} score={result.score} />
  {/each}
{/if}
```

**Why This Approach**: Provides visual feedback during loading, improves perceived performance.

## Styling Strategy

### TailwindCSS Integration

**Configuration**: `tailwind.config.js`
```javascript
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          500: '#3b82f6',
          700: '#1d4ed8'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif']
      }
    }
  }
};
```

**Why TailwindCSS**: Utility-first approach speeds development, consistent design system, no CSS conflicts.

**Utility-First Approach**:
```svelte
<button class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-700 transition">
  Search
</button>
```

**Responsive Design**:
```svelte
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <!-- Responsive grid: 1 col on mobile, 2 on tablet, 3 on desktop -->
</div>
```

**Why This Approach**: Mobile-first design, clear breakpoints, maintainable responsive layouts.

## Routing & Navigation

### SvelteKit Routing

**File-based Routing**:
```
routes/
├── +page.svelte           → /
├── search/
│   └── +page.svelte       → /search
├── browse/
│   └── +page.svelte       → /browse
├── datasets/
│   └── [id]/
│       └── +page.svelte   → /datasets/:id (dynamic)
```

**Why File-based Routing**: Intuitive structure, automatic code splitting, clear mapping of URLs to components.

**Navigation Component**:
```svelte
<script>
  import { page } from '$app/stores';
</script>

<nav>
  <a href="/" class:active={$page.url.pathname === '/'}>Home</a>
  <a href="/search" class:active={$page.url.pathname === '/search'}>Search</a>
  <a href="/browse" class:active={$page.url.pathname === '/browse'}>Browse</a>
  <a href="/dashboard" class:active={$page.url.pathname === '/dashboard'}>Dashboard</a>
</nav>

<style>
  .active {
    font-weight: bold;
    border-bottom: 2px solid currentColor;
  }
</style>
```

**Why This Pattern**: Built-in active state tracking, client-side navigation, progressive enhancement.

<details>
<summary><b>Dynamic Routes Example (click to expand)</b></summary>

### Dataset Detail Page

**Location**: `routes/datasets/[id]/+page.svelte`

```svelte
<script>
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { datasetsAPI } from '$lib/api/datasets';
  
  let dataset = null;
  let loading = true;
  
  onMount(async () => {
    try {
      const data = await datasetsAPI.getById($page.params.id);
      dataset = data.dataset;
    } catch (error) {
      console.error('Failed to load dataset:', error);
    } finally {
      loading = false;
    }
  });
</script>

{#if loading}
  <Skeleton type="card" />
{:else if dataset}
  <article>
    <h1>{dataset.title}</h1>
    <p>{dataset.abstract}</p>
    <!-- More details -->
  </article>
{:else}
  <p>Dataset not found</p>
{/if}
```

**Why This Approach**: Clean URL structure, automatic route parameters, lifecycle hooks for data loading.

</details>

## State Management Patterns

### 1. Component State (Local)

For component-specific state:
```svelte
<script>
  let isOpen = false; // Local to this component
  let inputValue = '';
</script>
```

**When to Use**: State only relevant to single component, doesn't need sharing.

### 2. Store State (Global)

For shared state across components:
```javascript
// stores/search.js
import { writable, derived } from 'svelte/store';

export const searchResults = writable([]);
export const searchQuery = writable('');

// Derived store - automatically computed
export const resultCount = derived(
  searchResults,
  $results => $results.length
);
```

**When to Use**: State needed by multiple components, application-wide data.

### 3. URL State (Shareable)

For state that should be shareable via URL:
```svelte
<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  
  $: query = $page.url.searchParams.get('q') || '';
  
  function updateQuery(newQuery) {
    goto(`/search?q=${encodeURIComponent(newQuery)}`);
  }
</script>
```

**When to Use**: State users might want to bookmark or share (search queries, filters).

**Why These Patterns**: Different state has different lifecycles and scopes. Using appropriate pattern for each case improves maintainability.

## Performance Optimizations

### 1. Lazy Loading

```svelte
<script>
  import { onMount } from 'svelte';
  
  let HeavyComponent;
  
  onMount(async () => {
    const module = await import('./HeavyComponent.svelte');
    HeavyComponent = module.default;
  });
</script>

{#if HeavyComponent}
  <svelte:component this={HeavyComponent} />
{/if}
```

**Why**: Reduces initial bundle size, faster first paint.

### 2. Debounced Search

```svelte
<script>
  import { debounce } from '$lib/utils/debounce';
  
  let query = '';
  
  const debouncedSearch = debounce(async (q) => {
    const results = await searchAPI.semantic(q);
    $searchResults = results;
  }, 300);
  
  $: if (query.length > 2) {
    debouncedSearch(query);
  }
</script>

<input bind:value={query} placeholder="Search..." />
```

**Why**: Reduces API calls, better performance, improved UX.

<details>
<summary><b>Virtual Scrolling (for large lists) - Click to expand</b></summary>

```svelte
<script>
  let visibleItems = [];
  let scrollTop = 0;
  const itemHeight = 200;
  const containerHeight = 800;
  
  $: {
    const startIndex = Math.floor(scrollTop / itemHeight);
    const endIndex = Math.ceil((scrollTop + containerHeight) / itemHeight);
    visibleItems = items.slice(startIndex, endIndex);
  }
</script>

<div on:scroll={(e) => scrollTop = e.target.scrollTop} style="height: {containerHeight}px; overflow-y: auto;">
  <div style="height: {items.length * itemHeight}px; position: relative;">
    {#each visibleItems as item, i}
      <div style="position: absolute; top: {(startIndex + i) * itemHeight}px;">
        <ResultCard {item} />
      </div>
    {/each}
  </div>
</div>
```

**Why**: Renders only visible items, handles thousands of results smoothly.

</details>

## Error Handling

### API Error Boundaries

```svelte
<script>
  import { onMount } from 'svelte';
  import Toast from '$lib/components/common/Toast.svelte';
  
  let error = null;
  let showToast = false;
  
  async function fetchData() {
    try {
      const data = await datasetsAPI.list();
      // Process data
    } catch (err) {
      error = err.message;
      showToast = true;
    }
  }
</script>

{#if showToast}
  <Toast message={error} variant="error" on:close={() => showToast = false} />
{/if}
```

**Why This Approach**: User-friendly error messages, non-blocking errors, consistent error presentation.

## Accessibility (a11y)

### Semantic HTML

```svelte
<nav aria-label="Main navigation">
  <ul>
    <li><a href="/">Home</a></li>
    <li><a href="/search">Search</a></li>
  </ul>
</nav>

<main id="main-content">
  <h1>Search Results</h1>
  <section aria-labelledby="results-heading">
    <h2 id="results-heading">Found {count} datasets</h2>
    <!-- Results -->
  </section>
</main>
```

**Why**: Screen reader compatibility, keyboard navigation, semantic structure.

### Keyboard Navigation

```svelte
<script>
  function handleKeydown(event) {
    if (event.key === 'Enter' || event.key === ' ') {
      handleClick();
    }
  }
</script>

<div
  role="button"
  tabindex="0"
  on:click={handleClick}
  on:keydown={handleKeydown}
>
  Click me
</div>
```

**Why**: Keyboard-only users can navigate, WCAG compliance.

### ARIA Labels

```svelte
<button aria-label="Search datasets" aria-pressed={isSearching}>
  {#if isSearching}
    <span aria-live="polite">Searching...</span>
  {:else}
    Search
  {/if}
</button>

<input
  type="text"
  aria-describedby="search-help"
  aria-required="true"
/>
<p id="search-help">Enter keywords to find relevant datasets</p>
```

**Why**: Assistive technology support, better user experience for all users.

## Code Quality

### Component Documentation

All components include:
- Purpose comment
- Props documentation
- Event documentation
- Usage examples

**Example**:
```svelte
<!--
  SearchBar Component
  
  Purpose: Provides semantic search input with loading states
  
  Props:
    - placeholder (string): Input placeholder text
    - disabled (boolean): Disable input
  
  Events:
    - search: Emitted when search is triggered
  
  Usage:
    <SearchBar on:search={handleSearch} />
-->
```

**Why**: Improves maintainability, helps other developers understand component purpose.