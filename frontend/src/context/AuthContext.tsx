import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { auth, setAccessToken } from '../lib/api';

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    token: null,
    isAuthenticated: false,
    isLoading: true,
  });

  useEffect(() => {
    auth.refresh()
      .then((tokens) => {
        setState({
          token: tokens.access_token,
          isAuthenticated: true,
          isLoading: false,
        });
      })
      .catch(() => {
        setAccessToken(null);
        setState({
          token: null,
          isAuthenticated: false,
          isLoading: false,
        });
      });
  }, []);

  const login = async (username: string, password: string) => {
    const response = await auth.login({ username, password });
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

  const logout = async () => {
    await auth.logout().catch(() => undefined);
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
