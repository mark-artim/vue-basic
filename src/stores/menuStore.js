// /src/store/menuStore.js
import { defineStore } from 'pinia'
import apiClient from '@/utils/axios'

export const useMenuStore = defineStore('menu', {
  state: () => ({
    menus: [], // All menus from Mongo
    loading: false,
    error: null
  }),

  actions: {
    async fetchMenus() {
      this.loading = true
      this.error = null
      try {
        const res = await apiClient.get('/admin/menus') // or /menus if public
        this.menus = res.data
      } catch (err) {
        this.error = err.response?.data?.message || err.message
      } finally {
        this.loading = false
      }
    },

    getRolesByProduct(productCode) {
      return [...new Set(
        this.menus
          .filter(m => m.product === productCode)
          .flatMap(m => m.roles || [])
          .filter(Boolean)
      )]
    }
  }
})
