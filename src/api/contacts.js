import axios from '@/utils/axios';


export const searchContacts = async (keyword, sessionToken) => {
  try {
    const response = await axios.get('Contacts', {
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
      const response = await axios.put(
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
      const response = await axios.get(
        `/Contacts/${contactId}`,
      );
      return response.data;
    } catch (error) {
      throw new Error('Failed to get the contact. ' + error.response?.data?.message || '');
    }
  };  


