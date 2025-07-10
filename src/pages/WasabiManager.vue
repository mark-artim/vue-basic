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

    <v-data-table
      v-if="files.length"
      :headers="headers"
      :items="files"
      class="elevation-1"
    >
      <template #item.lastModified="{ item }">
        {{ new Date(item.lastModified).toLocaleString() }}
      </template>
      <template #item.size="{ item }">
        {{ formatSize(item.size) }}
      </template>
      <template #item.actions="{ item }">
        <v-btn icon @click="downloadFile(item)">
          <v-icon>mdi-download</v-icon>
        </v-btn>
        <v-btn icon @click="openRenameDialog(item)">
          <v-icon>mdi-pencil</v-icon>
        </v-btn>
        <v-btn icon @click="deleteFile(item.key)">
          <v-icon color="red">mdi-delete</v-icon>
        </v-btn>
      </template>
    </v-data-table>
    <div v-else class="text-grey mt-4">No files found in Wasabi bucket.</div>

    <!-- Rename Dialog -->
    <v-dialog v-model="renameDialog" max-width="500">
      <v-card>
        <v-card-title>Rename File</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newFileName"
            label="New filename"
            autofocus
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="closeRenameDialog">Cancel</v-btn>
          <v-btn color="primary" @click="renameFileAction">Rename</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from '@/utils/axios'

const selectedFile = ref(null)
const uploading = ref(false)
const files = ref([])
const headers = [
  { title: 'Name', key: 'key' },
  { title: 'Last Modified', key: 'lastModified' },
  { title: 'Size', key: 'size' },
  { title: 'Actions', key: 'actions', sortable: false }
]

const renameDialog = ref(false)
const renameTarget = ref(null)
const newFileName = ref('')

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

const downloadFile = async (file) => {
  try {
    const res = await axios.get('/wasabi/download', {
      params: { filename: file.key },
      responseType: 'blob'
    })
    const url = URL.createObjectURL(res.data)
    const link = document.createElement('a')
    link.href = url
    link.download = file.key.split('/').pop()
    link.click()
    URL.revokeObjectURL(url)
    await fetchFiles()
  } catch (err) {
    console.error('❌ Download failed:', err)
  }
}

const openRenameDialog = (file) => {
  renameTarget.value = file
  newFileName.value = file.key
  renameDialog.value = true
}

const closeRenameDialog = () => {
  renameDialog.value = false
  renameTarget.value = null
  newFileName.value = ''
}

const renameFileAction = async () => {
  if (!renameTarget.value) return
  try {
    await axios.post('/wasabi/rename', {
      oldKey: renameTarget.value.key,
      newKey: newFileName.value
    })
    closeRenameDialog()
    await fetchFiles()
  } catch (err) {
    console.error('❌ Rename failed:', err)
  }
}

const formatSize = (size) => {
  if (size > 1024 * 1024) {
    return (size / (1024 * 1024)).toFixed(2) + ' MB'
  }
  return (size / 1024).toFixed(2) + ' KB'
}

onMounted(fetchFiles)
</script>
