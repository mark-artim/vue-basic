// src/stores/useShipFromStore.js
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useShipFromStore = defineStore('shipFrom', () => {
  const name = ref('')
  const addressLine1 = ref('')
  const addressLine2 = ref('')
  const city = ref('')
  const state = ref('')
  const postalCode = ref('')
  const phone = ref('312-504-3022')
  const email = ref('support@heritagedistribution.com')

  function set(data) {
    name.value = data.name || ''
    addressLine1.value = data.addressLine1 || ''
    addressLine2.value = data.addressLine2 || ''
    city.value = data.city || ''
    state.value = data.state || ''
    postalCode.value = data.postalCode || ''
    phone.value = data.phone || '312-504-3022'
    email.value = data.email || 'support@heritagedistribution.com'

    localStorage.setItem('shipFrom', JSON.stringify({
      name: name.value,
      addressLine1: addressLine1.value,
      addressLine2: addressLine2.value,
      city: city.value,
      state: state.value,
      postalCode: postalCode.value,
      phone: phone.value,
      email: email.value
    }))
  }

  function hydrate() {
    const saved = localStorage.getItem('shipFrom')
    if (saved) set(JSON.parse(saved))
  }

  return {
    name, addressLine1, addressLine2, city, state, postalCode, phone, email, set, hydrate
  }
})
