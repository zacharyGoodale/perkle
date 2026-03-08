import { useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Loader2, AlertCircle } from 'lucide-react';
import { usePlaidLinkFlow } from '../hooks/usePlaidLinkFlow';

export default function PlaidOAuthRedirect() {
  const navigate = useNavigate();
  const hasOpened = useRef(false);

  const { open, ready, error } = usePlaidLinkFlow({
    receivedRedirectUri: window.location.href,
    onSuccess: () => navigate('/accounts'),
  });

  useEffect(() => {
    if (ready && !hasOpened.current) {
      hasOpened.current = true;
      open();
    }
  }, [ready, open]);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl p-6 max-w-md w-full text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
          <h2 className="text-lg font-semibold">Connection Failed</h2>
          <p className="text-sm text-gray-600">{error}</p>
          <Link
            to="/upload"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Accounts
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center space-y-4">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600 mx-auto" />
        <p className="text-gray-600">Completing bank connection...</p>
      </div>
    </div>
  );
}
