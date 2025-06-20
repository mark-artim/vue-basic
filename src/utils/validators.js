import { ref } from 'vue';
import apiClient from '@/utils/axios'; // your Axios instance

// Synchronous validation
export const validVendorTypes = ['EXP', 'EXP:EMPL','EXP:UTY','INV', 'A-F', 'G-O', 'P-Z', 'LBMX:A-F', 'LBMX:G-O', 'LBMX:N-Z', 'LBMX:NEUCO', 'PC', 'RHEEM', 'EXP-AUTODR'];
export const validateVendorType = (val) => {
    return validVendorTypes.includes(val.toUpperCase());
    };


// Asynchronous autocomplete-based validation
export const useShipViaValidator = () => {
  const suggestions = ref([]);
  const isLoading = ref(false);

  const fetchShipVias = async (keyword) => {
    if (!keyword) {
      suggestions.value = [];
      return;
    }

    isLoading.value = true;
    try {
      const response = await apiClient.get(`/ShipVias?keyword=${encodeURIComponent(keyword)}`);
      suggestions.value = response.data.results || [];
    } catch (error) {
      console.error('Error fetching ShipVias:', error);
      suggestions.value = [];
    } finally {
      isLoading.value = false;
    }
  };

  return {
    suggestions,
    isLoading,
    fetchShipVias
  };
};

// ✅ Hook for TermsList autocomplete
export const useTermsValidator = () => {
  const suggestions = ref([]);
  const isLoading = ref(false);

  const fetchTerms = async (keyword) => {
    if (!keyword) {
      suggestions.value = [];
      return;
    }

    isLoading.value = true;
    try {
      const response = await apiClient.get(`/TermsList?keyword=${encodeURIComponent(keyword)}`);
      suggestions.value = response.data.results || [];
    } catch (error) {
      console.error('Error fetching TermsList:', error);
      suggestions.value = [];
    } finally {
      isLoading.value = false;
    }
  };
};
