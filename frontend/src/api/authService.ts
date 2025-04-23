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
    const response = await axiosInstance.post('/auth/login', data);
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
    return await axiosInstance.get('/auth/me');
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  }
};
