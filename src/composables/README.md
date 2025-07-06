# Composables

Utility functions that encapsulate reusable logic.

## `useDebouncedSearch`

```js
import { useDebouncedSearch } from '@/composables/useDebouncedSearch'
```

Use this composable to handle debounced search operations. Pass an async function that accepts a search term and returns the resulting items. The composable exposes:

- `searchTerm` – reactive string bound to your input
- `results` – array of fetched items
- `isLoading` – `true` while the search function is running
- `onSearch` – handler for input events or raw strings
- `clear` – reset all state

Example:

```js
const {
  searchTerm,
  results,
  isLoading,
  onSearch
} = useDebouncedSearch(query => apiClient.get(`/Items?keyword=${query}`))
```
