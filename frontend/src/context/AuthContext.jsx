import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

// Role Home Route Mapping
export const ROLE_HOME_ROUTES = {
  CITIZEN: '/citizen',
  URBAN_ANALYST: '/analyst',
  URBAN_AUTHORITY: '/authority',
  SYSTEM_ADMIN: '/admin',
};

// Available Demo Seed Users for Easy Development Testing
export const SEED_USERS = [
  {
    username: 'citizen',
    password: 'citizen123',
    role: 'CITIZEN',
    name: 'Aarav Sharma',
    email: 'citizen@urbansim.local',
    description: 'Public participation, local ward discovery & complaint filing',
    badgeColor: 'bg-emerald-950/80 text-emerald-400 border-emerald-500/30'
  },
  {
    username: 'analyst',
    password: 'analyst123',
    role: 'URBAN_ANALYST',
    name: 'Dr. Ananya Desai',
    email: 'analyst@urbansim.local',
    description: 'Full analytical GIS, deep learning diagnostics & scenarios',
    badgeColor: 'bg-cyan-950/80 text-cyan-400 border-cyan-500/30'
  },
  {
    username: 'authority',
    password: 'authority123',
    role: 'URBAN_AUTHORITY',
    name: 'Rajesh Kulkarni (Asst. Commissioner)',
    email: 'authority@urbansim.local',
    description: 'Operational municipal command, complaint queues & oversight',
    badgeColor: 'bg-amber-950/80 text-amber-400 border-amber-500/30'
  },
  {
    username: 'admin',
    password: 'admin123',
    role: 'SYSTEM_ADMIN',
    name: 'System Administrator',
    email: 'admin@urbansim.local',
    description: 'User management, RBAC matrix, system audit logs & AI pipelines',
    badgeColor: 'bg-purple-950/80 text-purple-400 border-purple-500/30'
  }
];

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load session from localStorage on initialization
  useEffect(() => {
    try {
      const storedToken = localStorage.getItem('urbansim_token');
      const storedUser = localStorage.getItem('urbansim_user');
      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      }
    } catch (e) {
      console.error('Failed to parse stored auth session:', e);
      localStorage.removeItem('urbansim_token');
      localStorage.removeItem('urbansim_user');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (usernameOrEmail, password) => {
    const cleanUsername = usernameOrEmail.trim().toLowerCase();
    const cleanPassword = password.trim();

    // 1. Try Backend API first
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: cleanUsername, password: cleanPassword }),
      });

      if (response.ok) {
        const data = await response.json();
        setToken(data.access_token);
        setUser(data.user);
        localStorage.setItem('urbansim_token', data.access_token);
        localStorage.setItem('urbansim_user', JSON.stringify(data.user));
        return { success: true, user: data.user, role: data.user.role };
      }

      if (response.status === 401 || response.status === 403) {
        const err = await response.json().catch(() => ({}));
        if (err.detail) throw new Error(err.detail);
      }
    } catch (apiErr) {
      if (apiErr.message && !apiErr.message.includes('fetch') && !apiErr.message.includes('504') && !apiErr.message.includes('500')) {
        throw apiErr;
      }
      console.warn('Backend login unavailable or timed out, trying local persistence:', apiErr);
    }

    // 2. Check locally registered citizens in database
    try {
      const localCitizens = JSON.parse(localStorage.getItem('urbansim_registered_citizens') || '[]');
      const matchedCitizen = localCitizens.find(
        u => (u.username.toLowerCase() === cleanUsername || u.email.toLowerCase() === cleanUsername) && u.password === cleanPassword
      );

      if (matchedCitizen) {
        const citizenUser = {
          username: matchedCitizen.username,
          email: matchedCitizen.email,
          name: matchedCitizen.name,
          role: 'CITIZEN',
          ward: matchedCitizen.ward || 'GS',
          phone: matchedCitizen.phone || '',
          permissions: ['public_gis:view', 'ward_info:view', 'facilities:view', 'complaints:submit', 'complaints:view_own']
        };
        const mockToken = `jwt_citizen_${matchedCitizen.username}_${Date.now()}`;
        setToken(mockToken);
        setUser(citizenUser);
        localStorage.setItem('urbansim_token', mockToken);
        localStorage.setItem('urbansim_user', JSON.stringify(citizenUser));
        return { success: true, user: citizenUser, role: 'CITIZEN' };
      }
    } catch (e) {
      console.error('Error checking local citizens database:', e);
    }

    // 3. Check Seed demo accounts
    const matchedSeed = SEED_USERS.find(
      u => (u.username.toLowerCase() === cleanUsername || u.email.toLowerCase() === cleanUsername) && u.password === cleanPassword
    );

    if (matchedSeed) {
      const mockUser = {
        username: matchedSeed.username,
        email: matchedSeed.email,
        name: matchedSeed.name,
        role: matchedSeed.role,
        ward: matchedSeed.role === 'CITIZEN' ? 'GS' : 'All',
        permissions: []
      };
      const mockToken = `mock_jwt_token_${matchedSeed.username}_${Date.now()}`;
      setToken(mockToken);
      setUser(mockUser);
      localStorage.setItem('urbansim_token', mockToken);
      localStorage.setItem('urbansim_user', JSON.stringify(mockUser));
      return { success: true, user: mockUser, role: mockUser.role };
    }

    throw new Error('Invalid username or password. Please verify credentials.');
  };

  const register = async (citizenData) => {
    const cleanUser = citizenData.username.trim().toLowerCase();
    const cleanEmail = citizenData.email.trim().toLowerCase();

    // 1. Try Backend API first
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: citizenData.name.trim(),
          email: cleanEmail,
          username: cleanUser,
          password: citizenData.password,
          ward: citizenData.ward || 'GS',
          phone: citizenData.phone || null,
          address: citizenData.address || null
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setToken(data.access_token);
        setUser(data.user);
        localStorage.setItem('urbansim_token', data.access_token);
        localStorage.setItem('urbansim_user', JSON.stringify(data.user));

        // Also sync to local storage cache
        try {
          const localCitizens = JSON.parse(localStorage.getItem('urbansim_registered_citizens') || '[]');
          if (!localCitizens.some(c => c.username === cleanUser)) {
            localCitizens.push({ ...data.user, password: citizenData.password });
            localStorage.setItem('urbansim_registered_citizens', JSON.stringify(localCitizens));
          }
        } catch (_) {}

        return { success: true, user: data.user, role: data.user.role };
      }

      // If backend returned a 400 validation error (e.g. duplicate username in SQLite)
      if (response.status >= 400 && response.status < 500) {
        const errorData = await response.json().catch(() => ({}));
        if (errorData.detail) {
          throw new Error(errorData.detail);
        }
      }
    } catch (err) {
      if (err.message && !err.message.includes('fetch') && !err.message.includes('504') && !err.message.includes('500') && !err.message.includes('NetworkError')) {
        throw err;
      }
      console.warn('Backend unavailable, saving citizen to browser database:', err);
    }

    // 2. Persistent Browser Database Storage
    try {
      const localCitizens = JSON.parse(localStorage.getItem('urbansim_registered_citizens') || '[]');

      // Check unique username
      if (localCitizens.some(u => u.username.toLowerCase() === cleanUser)) {
        throw new Error(`Username '${cleanUser}' is already registered. Please choose another.`);
      }

      // Check unique email
      if (localCitizens.some(u => u.email.toLowerCase() === cleanEmail)) {
        throw new Error(`Email '${cleanEmail}' is already registered with another account.`);
      }

      const newCitizenUser = {
        id: Date.now(),
        username: cleanUser,
        email: cleanEmail,
        name: citizenData.name.trim(),
        role: 'CITIZEN',
        ward: citizenData.ward || 'GS',
        phone: citizenData.phone || '',
        address: citizenData.address || '',
        password: citizenData.password,
        created_at: new Date().toISOString(),
        permissions: ['public_gis:view', 'ward_info:view', 'facilities:view', 'complaints:submit', 'complaints:view_own']
      };

      localCitizens.push(newCitizenUser);
      localStorage.setItem('urbansim_registered_citizens', JSON.stringify(localCitizens));

      const mockToken = `jwt_citizen_${newCitizenUser.username}_${Date.now()}`;
      setToken(mockToken);
      setUser(newCitizenUser);
      localStorage.setItem('urbansim_token', mockToken);
      localStorage.setItem('urbansim_user', JSON.stringify(newCitizenUser));

      return { success: true, user: newCitizenUser, role: 'CITIZEN' };
    } catch (storageErr) {
      throw storageErr;
    }
  };

  const logout = async () => {
    try {
      if (token && !token.startsWith('mock_') && !token.startsWith('jwt_citizen_')) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }).catch(() => {});
      }
    } catch (e) {
      // Ignore network errors on logout
    } finally {
      setUser(null);
      setToken(null);
      localStorage.removeItem('urbansim_token');
      localStorage.removeItem('urbansim_user');
    }
  };

  const hasRole = (allowedRoles) => {
    if (!user || !user.role) return false;
    if (user.role === 'SYSTEM_ADMIN') return true; // Admin has superuser access
    return Array.isArray(allowedRoles) ? allowedRoles.includes(user.role) : user.role === allowedRoles;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role: user?.role || null,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
