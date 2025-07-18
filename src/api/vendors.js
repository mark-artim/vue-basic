// src/api/vendors.js
import apiClient from '@/utils/axios';

export const searchVendors = async (keyword) => {
  const res = await apiClient.post('/api/erp-proxy', {
    method: 'GET',
    url: '/Vendors',
    params: {
      keyword,
      includeTotalItems: true,
    },
  });
  return res.data;
};

// Get one venbdor by ID
export const getVendor = async (vendorId) => {
  const res = await apiClient.post('/api/erp-proxy', {
    method: 'GET',
    url: `/Vendors/${vendorId}`,
  });
  return res.data;
};

// Create a new vendor
export const createVendorOLD = async (vendorData, sessionToken) => {
  return await apiClient.post('/Vendors', vendorData, {
    headers: {
      Authorization: `SessionToken ${sessionToken}`
    }
  });
};

export const createVendor = async (vendorData) => {
  return await apiClient.post('/api/erp-proxy', {
    method: 'POST',
    url: '/Vendors',
    data: vendorData,
  });
};

