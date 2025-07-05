<template>
  <v-container class="pa-4">
    <h2 class="mb-4">Wasabi File Manager</h2>

    <!-- Upload Section -->
    <v-file-input
      v-model="selectedFile"
      label="Upload a file (.csv, .txt, .pdf)"
      accept=".csv,.txt,.pdf"
      outlined
      class="mb-4"
    />

    <v-btn
      :disabled="!selectedFile"
      color="primary"
      @click="uploadFile"
      :loading="uploading"
      class="mb-6"
    >
      Upload
    </v-btn>

    <!-- File List -->
    <h3>Stored Files</h3>

    <v-list v-if="files.length" class="border rounded">
      <v-list-item
        v-for="file in files"
        :key="file.key"
        class="d-flex justify-space-between"
      >
        <span>{{ file.key }}</span>
        <v-btn icon @click="deleteFile(file.key)">
          <v-icon color="red">mdi-delete</v-icon>
        </v-btn>
      </v-list-item>
    </v-list>
    <div v-else class="text-grey mt-4">No files found in Wasabi bucket.</div>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from '@/utils/axios'

const selectedFile = ref(null)
const uploading = ref(false)
const files = ref([])

const fetchFiles = async () => {
  try {
    const res = await axios.get('/wasabi/list');
    files.value = (res.data.files || []).filter(file => !file.key.startsWith('log-')); // ❌ Filter out log files
  } catch (err) {
    console.error('❌ Failed to fetch files:', err);
  }
};


const uploadFile = async () => {
  if (!selectedFile.value) return;

  const formData = new FormData();
  formData.append('file', selectedFile.value);

  try {
    const response = await axios.post('/wasabi/upload', formData);
    console.log('✅ Upload success:', response.data);
    selectedFile.value = null; // Clear the file input
    fetchFiles(); // Refresh the file list
  } catch (error) {
    console.error('❌ Upload failed:', error);
  }
};


const deleteFile = async (filename) => {
  try {
    await axios.delete('/wasabi/delete', { data: { key: filename } })
    await fetchFiles()
  } catch (err) {
    console.error('❌ Delete failed:', err)
  }
}

onMounted(fetchFiles)
</script>
