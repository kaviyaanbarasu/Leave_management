import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(() => {
    const saved = localStorage.getItem('lms_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('lms_token') || '');
  const [personas, setPersonas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Load available personas
    api.getPersonas()
      .then((data) => {
        setPersonas(data);
      })
      .catch(console.error);
  }, []);

  const loginUser = async (username, password = 'password123') => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.login({ username, password });
      setCurrentUser(res.user);
      setToken(res.token);
      localStorage.setItem('lms_user', JSON.stringify(res.user));
      localStorage.setItem('lms_token', res.token);
      return res.user;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const switchPersona = async (employeeId) => {
    return loginUser(employeeId, employeeId.startsWith('ADMIN') ? 'admin123' : 'password123');
  };

  const logout = () => {
    setCurrentUser(null);
    setToken('');
    localStorage.removeItem('lms_user');
    localStorage.removeItem('lms_token');
  };

  const isAdmin = currentUser?.role === 'HR_ADMIN';

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        token,
        personas,
        isAdmin,
        loading,
        error,
        login: loginUser,
        switchPersona,
        logout,
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
