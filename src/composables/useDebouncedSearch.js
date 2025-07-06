import { ref } from 'vue'
import { debounce } from 'lodash-es'

export function useDebouncedSearch (fetchFn, delay = 300) {
  const searchTerm = ref('')
  const results = ref([])
  const isLoading = ref(false)

  const doFetch = async term => {
    if (!term) {
      results.value = []
      isLoading.value = false
      return
    }
    isLoading.value = true
    try {
      results.value = await fetchFn(term)
    } catch (err) {
      console.error('[useDebouncedSearch] fetch failed:', err)
      results.value = []
    } finally {
      isLoading.value = false
    }
  }

  const debouncedFetch = debounce(doFetch, delay)

  const onSearch = (evtOrString) => {
    const term = typeof evtOrString === 'string'
      ? evtOrString
      : evtOrString?.target?.value || ''
    searchTerm.value = term
    debouncedFetch(term)
  }

  const clear = () => {
    searchTerm.value = ''
    results.value = []
    isLoading.value = false
  }

  return { searchTerm, results, isLoading, onSearch, clear }
}
