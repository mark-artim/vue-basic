import apiClient from '@/utils/axios';


export const searchContacts = async (keyword, sessionToken) => {
  try {
    const response = await apiClient.get('Contacts', {
      params: {
        keyword,
        includeTotalItems: true,
      },
      headers: {
        Authorization: `SessionToken ${sessionToken}`,
      },
    });
    return response.data;
  } catch (error) {
    throw new Error('Error fetching contacts. Please try again.');
  }
};

export const updateContact = async (contactId, contactData, sessionToken) => {
    try {
      const response = await apiClient.put(
        `/Contacts/${contactId}`,
        contactData,
      );
      return response.data;
    } catch (error) {
      throw new Error('Failed to update the contact. ' + error.response?.data?.message || '');
    }
  };
  
  export const getContact = async (contactId, sessionToken) => {
    try {
      const response = await apiClient.get(
        `/Contacts/${contactId}`,
      );
      return response.data;
    } catch (error) {
      throw new Error('Failed to get the contact. ' + error.response?.data?.message || '');
    }
  };  


