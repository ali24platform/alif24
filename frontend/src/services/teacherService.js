import apiService from './apiService';

class TeacherService {
    /**
     * Search for students by email or username
     * @param {string} query - Search query
     * @returns {Promise<Array>} List of students
     */
    async searchStudents(query) {
        return apiService.get('/teachers/students/search', { query });
    }

    /**
     * Add student to a classroom
     * @param {string} classroomId - Classroom ID
     * @param {string} studentId - Student User ID
     * @returns {Promise<Object>} Response
     */
    async addStudentToClass(classroomId, studentId) {
        return apiService.post(`/teachers/classrooms/${classroomId}/students`, { student_user_id: studentId });
    }

    /**
     * Get teacher's classrooms
     * @returns {Promise<Array>} List of classrooms
     */
    async getMyClassrooms() {
        return apiService.get('/teachers/my-classes');
    }

    /**
     * Create a new classroom
     * @param {Object} data - { name, subject, grade_level, description }
     * @returns {Promise<Object>} Created classroom
     */
    async createClassroom(data) {
        return apiService.post('/teachers/classrooms', data);
    }

    /**
     * Get dashboard statistics
     * @returns {Promise<Object>} Stats data
     */
    async getDashboardStats() {
        return apiService.get('/teachers/dashboard/stats');
    }

    /**
     * Get upcoming events (lessons/meetings)
     * @returns {Promise<Array>} List of events
     */
    async getUpcomingEvents() {
        return apiService.get('/teachers/dashboard/events');
    }

    /**
     * Get assignments
     * @returns {Promise<Array>} List of assignments
     */
    async getAssignments() {
        // Placeholder until backend endpoint is ready, returning empty array to prevent crash
        // return apiService.get('/teachers/assignments'); 
        return [];
    }

    /**
     * Get messages
     * @returns {Promise<Array>} List of messages
     */
    async getMessages() {
        // Placeholder until backend endpoint is ready
        // return apiService.get('/messages');
        return [];
    }

    /**
     * Create a new lesson
     * @param {Object} lessonData - Lesson data
     * @returns {Promise<Object>} Created lesson
     */
    async createLesson(lessonData) {
        // Prepare FormData for file upload if needed, or JSON
        // The backend expects Form data but apiService might handle it if we pass FormData
        // However, looking at backend implementation, it expects Form fields.
        // Let's us assume apiService handles JSON -> Form or we construct FormData

        const formData = new FormData();
        Object.keys(lessonData).forEach(key => {
            if (lessonData[key] !== null && lessonData[key] !== undefined) {
                formData.append(key, lessonData[key]);
            }
        });

        return apiService.post('/lessons', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    }

    /**
     * Create a new quiz (TeacherTest)
     * @param {Object} quizData - Quiz data
     * @returns {Promise<Object>} Created quiz
     */
    async createQuiz(quizData) {
        const formData = new FormData();
        Object.keys(quizData).forEach(key => {
            if (quizData[key] !== null && quizData[key] !== undefined) {
                if (typeof quizData[key] === 'object' && key === 'questions') {
                    formData.append(key, JSON.stringify(quizData[key]));
                } else {
                    formData.append(key, quizData[key]);
                }
            }
        });

        return apiService.post('/teacher-tests', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
    }
}

export const teacherService = new TeacherService();
