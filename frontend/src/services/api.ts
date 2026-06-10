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
  (response) => {
    // Global Normalization: If the response is a DRF paginated object, unwrap the results array
    // so that collection-based components (using .map, .filter) do not crash.
    if (
      response.data &&
      typeof response.data === 'object' &&
      'results' in response.data &&
      Array.isArray(response.data.results)
    ) {
      const results = response.data.results;
      // Attach pagination metadata to the array as hidden properties for advanced use
      Object.defineProperty(results, '_pagination', {
        value: {
          count: response.data.count,
          next: response.data.next,
          previous: response.data.previous,
        },
        enumerable: false,
      });
      response.data = results;
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
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
  update: (groupId: number, data: { name: string; description: string }) => api.patch(`/groups/${groupId}/`, data),
};

export const questionnairesApi = {
  list: () => api.get('/questionnaires/'),
  getDetail: (id: string) => api.get(`/questionnaires/${id}/`),
  createResponseSet: (questionnaireId: string, milestone?: string) => api.post('/questionnaires/response-sets/', { questionnaire: questionnaireId, milestone }),
  getResponseSet: (id: string) => api.get(`/questionnaires/response-sets/${id}/`),
  listResponseSets: () => api.get('/questionnaires/response-sets/'),
  submitResponseSet: (responseSetId: string, responsesData: any[]) =>
    api.post(`/questionnaires/response-sets/${responseSetId}/submit/`, { responses_data: responsesData }),
  saveDraftResponseSet: (responseSetId: string, responsesData: any[]) =>
    api.post(`/questionnaires/response-sets/${responseSetId}/save-draft/`, { responses_data: responsesData }),
  submitOptIn: (responseSetId: string, optIn: boolean) =>
    api.post(`/questionnaires/response-sets/${responseSetId}/opt-in/`, { opt_in: optIn }),

  // Administrative Operations
  getAnalyticsSummary: () => api.get('/questionnaires/analytics/all/'),

  getAdminT0Responses: (page: number = 1) => api.get(`/questionnaires/t0-results/?page=${page}`),
  getAdminT0Detail: (id: string) => api.get(`/questionnaires/t0-results/${id}/`),
  getAdminT1Responses: (page: number = 1) => api.get(`/questionnaires/t1-results/?page=${page}`),
  getAdminT1Detail: (id: string) => api.get(`/questionnaires/t1-results/${id}/`),
  getAdminTFirstMonthResponses: (page: number = 1) => api.get(`/questionnaires/t-first-month-results/?page=${page}`),
  getAdminTFirstMonthDetail: (id: string) => api.get(`/questionnaires/t-first-month-results/${id}/`),
  getAdminT2Responses: (page: number = 1) => api.get(`/questionnaires/t2-results/?page=${page}`),
  getAdminT2Detail: (id: string) => api.get(`/questionnaires/t2-results/${id}/`),
  getAdminT3Responses: (page: number = 1) => api.get(`/questionnaires/t3-results/?page=${page}`),
  getAdminT3Detail: (id: string) => api.get(`/questionnaires/t3-results/${id}/`),
  getAdminT4Responses: (page: number = 1) => api.get(`/questionnaires/t4-results/?page=${page}`),
  getAdminT4Detail: (id: string) => api.get(`/questionnaires/t4-results/${id}/`),
  getDashboardAnalytics: () => api.get('/admin/tools/dashboard-analytics/'),

  triggerAdminT0Export: (groupName?: string) => api.post('/admin/tools/export/t0/csv/', {
    group: groupName || 'All'
  }),
  triggerAdminT1Export: (groupName?: string) => api.post('/admin/tools/export/t1/csv/', {
    group: groupName || 'All'
  }),
  triggerAdminTFirstMonthExport: (groupName?: string) => api.post('/admin/tools/export/t-first-month/csv/', {
    group: groupName || 'All'
  }),
  triggerAdminT2Export: (groupName?: string) => api.post('/admin/tools/export/t2/csv/', {
    group: groupName || 'All'
  }),
  triggerAdminT3Export: (groupName?: string) => api.post('/admin/tools/export/t3/csv/', {
    group: groupName || 'All'
  }),
  triggerAdminT4Export: (groupName?: string) => api.post('/admin/tools/export/t4/csv/', {
    group: groupName || 'All'
  }),
  triggerAdminLongitudinalExport: (groupName?: string) => api.post('/admin/tools/export/longitudinal/csv/', {
    group: groupName || 'All'
  }),
  getAdminExportStatus: (taskId: string) => api.get(`/admin/tools/export/status/${taskId}/`),

  exportQuestionnaireData: (id: string) => api.get(`/questionnaires/${id}/export/`, { responseType: 'blob' }),
};

export const activitiesApi = {
  getCurrentActivity: () => api.get('/activities/daily/current/'),
  submitActivity: (data: { content: string }) => api.post('/activities/daily/submit/', data),
};

// Aliases for compatibility with upstream UI components
export const getGroups = groupsApi.list;
export const getGroupDetail = groupsApi.getDetail;
export const updateGroup = groupsApi.update;

export const usersApi = {
  deleteUser: (userId: number, confirmation: string) =>
    api.post(`/users/admin/users/${userId}/delete/`, { confirmation }),
};

export default api;
