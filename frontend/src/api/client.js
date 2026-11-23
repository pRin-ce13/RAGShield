/**
 * RAGShield REST API Client
 * Lightweight JavaScript wrapper consuming FastAPI endpoints with JWT auth and auto-headers.
 */

const API_BASE = '/api/v1';

class ApiClient {
  constructor() {
    this.tokenKey = 'ragshield_access_token';
  }

  getToken() {
    return localStorage.getItem(this.tokenKey);
  }

  setToken(token) {
    if (token) {
      localStorage.setItem(this.tokenKey, token);
    } else {
      localStorage.removeItem(this.tokenKey);
    }
  }

  getHeaders(isFormData = false) {
    const headers = {};
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  async request(endpoint, options = {}) {
    const isFormData = options.body instanceof FormData;
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
    
    const config = {
      ...options,
      headers: {
        ...this.getHeaders(isFormData),
        ...(options.headers || {}),
      },
    };

    const response = await fetch(url, config);
    
    if (response.status === 204) {
      return null;
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const errorMsg = data.detail || data.message || `Request failed with status ${response.status}`;
      throw new Error(errorMsg);
    }

    return data;
  }

  // --- Authentication ---
  async login(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const data = await this.request('/auth/login', {
      method: 'POST',
      body: formData,
    });
    
    if (data.access_token) {
      this.setToken(data.access_token);
    }
    return data;
  }

  async register(userData) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  logout() {
    this.setToken(null);
  }

  // --- Health ---
  async checkBackendHealth() {
    const res = await fetch('/health');
    return res.json();
  }

  // --- Targets ---
  async getTargets(skip = 0, limit = 50) {
    return this.request(`/targets/?skip=${skip}&limit=${limit}`);
  }

  async createTarget(targetData) {
    return this.request('/targets/', {
      method: 'POST',
      body: JSON.stringify(targetData),
    });
  }

  async checkTargetHealth(targetId) {
    return this.request(`/targets/${targetId}/check`, {
      method: 'POST',
    });
  }

  async deleteTarget(targetId) {
    return this.request(`/targets/${targetId}`, {
      method: 'DELETE',
    });
  }

  // --- Scans ---
  async launchScan(scanConfig) {
    return this.request('/scans/launch', {
      method: 'POST',
      body: JSON.stringify(scanConfig),
    });
  }

  async getScans(targetId = null, limit = 20) {
    const query = targetId ? `?target_id=${targetId}&limit=${limit}` : `?limit=${limit}`;
    return this.request(`/scans/${query}`);
  }

  async getScan(scanId) {
    return this.request(`/scans/${scanId}`);
  }

  async getScanResults(scanId) {
    return this.request(`/scans/${scanId}/results`);
  }

  // --- Findings & Posture ---
  async getScanFindings(scanId) {
    return this.request(`/findings/${scanId}`);
  }

  async getScanPosture(scanId) {
    return this.request(`/findings/${scanId}/posture`);
  }
}

export const api = new ApiClient();
