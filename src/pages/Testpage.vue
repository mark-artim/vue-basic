<template>
  <div class="TestPage">
    <h1>Test Page</h1>
    <p>This is a test page to check the functionality of Vue components.</p>

    <div class="search-form">
      <div class="form-group">
        <label for="edsPn">Ship To ID:</label>
        <input
          id="edsPn"
          v-model="edsPn"
          type="text"
          placeholder="Enter an Ed's Product ID"
          @keyup.enter="fetchXref"
        >
      </div>
      <button
        :disabled="isLoading"
        @click="fetchXref"
      >
        {{ isLoading ? 'Loading...' : 'Search' }}
      </button>
      <p
        v-if="error"
        class="error"
      >
        {{ error }}
      </p>
    </div>
    <div
      v-if="xrefResult"
      class="result-box"
    >
      <h3>Cross Reference Result:</h3>
      <ul>
        <li><strong>@ID:</strong> {{ xrefResult['@ID'] }}</li>
        <li><strong>File Name:</strong> {{ xrefResult.FileName }}</li>
        <li><strong>HER PN:</strong> {{ xrefResult.HER_PN }}</li>
        <li><strong>ID:</strong> {{ xrefResult.id }}</li>
      </ul>
    </div>
    <div
      v-else-if="!isLoading && searchExecuted"
      class="no-results"
    >
      No cross reference found for the provided Ed's Product ID.
    </div>
  </div>
</template>

<script>
import apiClient from '@/utils/axios';
import { getUserDefined } from '@/api/userdefined';
import { omit } from 'lodash-es';
import { useAuthStore } from '@/stores/auth';

export default {
    name: 'Testpage',
    data() {
        return {
            edsPn: '',
            xrefResult: null,
            isLoading: false,
            error: '',
            searchExecuted: false
        };
    },
    methods: {
        async fetchXref() {
          const authStore = useAuthStore();
            if (!this.edsPn) {
                this.error = 'Please enter an Eds Part Number';
                return;
            }
            try {
                const response = await getUserDefined(`EDS.PN.XREF?id=${this.edsPn}`);
                this.xrefResult = response;
                this.error = '';
                this.searchExecuted = true;
                this.isLoading = false;
                if (authStore.apiLogging) {console.log('📦 Raw results:', response);}
                if (authStore.apiLogging) {console.log('logging:', authStore.apiLogging);}
            } catch (error) {
                this.error = 'Failed to retrieve cross reference.';
                console.error('[ERROR] XREF fetch failed:', error);
            }
        },




    }
};
</script>

<style scoped>
h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

p {
  color: #444;
}

.TestPage {
  max-width: 800px;
  margin: 1.5rem;
}

.search-form {
  margin-top: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 1rem;
}

input[type="text"] {
  padding: 0.5rem;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  margin-top: 0.25rem;
}

button {
  padding: 0.5rem 1rem;
  font-size: 1rem;
  border: none;
  background-color: #007bff;
  color: white;
  border-radius: 6px;
  cursor: pointer;
}

button[disabled] {
  background-color: #6c757d;
  cursor: not-allowed;
}

.error {
  color: red;
  margin-top: 0.5rem;
}

.result-box {
  margin-top: 2rem;
  padding: 1rem;
  /* background-color: #f1f9f1; */
  border-left: 4px solid #28a745;
  border-radius: 8px;
}

.result-box h3 {
  margin-bottom: 1rem;
}

.result-box ul {
  list-style: none;
  padding-left: 0;
}

.result-box li {
  margin-bottom: 0.5rem;
}

.no-results {
  margin-top: 2rem;
  color: #999;
  font-style: italic;
}
</style>
