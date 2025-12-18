'use client';

import { useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { authApi } from '@/lib/api';
import type { LoginCredentials, RegisterData } from '@/types';

export function useAuth() {
  const router = useRouter();
  const { token, user, isAuthenticated, isLoading, setToken, setUser, logout, setLoading } = useAuthStore();

  // Check auth status on mount
  useEffect(() => {
    const checkAuth = async () => {
      if (token && !user) {
        try {
          const response = await authApi.me();
          setUser(response.data);
        } catch {
          logout();
        }
      }
      setLoading(false);
    };
    
    checkAuth();
  }, [token, user, setUser, logout, setLoading]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    const response = await authApi.login(credentials);
    setToken(response.data.access_token);
    
    // Fetch user data
    const userResponse = await authApi.me();
    setUser(userResponse.data);
    
    router.push('/discover');
  }, [setToken, setUser, router]);

  const register = useCallback(async (data: RegisterData) => {
    const response = await authApi.register(data);
    setToken(response.data.access_token);
    
    // Fetch user data
    const userResponse = await authApi.me();
    setUser(userResponse.data);
    
    // Redirect to onboarding
    router.push('/onboarding');
  }, [setToken, setUser, router]);

  const signOut = useCallback(() => {
    logout();
    router.push('/login');
  }, [logout, router]);

  return {
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout: signOut,
  };
}
