import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { benefits, type BenefitStatusResponse, type BenefitStatus } from '../lib/api';
import { CheckCircle, AlertCircle, Circle, Clock, ChevronRight, Info, CreditCard } from 'lucide-react';
import { cn } from '../lib/utils';

function StatusIcon({ status }: { status: BenefitStatus['status'] }) {
  switch (status) {
    case 'used':
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    case 'partial':
      return <Clock className="w-5 h-5 text-yellow-500" />;
    case 'expiring':
      return <AlertCircle className="w-5 h-5 text-orange-500" />;
    case 'expired':
      return <Circle className="w-5 h-5 text-red-400" />;
    case 'info':
      return <Info className="w-5 h-5 text-blue-400" />;
    default:
      return <Circle className="w-5 h-5 text-gray-300" />;
  }
}

function BenefitItem({ benefit }: { benefit: BenefitStatus }) {
  const percentage = benefit.amount_limit > 0 
    ? Math.min(100, (benefit.amount_used / benefit.amount_limit) * 100) 
    : 0;

  // Info-only benefits show differently
  if (benefit.tracking_mode === 'info') {
    return (
      <div className="flex items-center gap-3 p-3 rounded-lg bg-blue-50">
        <StatusIcon status="info" />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm truncate text-blue-900">{benefit.name}</p>
          <p className="text-xs text-blue-600">Auto - no action needed</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn(
      "flex items-center gap-3 p-3 rounded-lg",
      benefit.status === 'expiring' && "bg-orange-50",
      benefit.status === 'used' && "bg-green-50",
    )}>
      <StatusIcon status={benefit.status} />
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm truncate">{benefit.name}</p>
        <div className="flex items-center gap-2 mt-1">
          <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className={cn(
                "h-full rounded-full transition-all",
                benefit.status === 'used' ? "bg-green-500" :
                benefit.status === 'partial' ? "bg-yellow-500" :
                benefit.status === 'expiring' ? "bg-orange-500" : "bg-gray-300"
              )}
              style={{ width: `${percentage}%` }}
            />
          </div>
          <span className="text-xs text-gray-500 whitespace-nowrap">
            ${benefit.amount_used.toFixed(0)}/${benefit.value}
          </span>
        </div>
      </div>
      {benefit.days_remaining <= 7 && benefit.days_remaining > 0 && (
        <span className="text-xs text-orange-600 font-medium">
          {benefit.days_remaining}d left
        </span>
      )}
    </div>
  );
}

export default function Dashboard() {
  const { token, logout } = useAuth();
  const [data, setData] = useState<BenefitStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) return;
    
    benefits.getStatus(token)
      .then(setData)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="text-center">
          <p className="text-red-600">{error}</p>
          <button onClick={() => window.location.reload()} className="mt-4 text-blue-600">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data || data.cards.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold">🎯 Perkle</h1>
            <button onClick={logout} className="text-sm text-gray-600">Logout</button>
          </div>
        </header>
        <div className="p-4 text-center mt-20">
          <p className="text-gray-600 mb-4">No cards in your portfolio yet.</p>
          <Link to="/cards" className="text-blue-600 hover:underline">
            Add your first card →
          </Link>
        </div>
      </div>
    );
  }

  const { summary, cards: cardStatuses } = data;

  // Calculate aggregate unused benefits across all cards
  const allUnusedBenefits = cardStatuses.flatMap(card => 
    card.benefits
      .filter(b => b.tracking_mode !== 'info' && b.status !== 'used' && !b.muted)
      .map(b => ({
        ...b,
        cardName: card.card_name,
        cardId: card.user_card_id,
      }))
  ).sort((a, b) => a.days_remaining - b.days_remaining); // Sort by urgency

  const totalUnusedValue = allUnusedBenefits.reduce((sum, b) => sum + (b.value - b.amount_used), 0);

  // Aggregate stats by cadence (excluding muted benefits)
  const allBenefits = cardStatuses.flatMap(card => card.benefits.filter(b => b.tracking_mode !== 'info' && !b.muted));
  const cadenceStats = {
    monthly: { used: 0, available: 0 },
    quarterly: { used: 0, available: 0 },
    'semi-annual': { used: 0, available: 0 },
    annual: { used: 0, available: 0 },
  };
  
  for (const b of allBenefits) {
    const cadence = b.cadence as keyof typeof cadenceStats;
    if (cadenceStats[cadence]) {
      cadenceStats[cadence].used += b.amount_used;
      cadenceStats[cadence].available += b.status !== 'used' ? (b.amount_limit - b.amount_used) : 0;
    }
  }
  
  // Filter to only show cadences with benefits
  const activeCadences = Object.entries(cadenceStats).filter(([_, stats]) => stats.used > 0 || stats.available > 0);

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <header className="bg-white border-b px-4 py-4 sticky top-0 z-10">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">🎯 Perkle</h1>
          <button onClick={logout} className="text-sm text-gray-600">Logout</button>
        </div>
      </header>

      {/* Summary by Cadence */}
      <div className="bg-gradient-to-br from-blue-600 to-blue-700 text-white p-6 mx-4 mt-4 rounded-2xl">
        <p className="text-blue-100 text-sm mb-3">Benefits Used</p>
        
        {/* Cadence breakdown */}
        <div className="space-y-3">
          {activeCadences.map(([cadence, stats]) => {
            const total = stats.used + stats.available;
            const pct = total > 0 ? (stats.used / total) * 100 : 0;
            return (
              <div key={cadence}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-blue-100 capitalize">{cadence.replace('-', ' ')}</span>
                  <span className="font-medium">
                    ${stats.used.toFixed(0)} / ${total.toFixed(0)}
                  </span>
                </div>
                <div className="h-2 bg-blue-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-white rounded-full transition-all"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
        
        {summary.expiring_soon_count > 0 && (
          <div className="mt-4 pt-3 border-t border-blue-500">
            <p className="text-orange-300 text-sm">
              ⚠️ {summary.expiring_soon_count} benefit{summary.expiring_soon_count > 1 ? 's' : ''} expiring soon
            </p>
          </div>
        )}
      </div>

      {/* Renewal Warnings */}
      {cardStatuses.some(c => c.days_until_renewal && c.days_until_renewal <= 30) && (
        <div className="mx-4 mt-4 p-4 bg-amber-50 border border-amber-200 rounded-xl">
          <div className="flex items-center gap-2 text-amber-800">
            <CreditCard className="w-5 h-5" />
            <span className="font-medium">Upcoming Renewals</span>
          </div>
          <div className="mt-2 space-y-1">
            {cardStatuses
              .filter(c => c.days_until_renewal && c.days_until_renewal <= 30)
              .map(c => (
                <p key={c.user_card_id} className="text-sm text-amber-700">
                  {c.card_name}: ${c.annual_fee} in {c.days_until_renewal} days
                </p>
              ))}
          </div>
        </div>
      )}

      {/* Aggregate Unused Benefits */}
      {allUnusedBenefits.length > 0 && (
        <div className="mx-4 mt-4 bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="p-4 border-b">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-semibold">💰 Unused Benefits</h2>
                <p className="text-sm text-gray-500">
                  ${totalUnusedValue.toFixed(0)} available across {allUnusedBenefits.length} benefits
                </p>
              </div>
            </div>
          </div>
          <div className="p-2 space-y-1 max-h-64 overflow-y-auto">
            {allUnusedBenefits.slice(0, 8).map((benefit) => (
              <Link
                key={`${benefit.cardId}-${benefit.slug}`}
                to={`/card/${benefit.cardId}`}
                className={cn(
                  "flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50",
                  benefit.status === 'expiring' && "bg-orange-50",
                )}
              >
                <StatusIcon status={benefit.status} />
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{benefit.name}</p>
                  <p className="text-xs text-gray-500 truncate">{benefit.cardName}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">${(benefit.value - benefit.amount_used).toFixed(0)}</p>
                  {benefit.days_remaining <= 7 && (
                    <p className="text-xs text-orange-600">{benefit.days_remaining}d left</p>
                  )}
                </div>
              </Link>
            ))}
            {allUnusedBenefits.length > 8 && (
              <p className="text-xs text-gray-400 text-center py-2">
                +{allUnusedBenefits.length - 8} more benefits
              </p>
            )}
          </div>
        </div>
      )}

      {/* Cards */}
      <div className="p-4 space-y-4">
        {cardStatuses.map((card) => {
          const trackableBenefits = card.benefits.filter(b => b.tracking_mode !== 'info');
          const usedCount = trackableBenefits.filter(b => b.status === 'used').length;
          const expiringCount = trackableBenefits.filter(b => b.status === 'expiring').length;
          
          // Sort: unused/expiring first, partial second, used third, info last
          // Secondary sort by slug for stability
          const sortedBenefits = [...card.benefits].sort((a, b) => {
            const statusOrder = (status: string, trackingMode: string) => {
              if (trackingMode === 'info') return 4;
              if (status === 'used') return 3;
              if (status === 'partial') return 2;
              return 1; // available, expiring, expired
            };
            const orderDiff = statusOrder(a.status, a.tracking_mode) - statusOrder(b.status, b.tracking_mode);
            if (orderDiff !== 0) return orderDiff;
            return a.slug.localeCompare(b.slug);
          });
          
          return (
            <Link
              key={card.user_card_id}
              to={`/card/${card.user_card_id}`}
              className="block bg-white rounded-xl shadow-sm overflow-hidden"
            >
              <div className="p-4 border-b flex items-center justify-between">
                <div>
                  <h2 className="font-semibold">{card.card_name}</h2>
                  <p className="text-sm text-gray-500">
                    {usedCount}/{trackableBenefits.length} used
                    {expiringCount > 0 && (
                      <span className="text-orange-600 ml-2">
                        • {expiringCount} expiring
                      </span>
                    )}
                    {card.days_until_renewal && card.days_until_renewal <= 30 && (
                      <span className="text-amber-600 ml-2">
                        • Renews in {card.days_until_renewal}d
                      </span>
                    )}
                  </p>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-400" />
              </div>
              <div className="p-2 space-y-1 max-h-48 overflow-y-auto">
                {sortedBenefits
                  .filter(b => b.status !== 'available' || b.days_remaining <= 14)
                  .slice(0, 4)
                  .map((benefit) => (
                    <BenefitItem key={benefit.slug} benefit={benefit} />
                  ))}
                {sortedBenefits.filter(b => b.status === 'available' && b.days_remaining > 14).length > 0 && (
                  <p className="text-xs text-gray-400 text-center py-2">
                    +{sortedBenefits.filter(b => b.status === 'available' && b.days_remaining > 14).length} more available
                  </p>
                )}
              </div>
            </Link>
          );
        })}
      </div>

      {/* Bottom Nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t px-4 py-2 flex justify-around">
        <Link to="/" className="flex flex-col items-center py-2 px-4 text-blue-600">
          <span className="text-xl">📊</span>
          <span className="text-xs mt-1">Dashboard</span>
        </Link>
        <Link to="/upload" className="flex flex-col items-center py-2 px-4 text-gray-600">
          <span className="text-xl">📤</span>
          <span className="text-xs mt-1">Upload</span>
        </Link>
        <Link to="/cards" className="flex flex-col items-center py-2 px-4 text-gray-600">
          <span className="text-xl">💳</span>
          <span className="text-xs mt-1">Cards</span>
        </Link>
      </nav>
    </div>
  );
}
