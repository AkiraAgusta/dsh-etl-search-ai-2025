# Frontend

Modern web interface built with SvelteKit and TailwindCSS for semantic dataset search and discovery.

## Overview

The frontend provides an intuitive interface for:

- **Semantic Search**: Natural language queries with AI-powered relevance
- **Advanced Filtering**: Keywords, date ranges, and spatial bounds
- **Dataset Discovery**: Browse and explore environmental datasets
- **Rich Metadata**: Detailed views with contacts, keywords, and relationships
- **Responsive Design**: Works on desktop, tablet, and mobile

<details>
<summary><b>Technology Stack Details (click to expand)</b></summary>

- **Framework**: SvelteKit 2.0 (File-based routing, SSR support)
- **Language**: JavaScript (ES6+)
- **Styling**: TailwindCSS 3.4 (Utility-first CSS)
- **HTTP Client**: Axios 1.6
- **Build Tool**: Vite 5.0
- **Package Manager**: npm

</details>

## Prerequisites

Before starting, ensure you have:

- **Node.js 18 or higher**
  ```bash
  node --version  # Should show v18.x.x or higher
  ```

- **npm** (comes with Node.js)
  ```bash
  npm --version   # Should show 9.x.x or higher
  ```

- **Backend API running** (see [Backend README](../backend/README.md))
  - API should be accessible at http://localhost:8000

## Installation

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
```

This installs all required packages including SvelteKit, Svelte, TailwindCSS, Axios, and Vite.

**Note**: First-time installation typically takes 2-3 minutes.

### 3. Verify Installation

```bash
npm list --depth=0
```

You should see all dependencies listed without errors.

<details>
<summary><b>Configuration Options (click to expand)</b></summary>

### Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

This creates a `.env` file with:
```bash
VITE_API_URL=http://localhost:8000/api
VITE_APP_NAME=CEH Dataset Discovery
```

</details>

## Development

### Start Development Server

```bash
npm run dev
```

To run on a different port, use the `--port` flag:
```bash
npm run dev --port 3000
```

**Expected output:**
```
  VITE v5.4.21  ready in 342 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### Access the Application

Open your browser to: **http://localhost:3000**

### Hot Module Replacement (HMR)

Changes to code are automatically reflected in the browser without full page reload:

- Edit `.svelte` files → See changes instantly
- Edit CSS → Styles update immediately
- Edit JavaScript → Components re-render

### Development Workflow

1. **Start backend API** (in separate terminal):
   ```bash
   cd backend
   python scripts/start_api.py
   ```

2. **Start frontend dev server**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Make changes** to components in `src/lib/components/`
4. **View changes** automatically in browser

## Project Structure

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

## Architecture

### Component Design Patterns

The frontend demonstrates key architectural patterns:

**Component-Based Architecture** - Modular, reusable UI components
```svelte
<SearchBar on:search={handleSearch} />
<FilterPanel on:apply={handleFilters} />
<ResultCard dataset={result} score={result.score} />
```

**Reactive State Management** - Svelte stores for global state
```javascript
// Automatically reactive
$: console.log('Query changed:', $searchQuery);
$: resultCount = $searchResults.length;
```

**API Client Pattern** - Centralized backend communication
```javascript
// Organized by domain
import { searchAPI } from '$lib/api/search';
import { datasetsAPI } from '$lib/api/datasets';
```

### Routing & Navigation

**File-based Routing** - SvelteKit conventions
```
routes/
├── +page.svelte                 → /
├── search/+page.svelte          → /search
└── datasets/[id]/+page.svelte   → /datasets/:id
```

## Additional Resources

- [SvelteKit Documentation](https://kit.svelte.dev/)
- [TailwindCSS Documentation](https://tailwindcss.com/docs)
- [Vite Documentation](https://vitejs.dev/)
- [Axios Documentation](https://axios-http.com/)