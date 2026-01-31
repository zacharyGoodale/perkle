import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { auth } from '../lib/api';

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

const TOKEN_KEY = 'perkle_token';
const REFRESH_KEY = 'perkle_refresh';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    token: null,
    isAuthenticated: false,
    isLoading: true,
  });

  useEffect(() => {
    // Check for stored token on mount
    const storedToken = localStorage.getItem(TOKEN_KEY);
    if (storedToken) {
      setState({
        token: storedToken,
        isAuthenticated: true,
        isLoading: false,
      });
    } else {
      setState(s => ({ ...s, isLoading: false }));
    }
  }, []);

  const login = async (username: string, password: string) => {
    const response = await auth.login({ username, password });
    localStorage.setItem(TOKEN_KEY, response.access_token);
    localStorage.setItem(REFRESH_KEY, response.refresh_token);
    setState({
      token: response.access_token,
      isAuthenticated: true,
      isLoading: false,
    });
  };

  const register = async (username: string, email: string, password: string) => {
    await auth.register({ username, email, password });
    // Auto-login after register
    await login(username, password);
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    setState({
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
  };

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
