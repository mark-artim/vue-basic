// src/api/customers.js
import apiClient from '@/utils/axios';

export async function searchCustomers(keyword, sessionToken) {
  try {
    const response = await apiClient.get('/Customers', {
      headers: {
        Authorization: `SessionToken ${sessionToken}`
      },
      params: {
        keyword: keyword
      }
    });
    return response.data;
  } catch (error) {
    console.error('Customer search failed:', error);
    throw error;
  }
}

// Get one customer by ID

export async function getCustomerById(id, sessionToken) {
  try {
    const response = await apiClient.get(`/Customers/${id}`, {
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

// Create a new customer

export const createCustomer = async (vendorData, sessionToken) => {
  return await apiClient.post('/Customers', vendorData, {
    headers: {
      Authorization: `SessionToken ${sessionToken}`
    }
  });
};