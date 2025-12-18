import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/store/auth';
import type { ApiError } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      useAuthStore.getState().logout();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authApi = {
  register: (data: { email: string; password: string; display_name?: string }) =>
    api.post('/auth/register', data),
  
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),
  
  me: () => api.get('/auth/me'),
};

// Users API
export const usersApi = {
  getProfile: () => api.get('/users/me'),
  
  updateProfile: (data: { display_name?: string; bio?: string; avatar_url?: string }) =>
    api.put('/users/me', data),
  
  getInteractions: (params?: { media_type?: string; interaction_type?: string }) =>
    api.get('/users/me/interactions', { params }),
  
  submitVibeCheck: (answers: { question_id: string; answer: string }[]) =>
    api.post('/users/me/vibe-check', { answers }),
  
  getUserProfile: (userId: string) => api.get(`/users/${userId}`),
};

// Media API
export const mediaApi = {
  searchMovies: (query: string) =>
    api.get('/media/search/movies', { params: { q: query } }),
  
  searchArtists: (query: string) =>
    api.get('/media/search/artists', { params: { q: query } }),
  
  searchTracks: (query: string) =>
    api.get('/media/search/tracks', { params: { q: query } }),
  
  getTrendingMovies: () => api.get('/media/movies/trending'),
  
  logInteraction: (data: {
    media: {
      external_id: string;
      media_type: string;
      title: string;
      image_url?: string;
      extra_data?: Record<string, unknown>;
    };
    interaction_type: string;
    rating?: number;
    review_text?: string;
  }) => {
    // Filter out undefined values
    const payload = {
      media: {
        external_id: data.media.external_id,
        media_type: data.media.media_type,
        title: data.media.title,
        ...(data.media.image_url && { image_url: data.media.image_url }),
        ...(data.media.extra_data && { extra_data: data.media.extra_data }),
      },
      interaction_type: data.interaction_type,
      ...(data.rating !== undefined && { rating: data.rating }),
      ...(data.review_text !== undefined && { review_text: data.review_text }),
    };
    return api.post('/media/interactions', payload);
  },
  
  removeInteraction: (interactionId: string) =>
    api.delete(`/media/interactions/${interactionId}`),
};

// Matches API
export const matchesApi = {
  discover: (limit?: number) =>
    api.post('/matches/discover', null, { params: { limit } }),
  
  getMatches: (status?: string) =>
    api.get('/matches', { params: { status } }),
  
  respondToMatch: (matchId: string, action: 'accept' | 'reject') =>
    api.post(`/matches/${matchId}/action`, { action }),
  
  getMessages: (matchId: string, limit?: number, before?: string) =>
    api.get(`/matches/${matchId}/messages`, { params: { limit, before } }),
  
  sendMessage: (matchId: string, content: string) =>
    api.post(`/matches/${matchId}/messages`, { content }),
};

// Spotify API
export const spotifyApi = {
  getAuthUrl: () => api.get('/spotify/auth-url'),
  
  importTopItems: () => api.post('/spotify/import'),
  
  getProfile: () => api.get('/spotify/profile'),
  
  disconnect: () => api.delete('/spotify/disconnect'),
};
