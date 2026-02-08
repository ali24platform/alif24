import api from './apiService';

const organizationService = {
    /**
     * Get platform statistics (users, classrooms, pending teachers)
     */
    getStats: async () => {
        try {
            const response = await api.get('/organization/stats');
            return response.data;
        } catch (error) {
            throw error;
        }
    },

    /**
     * Get all users with filters
     * @param {Object} params - { role, user_status, skip, limit }
     */
    getUsers: async (params = {}) => {
        try {
            const response = await api.get('/organization/users', { params });
            return response.data;
        } catch (error) {
            throw error;
        }
    },

    /**
     * Get pending teacher applications
     */
    getPendingTeachers: async () => {
        try {
            const response = await api.get('/organization/pending-teachers');
            return response.data;
        } catch (error) {
            throw error;
        }
    },

    /**
     * Approve a teacher
     * @param {string} teacherId
     */
    approveTeacher: async (teacherId) => {
        try {
            const response = await api.post(`/organization/approve-teacher/${teacherId}`);
            return response.data;
        } catch (error) {
            throw error;
        }
    },

    /**
     * Reject a teacher
     * @param {string} teacherId
     * @param {string} reason
     */
    rejectTeacher: async (teacherId, reason) => {
        try {
            const response = await api.post(`/organization/reject-teacher/${teacherId}`, { reason });
            return response.data;
        } catch (error) {
            throw error;
        }
    },

    /**
     * Update user status (block/unblock)
     * @param {string} userId
     * @param {string} status - 'active', 'suspended', 'deleted'
     */
    updateUserStatus: async (userId, status) => {
        try {
            const response = await api.patch(`/organization/users/${userId}/status`, { status });
            return response.data;
        } catch (error) {
            throw error;
        }
    }
};

export default organizationService;
