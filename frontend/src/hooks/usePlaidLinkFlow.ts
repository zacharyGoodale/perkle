import { useState, useCallback } from 'react';
import { usePlaidLink, type PlaidLinkOnSuccess, type PlaidLinkOnExit } from 'react-plaid-link';
import { plaid } from '../lib/api';

const LINK_TOKEN_KEY = 'plaid_link_token';

interface UsePlaidLinkFlowOptions {
  onSuccess?: (institutionName?: string) => void;
  onExit?: () => void;
  receivedRedirectUri?: string;
}

export function usePlaidLinkFlow({ onSuccess, onExit, receivedRedirectUri }: UsePlaidLinkFlowOptions = {}) {
  const [linkToken, setLinkToken] = useState<string | null>(
    receivedRedirectUri ? localStorage.getItem(LINK_TOKEN_KEY) : null,
  );
  const [isLoadingToken, setIsLoadingToken] = useState(false);
  const [isExchanging, setIsExchanging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLinkToken = useCallback(async () => {
    setIsLoadingToken(true);
    setError(null);
    try {
      const { link_token } = await plaid.createLinkToken();
      setLinkToken(link_token);
      localStorage.setItem(LINK_TOKEN_KEY, link_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize bank connection');
    } finally {
      setIsLoadingToken(false);
    }
  }, []);

  const handleSuccess: PlaidLinkOnSuccess = useCallback(async (publicToken, metadata) => {
    setIsExchanging(true);
    setError(null);
    try {
      const result = await plaid.exchangePublicToken(
        publicToken,
        metadata.institution?.institution_id,
        metadata.institution?.name,
      );
      localStorage.removeItem(LINK_TOKEN_KEY);
      onSuccess?.(result.institution_name);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect account');
    } finally {
      setIsExchanging(false);
    }
  }, [onSuccess]);

  const handleExit: PlaidLinkOnExit = useCallback((err) => {
    if (err) {
      setError(err.display_message || err.error_message || 'Connection cancelled');
    }
    onExit?.();
  }, [onExit]);

  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess: handleSuccess,
    onExit: handleExit,
    ...(receivedRedirectUri ? { receivedRedirectUri } : {}),
  });

  return { open, ready, isLoadingToken, isExchanging, error, linkToken, fetchLinkToken };
}
