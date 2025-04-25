import axiosInstance from './axiosConfig';

interface LoginData {
  username: string;
  password: string;
}

interface RegisterData {
  username: string;
  email: string;
  password: string;
  fullName?: string;
}

export const authService = {
  login: async (data: LoginData) => {
    // Convert to URLSearchParams for OAuth2 compatibility
    const params = new URLSearchParams();
    params.append('username', data.username);
    params.append('password', data.password);
    
    // Use axios with special content-type for form submission
    const response = await axiosInstance.post('/auth/token', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }
    return response.data;
  },

  register: async (data: RegisterData) => {
    return await axiosInstance.post('/auth/register', data);
  },

  logout: () => {
    localStorage.removeItem('access_token');
  },

  getCurrentUser: async () => {
    return await axiosInstance.get('/auth/users/me');
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  }
};
