const API_BASE = '/api';

interface FetchOptions extends RequestInit {
  token?: string;
}

async function fetchApi<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { token, ...fetchOptions } = options;
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...fetchOptions,
    headers,
  });
  
  // Handle 401 Unauthorized - clear tokens and redirect to login
  if (response.status === 401) {
    localStorage.removeItem('perkle_token');
    localStorage.removeItem('perkle_refresh');
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
    fetchApi<TokenResponse>('/auth/refresh', { 
      method: 'POST', 
      body: JSON.stringify({ refresh_token: refreshToken }) 
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
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE}/transactions/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData,
    });
    
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
  muted: boolean;
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
  muted?: boolean;
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
    fetchApi<BenefitStatusResponse>('/benefits/status?include_muted=true', { token }),
  
  detect: (token: string) =>
    fetchApi<DetectionResult>('/benefits/detect', { token, method: 'POST' }),
  
  markUsed: (token: string, userCardId: string, benefitSlug: string, amount?: number, notes?: string) =>
    fetchApi('/benefits/mark-used', {
      token,
      method: 'POST',
      body: JSON.stringify({ user_card_id: userCardId, benefit_slug: benefitSlug, amount, notes }),
    }),
};
