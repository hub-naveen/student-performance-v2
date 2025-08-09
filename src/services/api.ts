import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login/', { email, password });
    return response.data;
  },

  register: async (userData: any) => {
    const response = await api.post('/auth/register/', userData);
    return response.data;
  },

  logout: async () => {
    const response = await api.post('/auth/logout/');
    return response.data;
  },

  getProfile: async () => {
    const response = await api.get('/auth/profile/');
    return response.data;
  },

  updateProfile: async (userData: any) => {
    const response = await api.patch('/auth/profile/', userData);
    return response.data;
  },

  changePassword: async (passwordData: any) => {
    const response = await api.post('/auth/change-password/', passwordData);
    return response.data;
  },
};

// Students API
export const studentsAPI = {
  getDashboard: async () => {
    const response = await api.get('/students/dashboard/student/');
    return response.data;
  },

  getTeacherDashboard: async () => {
    const response = await api.get('/students/dashboard/teacher/');
    return response.data;
  },

  getProfiles: async (params?: any) => {
    const response = await api.get('/students/profiles/', { params });
    return response.data;
  },

  getClasses: async (params?: any) => {
    const response = await api.get('/students/classes/', { params });
    return response.data;
  },

  getGrades: async (params?: any) => {
    const response = await api.get('/students/grades/', { params });
    return response.data;
  },

  getAssignments: async (params?: any) => {
    const response = await api.get('/students/assignments/', { params });
    return response.data;
  },

  getAttendance: async (params?: any) => {
    const response = await api.get('/students/attendance/', { params });
    return response.data;
  },
};

// Predictions API
export const predictionsAPI = {
  getPredictions: async (params?: any) => {
    const response = await api.get('/predictions/predictions/', { params });
    return response.data;
  },

  createBatchPredictions: async (data: any) => {
    const response = await api.post('/predictions/predictions/batch_predict/', data);
    return response.data;
  },

  getRecommendations: async (params?: any) => {
    const response = await api.get('/predictions/recommendations/', { params });
    return response.data;
  },

  generateRecommendations: async (data: any) => {
    const response = await api.post('/predictions/recommendations/generate_from_prediction/', data);
    return response.data;
  },

  getAnalytics: async (params?: any) => {
    const response = await api.get('/predictions/analytics/', { params });
    return response.data;
  },

  getModels: async () => {
    const response = await api.get('/predictions/models/');
    return response.data;
  },

  trainModel: async (data: FormData) => {
    const response = await api.post('/predictions/train-model/', data, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// Notifications API
export const notificationsAPI = {
  getNotifications: async (params?: any) => {
    const response = await api.get('/notifications/notifications/', { params });
    return response.data;
  },

  markAsRead: async (notificationIds: string[]) => {
    const response = await api.post('/notifications/notifications/mark_as_read/', {
      notification_ids: notificationIds,
    });
    return response.data;
  },

  getSummary: async () => {
    const response = await api.get('/notifications/notifications/summary/');
    return response.data;
  },

  getPreferences: async () => {
    const response = await api.get('/notifications/preferences/');
    return response.data;
  },

  updatePreferences: async (data: any) => {
    const response = await api.patch('/notifications/preferences/', data);
    return response.data;
  },

  getAnalytics: async (params?: any) => {
    const response = await api.get('/notifications/analytics/', { params });
    return response.data;
  },
};

export default api;