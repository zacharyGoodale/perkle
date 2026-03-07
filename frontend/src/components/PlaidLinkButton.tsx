import { useEffect, useRef } from 'react';
import { Building2, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils';
import { usePlaidLinkFlow } from '../hooks/usePlaidLinkFlow';

interface PlaidLinkButtonProps {
  onSuccess?: (institutionName?: string) => void;
  className?: string;
}

export default function PlaidLinkButton({ onSuccess, className }: PlaidLinkButtonProps) {
  const { open, ready, isLoadingToken, isExchanging, error, linkToken, fetchLinkToken } =
    usePlaidLinkFlow({ onSuccess });
  const hasOpened = useRef(false);

  useEffect(() => {
    if (ready && linkToken && !hasOpened.current) {
      hasOpened.current = true;
      open();
    }
  }, [ready, linkToken, open]);

  const handleClick = () => {
    hasOpened.current = false;
    fetchLinkToken();
  };

  if (isExchanging) {
    return (
      <div className={cn('flex items-center justify-center gap-2 py-3 px-4 bg-blue-50 text-blue-700 rounded-lg', className)}>
        <Loader2 className="w-5 h-5 animate-spin" />
        Connecting...
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('space-y-3', className)}>
        <div className="flex items-center gap-2 p-3 bg-red-50 text-red-600 rounded-lg text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          {error}
        </div>
        <button
          onClick={handleClick}
          className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={handleClick}
      disabled={isLoadingToken}
      className={cn(
        'w-full flex items-center justify-center gap-2 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors',
        className,
      )}
    >
      {isLoadingToken ? (
        <>
          <Loader2 className="w-5 h-5 animate-spin" />
          Preparing...
        </>
      ) : (
        <>
          <Building2 className="w-5 h-5" />
          Connect your bank
        </>
      )}
    </button>
  );
}
