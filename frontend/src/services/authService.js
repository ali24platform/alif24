import apiService from './apiService';

/**
 * Auth Service
 * Handles authentication-related API calls
 */
class AuthService {
  /**
   * Login user
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise<Object>} User data and tokens
   */
  async login(email, password) {
    const response = await apiService.post('/auth/login', { email, password });
    return response.data;
  }

  /**
   * Register new user
   * @param {Object} userData - Registration data
   * @returns {Promise<Object>} User data and tokens
   */
  async register(userData) {
    const response = await apiService.post('/auth/register', userData);
    return response.data;
  }

  /**
   * Logout user
   * @returns {Promise<void>}
   */
  async logout() {
    await apiService.post('/auth/logout');
  }

  /**
   * Get current user profile
   * @returns {Promise<Object>} User profile
   */
  async getProfile() {
    const response = await apiService.get('/auth/me');
    return response.data;
  }

  /**
   * Update user profile
   * @param {Object} updates - Profile updates
   * @returns {Promise<Object>} Updated profile
   */
  async updateProfile(updates) {
    const response = await apiService.put('/auth/profile', updates);
    return response.data;
  }

  /**
   * Change password
   * @param {string} currentPassword - Current password
   * @param {string} newPassword - New password
   * @returns {Promise<void>}
   */
  async changePassword(currentPassword, newPassword) {
    await apiService.put('/auth/password', { currentPassword, newPassword });
  }

  /**
   * Send verification code to phone via Telegram
   * @param {string} phone - Phone number
   * @returns {Promise<Object>} Response
   */
  async sendVerificationCode(phone) {
    const response = await apiService.post('/verification/send-code', { phone });
    return response;
  }

  /**
   * Verify code sent to phone
   * @param {string} phone - Phone number
   * @param {string} code - Verification code
   * @returns {Promise<Object>} Response
   */
  async verifyCode(phone, code) {
    const response = await apiService.post('/verification/verify-code', { phone, code });
    return response;
  }
}

export const authService = new AuthService();
export default authService;
