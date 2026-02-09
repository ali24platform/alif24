/**
 * CRM Service
 * Handles CRM-related API calls (leads, activities)
 * 
 * FIXED: Was using raw axios with wrong auth token key.
 * Now uses unified apiService with correct token handling.
 */
import apiService from './apiService';

const crmService = {
    // Leads
    getLeads: async (params = {}) => {
        const response = await apiService.get('/crm/leads', params);
        return response;
    },

    getLead: async (id) => {
        const response = await apiService.get(`/crm/leads/${id}`);
        return response;
    },

    createLead: async (data) => {
        const response = await apiService.post('/crm/leads', data);
        return response;
    },

    updateLead: async (id, data) => {
        const response = await apiService.put(`/crm/leads/${id}`, data);
        return response;
    },

    deleteLead: async (id) => {
        const response = await apiService.delete(`/crm/leads/${id}`);
        return response;
    },

    // Activities
    createActivity: async (leadId, data) => {
        const response = await apiService.post(`/crm/leads/${leadId}/activities`, data);
        return response;
    },

    updateActivity: async (id, data) => {
        const response = await apiService.put(`/crm/activities/${id}`, data);
        return response;
    },

    deleteActivity: async (id) => {
        const response = await apiService.delete(`/crm/activities/${id}`);
        return response;
    }
};

export default crmService;
