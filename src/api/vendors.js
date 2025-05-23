// src/api/vendors.js
import apiClient from '@/utils/axios';

export async function searchVendors(keyword, sessionToken) {
  try {
    const response = await apiClient.get('/Vendors', {
      headers: {
        Authorization: `SessionToken ${sessionToken}`
      },
      params: {
        keyword: keyword
      }
    });
    return response.data;
  } catch (error) {
    console.error('Vendor search failed:', error);
    throw error;
  }
}

