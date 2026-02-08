import api from './api';

const organizationService = {
    // --- Stats ---
    getStats: async () => {
        const response = await api.get('/organization/stats');
        return response.data;
    },

    // --- Users ---
    getUsers: async (role) => {
        const params = {};
        if (role) params.role = role;
        // Using generic admin users endpoint for now, assuming organization has access
        const response = await api.get('/organization/users', { params });
        return response.data;
    },

    inviteStudent: async (data) => {
        const response = await api.post('/organization-structure/students/invite', data);
        return response.data;
    },

    // --- Teachers ---
    getTeachers: async () => {
        const response = await api.get('/organization-structure/teachers');
        return response.data;
    },

    addTeacher: async (teacherId) => {
        const response = await api.post('/organization-structure/teachers', { teacher_id: teacherId });
        return response.data;
    },

    removeTeacher: async (teacherId) => {
        const response = await api.delete(`/organization-structure/teachers/${teacherId}`);
        return response.data;
    },

    // --- Materials (Content Box) ---
    getMaterials: async () => {
        const response = await api.get('/organization-structure/materials');
        return response.data;
    },

    uploadMaterial: async (formData) => {
        const response = await api.post('/organization-structure/materials', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    // --- Schedule ---
    getSchedule: async (classroomId) => {
        const response = await api.get(`/schedule/classroom/${classroomId}`);
        return response.data;
    },

    createSchedule: async (scheduleData) => {
        const response = await api.post('/schedule/', scheduleData);
        return response.data;
    },

    // --- Reading Analysis ---
    getReadingAnalyses: async (limit = 20) => {
        // Assuming a reading analysis endpoint exists for orgs
        // If not, we might need to mock or use a teacher/admin one
        try {
            const response = await api.get(`/organization/reading-analyses?limit=${limit}`);
            return response.data;
        } catch (e) {
            console.warn("Reading analysis endpoint not found, returning empty", e);
            return { analyses: [] };
        }
    }
};

export default organizationService;
