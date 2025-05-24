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

// Get one venbdor by ID
// This function retrieves a vendor's details by its ID

export async function getVendorById(id, sessionToken) {
  try {
    const response = await apiClient.get(`/Vendors/${id}`, {
      headers: {
        Authorization: `SessionToken ${sessionToken}`
      }
    });
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch vendor with ID ${id}:`, error);
    throw error;
  }
}

