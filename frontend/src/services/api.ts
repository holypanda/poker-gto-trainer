import axios from 'axios';

// API 地址配置
const API_BASE_URL = 'http://172.236.229.37:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 获取 token 的安全方法
const getToken = () => {
  try {
    const authStorage = localStorage.getItem('poker-auth-storage');
    if (authStorage) {
      const parsed = JSON.parse(authStorage);
      return parsed?.state?.token || null;
    }
  } catch (e) {
    console.error('Error reading token:', e);
  }
  return null;
};

// 请求拦截器 - 添加 token
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token 过期，清除认证状态
      try {
        localStorage.removeItem('poker-auth-storage');
        window.location.href = '/login';
      } catch (e) {
        console.error('Error clearing auth:', e);
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authApi = {
  login: (email: string, password: string) => {
    // 使用 form-data 格式
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);
    return api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  },
  
  register: (data: { email: string; username: string; password: string }) =>
    api.post('/auth/register', data),
  
  getMe: () => api.get('/auth/me'),
  
  getStats: () => api.get('/auth/stats'),
};

// Training API
export const trainingApi = {
  createSession: (data: {
    stack_size: number;
    position: string;
    action_to_you: string;
    scenario_count?: number;
  }) => api.post('/training/sessions', data),
  
  getSession: (sessionId: number) => api.get(`/training/sessions/${sessionId}`),
  
  submitAnswer: (sessionId: number, data: {
    scenario_id: number;
    action: string;
    response_time_ms?: number;
  }) => api.post(`/training/sessions/${sessionId}/answer`, data),
  
  completeSession: (sessionId: number) => api.post(`/training/sessions/${sessionId}/complete`),
  
  getHistory: (params?: { limit?: number; offset?: number }) =>
    api.get('/training/history', { params }),
  
  getStats: () => api.get('/training/stats'),
  
  getAdvice: (params: {
    hand: string;
    position: string;
    action_to_you: string;
    stack_size?: number;
  }) => api.get('/training/advice', { params }),
};

// Payment API
export const paymentApi = {
  createSubscription: (data: { return_url?: string; notify_url?: string }) =>
    api.post('/payment/subscribe', data),
  
  verifyPayment: (orderId: string) => api.get(`/payment/verify/${orderId}`),
  
  getStatus: () => api.get('/payment/status'),
  
  cancelSubscription: () => api.post('/payment/cancel'),
};
