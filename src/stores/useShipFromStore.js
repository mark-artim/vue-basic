// src/store/shipFrom.js
import { defineStore } from 'pinia'

export const useShipFromStore = defineStore('shipFrom', {
  state: () => ({
    name: '',
    addressLine1: '',
    addressLine2: '',
    city: '',
    state: '',
    postalCode: '',
    phone: '',
    email: ''
  }),
  actions: {
    setAddress(address) {
      Object.assign(this, address)
    },
    reset() {
      this.name = ''
      this.addressLine1 = ''
      this.addressLine2 = ''
      this.city = ''
      this.state = ''
      this.postalCode = ''
      this.phone = ''
      this.email = ''
    }
  }
})
