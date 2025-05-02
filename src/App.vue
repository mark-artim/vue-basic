<template>
  <MainLayout />
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'
import MainLayout from './layouts/MainLayout.vue'

const authStore = useAuthStore()

onMounted(() => {
  // Load any existing session from storage.
  authStore.initialize()
})
</script>

