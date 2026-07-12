import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../lib/api';

export interface UserProfile {
  id?: number;
  name: string;
  email: string;
  role: string;
  employee_id: string;
  photo_url: string;
}

interface UserContextType {
  profile: UserProfile | null;
  loading: boolean;
  updateProfile: (profile: UserProfile) => Promise<void>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const data = await apiClient.get('/users/profile');
      setProfile(data);
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async (newProfile: UserProfile) => {
    try {
      const data = await apiClient.put('/users/profile', newProfile);
      setProfile(data);
    } catch (error) {
      console.error('Failed to update user profile:', error);
      throw error;
    }
  };

  return (
    <UserContext.Provider value={{ profile, loading, updateProfile }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}
