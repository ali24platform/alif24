import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Get auth header
const getAuthHeader = () => {
    const user = JSON.parse(localStorage.getItem('user'));
    if (user && user.access_token) {
        return { Authorization: `Bearer ${user.access_token}` };
    }
    return {};
};

const crmService = {
    // Leads
    getLeads: async (params = {}) => {
        const response = await axios.get(`${API_URL}/crm/leads`, {
            headers: getAuthHeader(),
            params
        });
        return response.data;
    },

    getLead: async (id) => {
        const response = await axios.get(`${API_URL}/crm/leads/${id}`, {
            headers: getAuthHeader()
        });
        return response.data;
    },

    createLead: async (data) => {
        const response = await axios.post(`${API_URL}/crm/leads`, data, {
            headers: getAuthHeader()
        });
        return response.data;
    },

    updateLead: async (id, data) => {
        const response = await axios.put(`${API_URL}/crm/leads/${id}`, data, {
            headers: getAuthHeader()
        });
        return response.data;
    },

    deleteLead: async (id) => {
        const response = await axios.delete(`${API_URL}/crm/leads/${id}`, {
            headers: getAuthHeader()
        });
        return response.data;
    },

    // Activities
    createActivity: async (leadId, data) => {
        const response = await axios.post(`${API_URL}/crm/leads/${leadId}/activities`, data, {
            headers: getAuthHeader()
        });
        return response.data;
    },

    updateActivity: async (id, data) => {
        const response = await axios.put(`${API_URL}/crm/activities/${id}`, data, {
            headers: getAuthHeader()
        });
        return response.data;
    },

    deleteActivity: async (id) => {
        const response = await axios.delete(`${API_URL}/crm/activities/${id}`, {
            headers: getAuthHeader()
        });
        return response.data;
    }
};

export default crmService;
