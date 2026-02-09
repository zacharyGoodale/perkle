const API_BASE = '/api';

let accessToken: string | null = null;
let refreshInFlight: Promise<TokenResponse | null> | null = null;

interface FetchOptions extends RequestInit {
  retryOnUnauthorized?: boolean;
  withAuth?: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface MessageResponse {
  message: string;
}

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

async function refreshAccessToken(): Promise<TokenResponse | null> {
  if (refreshInFlight) {
    return refreshInFlight;
  }

  refreshInFlight = fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
  })
    .then(async (response) => {
      if (!response.ok) {
        setAccessToken(null);
        return null;
      }

      const refreshed = (await response.json()) as TokenResponse;
      setAccessToken(refreshed.access_token);
      return refreshed;
    })
    .catch(() => {
      setAccessToken(null);
      return null;
    })
    .finally(() => {
      refreshInFlight = null;
    });

  return refreshInFlight;
}

async function fetchApi<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { retryOnUnauthorized = true, withAuth = true, ...fetchOptions } = options;

  const headers = new Headers(fetchOptions.headers);
  if (!(fetchOptions.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  if (withAuth && accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...fetchOptions,
    headers,
    credentials: 'include',
  });

  if (response.status === 401 && withAuth && retryOnUnauthorized) {
    const refreshed = await refreshAccessToken();
    if (refreshed?.access_token) {
      return fetchApi<T>(endpoint, { ...fetchOptions, retryOnUnauthorized: false, withAuth: true });
    }

    setAccessToken(null);
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

export interface UserResponse {
  id: string;
  username: string;
  email: string;
  created_at: string;
}

export const auth = {
  login: async (data: LoginRequest) => {
    const tokens = await fetchApi<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
      withAuth: false,
      retryOnUnauthorized: false,
    });
    setAccessToken(tokens.access_token);
    return tokens;
  },

  register: (data: RegisterRequest) =>
    fetchApi<UserResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
      withAuth: false,
      retryOnUnauthorized: false,
    }),

  refresh: async () => {
    const tokens = await refreshAccessToken();
    if (!tokens) {
      throw new Error('Refresh failed');
    }
    return tokens;
  },

  logout: async () => {
    try {
      await fetchApi<MessageResponse>('/auth/logout', { method: 'POST' });
    } finally {
      setAccessToken(null);
    }
  },
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
  getAvailable: () => fetchApi<CardConfig[]>('/cards/available', { withAuth: false }),

  getMy: () => fetchApi<UserCard[]>('/cards/my'),

  add: (cardConfigId: string, nickname?: string, cardAnniversary?: string) =>
    fetchApi<UserCard>('/cards/my', {
      method: 'POST',
      body: JSON.stringify({
        card_config_id: cardConfigId,
        nickname,
        card_anniversary: cardAnniversary,
      }),
    }),

  remove: (userCardId: string) =>
    fetchApi<void>(`/cards/my/${userCardId}`, { method: 'DELETE' }),

  updateBenefitSetting: (userCardId: string, setting: BenefitSettingUpdate) =>
    fetchApi(`/cards/my/${userCardId}/benefits/settings`, {
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
  upload: async (file: File): Promise<UploadResult> => {
    const formData = new FormData();
    formData.append('file', file);

    const sendRequest = async (token: string) =>
      fetch(`${API_BASE}/transactions/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
        credentials: 'include',
      });

    const initialToken = getAccessToken();
    if (!initialToken) {
      throw new Error('Not authenticated');
    }

    let response = await sendRequest(initialToken);
    if (response.status === 401) {
      const refreshed = await refreshAccessToken();
      if (refreshed?.access_token) {
        response = await sendRequest(refreshed.access_token);
      } else {
        setAccessToken(null);
        window.location.href = '/login';
        throw new Error('Session expired');
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
  getStatus: () => fetchApi<BenefitStatusResponse>('/benefits/status?include_hidden=true'),

  detect: () =>
    fetchApi<DetectionResult>('/benefits/detect', { method: 'POST' }),

  markUsed: (userCardId: string, benefitSlug: string, amount?: number, notes?: string) =>
    fetchApi('/benefits/mark-used', {
      method: 'POST',
      body: JSON.stringify({ user_card_id: userCardId, benefit_slug: benefitSlug, amount, notes }),
    }),
};
