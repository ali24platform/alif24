import axios from 'axios';

const API_Base = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL: API_Base,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor to add token to requests
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('accessToken');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Interceptor to handle errors (e.g., 401 redirect)
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response && error.response.status === 401) {
            // Token expired or invalid
            // Optionally try refresh token here or just logout
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            // window.location.href = '/details/login'; // Redirect if needed
        }
        return Promise.reject(error);
    }
);

export default api;
