/**
 * Guest Session Service - Frontend API for guest tracking
 * 
 * FIXED: Was using raw axios with hardcoded localhost URL and had
 * an infinite retry loop on 404. Now uses correct base URL and
 * limits retries to prevent browser freeze.
 */

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

class GuestSessionService {
  constructor() {
    this.SESSION_KEY = 'guest_session_token';
    this.FINGERPRINT_KEY = 'browser_fingerprint';
  }

  /**
   * Get auth headers (guest sessions don't need auth, but include if available)
   */
  getHeaders() {
    return { 'Content-Type': 'application/json' };
  }

  /**
   * Make a fetch request with proper error handling
   */
  async request(method, endpoint, body = null) {
    const baseUrl = API_URL.startsWith('http')
      ? API_URL
      : `${window.location.origin}${API_URL}`;

    const options = {
      method,
      headers: this.getHeaders(),
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${baseUrl}${endpoint}`, options);
    const data = await response.json();

    if (!response.ok) {
      const error = new Error(data.detail || data.message || 'Request failed');
      error.status = response.status;
      throw error;
    }

    return data;
  }

  /**
   * Generate browser fingerprint (simple version)
   */
  generateFingerprint() {
    const nav = window.navigator;
    const screen = window.screen;

    const data = [
      nav.userAgent,
      nav.language,
      screen.colorDepth,
      screen.width + 'x' + screen.height,
      new Date().getTimezoneOffset(),
      !!window.sessionStorage,
      !!window.localStorage,
    ].join('|');

    let hash = 0;
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return hash.toString(36);
  }

  getSessionToken() {
    return localStorage.getItem(this.SESSION_KEY);
  }

  setSessionToken(token) {
    localStorage.setItem(this.SESSION_KEY, token);
  }

  getFingerprint() {
    let fingerprint = localStorage.getItem(this.FINGERPRINT_KEY);
    if (!fingerprint) {
      fingerprint = this.generateFingerprint();
      localStorage.setItem(this.FINGERPRINT_KEY, fingerprint);
    }
    return fingerprint;
  }

  /**
   * Create or get guest session
   */
  async createSession() {
    try {
      const fingerprint = this.getFingerprint();
      const data = await this.request('POST', '/guest/session', { fingerprint });
      this.setSessionToken(data.session_token);
      return data;
    } catch (error) {
      console.error('Error creating guest session:', error);
      throw error;
    }
  }

  /**
   * Track content access
   * FIXED: Added retry limit to prevent infinite recursion
   */
  async trackContentAccess(contentType, contentId, _retried = false) {
    try {
      let sessionToken = this.getSessionToken();

      if (!sessionToken) {
        const sessionData = await this.createSession();
        sessionToken = sessionData.session_token;
      }

      const data = await this.request('POST', '/guest/track', {
        session_token: sessionToken,
        content_type: contentType,
        content_id: contentId
      });

      return data;
    } catch (error) {
      console.error('Error tracking content access:', error);

      // If session not found, create new one and retry ONCE (not infinitely)
      if (error.status === 404 && !_retried) {
        localStorage.removeItem(this.SESSION_KEY);
        return this.trackContentAccess(contentType, contentId, true);
      }

      throw error;
    }
  }

  /**
   * Check session status
   */
  async checkSessionStatus() {
    try {
      const sessionToken = this.getSessionToken();
      if (!sessionToken) {
        return {
          exists: false,
          requires_login: true,
          message: 'No session found'
        };
      }

      const data = await this.request('GET', `/guest/status/${sessionToken}`);
      return data;
    } catch (error) {
      console.error('Error checking session status:', error);
      return {
        exists: false,
        requires_login: true,
        message: 'Session check failed'
      };
    }
  }

  /**
   * Convert guest session to user account after registration/login
   */
  async convertToUser(userId) {
    try {
      const sessionToken = this.getSessionToken();
      if (!sessionToken) return false;

      await this.request('POST', `/guest/convert/${sessionToken}?user_id=${userId}`);

      localStorage.removeItem(this.SESSION_KEY);
      return true;
    } catch (error) {
      console.error('Error converting session to user:', error);
      return false;
    }
  }

  clearSession() {
    localStorage.removeItem(this.SESSION_KEY);
  }
}

export default new GuestSessionService();
