import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { plaid, type PlaidItem } from '../lib/api';
import { CheckCircle, Loader2, Trash2 } from 'lucide-react';
import { cn } from '../lib/utils';
import PlaidLinkButton from '../components/PlaidLinkButton';

export default function Accounts() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [items, setItems] = useState<PlaidItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [removing, setRemoving] = useState<string | null>(null);
  const [plaidConnected, setPlaidConnected] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  const loadItems = () => {
    plaid.getItems()
      .then(setItems)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!token) return;
    loadItems();
  }, [token]);

  const handleSuccess = (name?: string) => {
    setPlaidConnected(name ?? 'your bank');
    loadItems();
  };

  const handleRemove = async (itemId: string) => {
    setRemoving(itemId);
    try {
      await plaid.removeItem(itemId);
      setItems(items.filter(i => i.id !== itemId));
    } catch {
      // ignore
    } finally {
      setRemoving(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      <header className="bg-white border-b px-4 py-4">
        <h1 className="text-xl font-bold">🏦 Accounts</h1>
      </header>

      <div className="p-4 space-y-4">
        {/* Just-connected success banner */}
        {plaidConnected && (
          <div className="bg-white rounded-xl p-4 text-center">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
            <h2 className="font-semibold text-lg">Bank Connected</h2>
            <p className="text-sm text-gray-500 mt-1">
              Successfully connected to {plaidConnected}. Your account has been linked successfully.
            </p>
            <button
              disabled={syncing}
              onClick={async () => {
                setSyncing(true);
                try {
                  await plaid.sync();
                } catch {
                  // still navigate — dashboard will show the account
                } finally {
                  navigate('/');
                }
              }}
              className="mt-4 w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {syncing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Syncing Transactions...
                </>
              ) : (
                'Sync Transactions & View Dashboard'
              )}
            </button>
          </div>
        )}

        {/* Connected accounts */}
        {items.length > 0 && (
          <section>
            <h2 className="text-sm font-medium text-gray-500 mb-3">CONNECTED ACCOUNTS</h2>
            <div className="space-y-2">
              {items.map((item) => (
                <div
                  key={item.id}
                  className="bg-white rounded-xl p-4 flex items-center justify-between"
                >
                  <div>
                    <p className="font-medium">{item.institution_name || 'Unknown Bank'}</p>
                    <p className={cn(
                      "text-sm",
                      item.status === 'error' ? 'text-red-500' : 'text-gray-500',
                    )}>
                      {item.status === 'error'
                        ? 'Needs reconnection'
                        : item.last_synced_at
                          ? `Last synced ${new Date(item.last_synced_at).toLocaleDateString()}`
                          : 'Never synced'}
                    </p>
                  </div>
                  <button
                    onClick={() => handleRemove(item.id)}
                    disabled={removing === item.id}
                    className="p-2 text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50"
                  >
                    {removing === item.id ? (
                      <div className="w-5 h-5 animate-spin rounded-full border-2 border-gray-400 border-t-transparent" />
                    ) : (
                      <Trash2 className="w-5 h-5" />
                    )}
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Connect new account (hidden after successful link to avoid dead button) */}
        {!plaidConnected && <section>
          <h2 className="text-sm font-medium text-gray-500 mb-3">
            {items.length > 0 ? 'ADD ANOTHER ACCOUNT' : 'CONNECT AN ACCOUNT'}
          </h2>
          <div className="p-4 bg-white rounded-xl">
            <p className="text-gray-600 text-sm mb-4">
              Connect your bank account to automatically import transactions. Your credentials are handled securely by Plaid and never stored by Perkle.
            </p>
            <PlaidLinkButton onSuccess={handleSuccess} />
          </div>
        </section>}
      </div>

      {/* Bottom Nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t px-4 py-2 flex justify-around">
        <Link to="/" className="flex flex-col items-center py-2 px-4 text-gray-600">
          <span className="text-xl">📊</span>
          <span className="text-xs mt-1">Dashboard</span>
        </Link>
        <Link to="/accounts" className="flex flex-col items-center py-2 px-4 text-blue-600">
          <span className="text-xl">🏦</span>
          <span className="text-xs mt-1">Accounts</span>
        </Link>
        <Link to="/cards" className="flex flex-col items-center py-2 px-4 text-gray-600">
          <span className="text-xl">💳</span>
          <span className="text-xs mt-1">Cards</span>
        </Link>
      </nav>
    </div>
  );
}
