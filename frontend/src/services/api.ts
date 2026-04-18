import axios from 'axios';

export const API_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/login/refresh/`, {
            refresh: refreshToken,
          });
          localStorage.setItem('access_token', response.data.access);
          api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access}`;
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export const groupsApi = {
  list: () => api.get('/groups/'),
  getDetail: (groupId: number) => api.get(`/groups/${groupId}/`),
  toggleActive: (groupId: number) => api.post(`/groups/${groupId}/toggle_active/`),
};

export const questionnairesApi = {
  list: () => api.get('/questionnaires/'),
  getDetail: (id: string) => api.get(`/questionnaires/${id}/`),
  createResponseSet: (questionnaireId: string) => api.post('/questionnaires/response-sets/', { questionnaire: questionnaireId }),
  getResponseSet: (id: string) => api.get(`/questionnaires/response-sets/${id}/`),
  listResponseSets: () => api.get('/questionnaires/response-sets/'),
  submitResponseSet: (responseSetId: string, responsesData: any[]) =>
    api.post(`/questionnaires/response-sets/${responseSetId}/submit/`, { responses_data: responsesData }),

  // Administrative Operations
  getAnalyticsSummary: () => api.get('/questionnaires/analytics/all/'),
  getAdminBaselineResponses: (page: number = 1) => api.get(`/questionnaires/baselines/?page=${page}`),
  getAdminBaselineDetail: (id: string) => api.get(`/questionnaires/baselines/${id}/`),
  getDashboardAnalytics: () => api.get('/admin/tools/dashboard-analytics/'),
  exportAdminBaselinesCSV: (groupName?: string) => api.get('/admin/tools/export/baselines/csv/', { 
    params: groupName && groupName !== 'All' ? { group: groupName } : {},
    responseType: 'blob' 
  }),
};

// Aliases for compatibility with upstream UI components
export const getGroups = groupsApi.list;
export const getGroupDetail = groupsApi.getDetail;

export default api;
