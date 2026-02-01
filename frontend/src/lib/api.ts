const API_BASE = '/api';
const ACCESS_TOKEN_KEY = 'perkle_token';
const REFRESH_TOKEN_KEY = 'perkle_refresh';
// TODO(auth): Move refresh tokens to HttpOnly cookies and keep access tokens in memory only.

interface FetchOptions extends RequestInit {
  token?: string;
  retryOnUnauthorized?: boolean;
}

interface RefreshResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

function getStoredToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function setStoredTokens(tokens: RefreshResponse) {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

function clearStoredTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

async function refreshAccessToken(): Promise<RefreshResponse | null> {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refreshToken) {
    return null;
  }

  const response = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    return null;
  }

  return response.json();
}

async function fetchApi<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { token, retryOnUnauthorized = true, ...fetchOptions } = options;
  const storedToken = getStoredToken();
  const authToken = storedToken ?? token;
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...fetchOptions,
    headers,
  });
  
  // Handle 401 Unauthorized - attempt refresh once before logging out
  if (response.status === 401 && retryOnUnauthorized) {
    const refreshed = await refreshAccessToken();
    if (refreshed?.access_token) {
      setStoredTokens(refreshed);
      return fetchApi<T>(endpoint, {
        ...fetchOptions,
        token: refreshed.access_token,
        retryOnUnauthorized: false,
      });
    }

    clearStoredTokens();
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || 'Request failed');
  }
  
  if (response.status === 204) {
    return {} as T;
  }
  
  return response.json();
}

// Auth
export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  username: string;
  email: string;
  created_at: string;
}

export const auth = {
  login: (data: LoginRequest) => 
    fetchApi<TokenResponse>('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  
  register: (data: RegisterRequest) =>
    fetchApi<UserResponse>('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  
  refresh: (refreshToken: string) =>
    fetch(`${API_BASE}/auth/refresh`, { 
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    }).then(async response => {
      if (!response.ok) {
        throw new Error('Refresh failed');
      }
      return response.json() as Promise<TokenResponse>;
    }),
};

// Cards
export interface Benefit {
  slug: string;
  name: string;
  value: number;
  cadence: string;
  tracking_mode: string;
  notes?: string;
}

export interface CardConfig {
  id: string;
  slug: string;
  name: string;
  issuer: string;
  annual_fee: number;
  benefits_url?: string;
  benefits: Benefit[];
}

export interface UserCard {
  id: string;
  card_config_id: string;
  card_slug: string;
  card_name: string;
  card_issuer: string;
  nickname?: string;
  card_anniversary?: string;
  active: boolean;
  added_at: string;
}

export const cards = {
  getAvailable: () => fetchApi<CardConfig[]>('/cards/available'),
  
  getMy: (token: string) => 
    fetchApi<UserCard[]>('/cards/my', { token }),
  
  add: (token: string, cardConfigId: string, nickname?: string, cardAnniversary?: string) =>
    fetchApi<UserCard>('/cards/my', {
      token,
      method: 'POST',
      body: JSON.stringify({ 
        card_config_id: cardConfigId, 
        nickname, 
        card_anniversary: cardAnniversary 
      }),
    }),
  
  remove: (token: string, userCardId: string) =>
    fetchApi<void>(`/cards/my/${userCardId}`, { token, method: 'DELETE' }),
  
  updateBenefitSetting: (token: string, userCardId: string, setting: BenefitSettingUpdate) =>
    fetchApi(`/cards/my/${userCardId}/benefits/settings`, {
      token,
      method: 'PUT',
      body: JSON.stringify(setting),
    }),
};

// Transactions
export interface UploadResult {
  imported: number;
  skipped: number;
  errors: string[];
  total_errors: number;
}

export const transactions = {
  upload: async (token: string, file: File): Promise<UploadResult> => {
    const storedToken = getStoredToken();
    const authToken = storedToken ?? token;
    const formData = new FormData();
    formData.append('file', file);
    
    const sendRequest = async (accessToken: string) =>
      fetch(`${API_BASE}/transactions/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${accessToken}` },
        body: formData,
      });
    
    let response = await sendRequest(authToken ?? '');
    if (response.status === 401) {
      const refreshed = await refreshAccessToken();
      if (refreshed?.access_token) {
        setStoredTokens(refreshed);
        response = await sendRequest(refreshed.access_token);
      }
    }
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || 'Upload failed');
    }
    
    return response.json();
  },
};

// Benefits
export interface BenefitStatus {
  slug: string;
  name: string;
  value: number;
  cadence: string;
  tracking_mode: 'auto' | 'manual' | 'info';
  reset_type?: 'calendar_year' | 'cardmember_year' | 'rolling_years';
  period_start: string;
  period_end: string;
  days_remaining: number;
  status: 'used' | 'partial' | 'expired' | 'expiring' | 'available' | 'info';
  amount_used: number;
  amount_limit: number;
  notes?: string;
  hidden: boolean;
}

export interface CardBenefitStatus {
  user_card_id: string;
  card_name: string;
  card_slug: string;
  card_anniversary?: string;
  next_renewal_date?: string;
  annual_fee: number;
  benefits_url?: string;
  days_until_renewal?: number;
  benefits: BenefitStatus[];
}

export interface BenefitSettingUpdate {
  benefit_slug: string;
  hidden?: boolean;
  notes?: string;
}

export interface BenefitStatusResponse {
  cards: CardBenefitStatus[];
  summary: {
    total_available_value: number;
    total_used_value: number;
    expiring_soon_count: number;
    cards_count: number;
  };
}

export interface DetectionResult {
  detected: number;
  cards_checked: number;
  benefits: Array<{
    card: string;
    benefit: string;
    amount: number;
    date: string;
    transaction: string;
  }>;
}

export const benefits = {
  getStatus: (token: string) =>
    fetchApi<BenefitStatusResponse>('/benefits/status?include_hidden=true', { token }),
  
  detect: (token: string) =>
    fetchApi<DetectionResult>('/benefits/detect', { token, method: 'POST' }),
  
  markUsed: (token: string, userCardId: string, benefitSlug: string, amount?: number, notes?: string) =>
    fetchApi('/benefits/mark-used', {
      token,
      method: 'POST',
      body: JSON.stringify({ user_card_id: userCardId, benefit_slug: benefitSlug, amount, notes }),
    }),
};
