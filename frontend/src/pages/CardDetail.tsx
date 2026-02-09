import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { benefits, cards, type BenefitStatusResponse, type BenefitStatus } from '../lib/api';
import { ArrowLeft, CheckCircle, Circle, Clock, AlertCircle, Info, EyeOff, Eye, CreditCard, X, DollarSign, ExternalLink } from 'lucide-react';
import { cn } from '../lib/utils';

export default function CardDetail() {
  const { cardId } = useParams<{ cardId: string }>();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState<BenefitStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [marking, setMarking] = useState<string | null>(null);
  const [hiding, setHiding] = useState<string | null>(null);
  const [amountModal, setAmountModal] = useState<BenefitStatus | null>(null);
  const [customAmount, setCustomAmount] = useState('');

  useEffect(() => {
    if (!token) return;

    benefits.getStatus()
      .then(setData)
      .finally(() => setLoading(false));
  }, [token]);

  const card = data?.cards.find(c => c.user_card_id === cardId);

  const handleMarkUsed = async (benefit: BenefitStatus, amount?: number) => {
    if (!token || !cardId) return;
    setMarking(benefit.slug);

    try {
      await benefits.markUsed(cardId, benefit.slug, amount);
      // Refresh data
      const updated = await benefits.getStatus();
      setData(updated);
      setAmountModal(null);
      setCustomAmount('');
    } catch (err) {
      console.error(err);
    } finally {
      setMarking(null);
    }
  };

  const openAmountModal = (benefit: BenefitStatus) => {
    setAmountModal(benefit);
    // Pre-fill with remaining amount
    const remaining = benefit.value - benefit.amount_used;
    setCustomAmount(remaining.toFixed(2));
  };

  const validateAndSubmitAmount = (benefit: BenefitStatus) => {
    const amount = parseFloat(customAmount);
    const remaining = benefit.value - benefit.amount_used;
    
    if (isNaN(amount) || amount <= 0) {
      alert('Please enter a valid positive amount');
      return;
    }
    if (amount > remaining) {
      alert(`Amount cannot exceed remaining credit ($${remaining.toFixed(2)})`);
      return;
    }
    
    handleMarkUsed(benefit, amount);
  };

  const handleToggleHidden = async (benefit: BenefitStatus) => {
    if (!token || !cardId) return;
    setHiding(benefit.slug);

    try {
      await cards.updateBenefitSetting(cardId, {
        benefit_slug: benefit.slug,
        hidden: !benefit.hidden,
      });
      // Refresh data
      const updated = await benefits.getStatus();
      setData(updated);
    } catch (err) {
      console.error(err);
    } finally {
      setHiding(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!card) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="text-center">
          <p className="text-gray-600">Card not found</p>
          <button onClick={() => navigate('/')} className="mt-4 text-blue-600">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const statusIcon = (status: BenefitStatus['status']) => {
    switch (status) {
      case 'used':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'partial':
        return <Clock className="w-6 h-6 text-yellow-500" />;
      case 'expiring':
        return <AlertCircle className="w-6 h-6 text-orange-500" />;
      case 'info':
        return <Info className="w-6 h-6 text-blue-400" />;
      default:
        return <Circle className="w-6 h-6 text-gray-300" />;
    }
  };

  const trackableBenefits = card?.benefits.filter(b => b.tracking_mode !== 'info') || [];

  // Sort benefits: hidden at bottom, then by status priority
  // Secondary sort by slug for stability
  const sortedBenefits = [...(card?.benefits || [])].sort((a, b) => {
    // Hidden benefits always go to the bottom
    if (a.hidden && !b.hidden) return 1;
    if (!a.hidden && b.hidden) return -1;
    
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
  
  // Check if there are hidden benefits to show a divider
  const hasHiddenBenefits = sortedBenefits.some(b => b.hidden);
  const firstHiddenIndex = sortedBenefits.findIndex(b => b.hidden);

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Amount Input Modal */}
      {amountModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 max-w-sm w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Record Usage</h3>
              <button
                onClick={() => {
                  setAmountModal(null);
                  setCustomAmount('');
                }}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-sm text-gray-600 mb-4">{amountModal.name}</p>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Amount Used
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  max={amountModal.value - amountModal.amount_used}
                  value={customAmount}
                  onChange={(e) => setCustomAmount(e.target.value)}
                  className="w-full pl-8 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="0.00"
                />
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Already used: ${amountModal.amount_used.toFixed(2)} / ${amountModal.value} limit
                <br />
                Remaining: ${(amountModal.value - amountModal.amount_used).toFixed(2)}
              </p>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => validateAndSubmitAmount(amountModal)}
                disabled={marking === amountModal.slug}
                className="flex-1 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {marking === amountModal.slug ? 'Recording...' : 'Record'}
              </button>
              <button
                onClick={() => handleMarkUsed(amountModal, amountModal.value - amountModal.amount_used)}
                disabled={marking === amountModal.slug}
                className="px-4 py-3 border rounded-lg hover:bg-gray-50"
                title="Mark full remaining amount as used"
              >
                Full
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="bg-white border-b px-4 py-4">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/')} className="p-1">
            <ArrowLeft className="w-6 h-6" />
          </button>
          <div className="flex-1">
            <h1 className="font-bold">{card.card_name}</h1>
            <p className="text-sm text-gray-500">
              {trackableBenefits.length} benefits
              {card.annual_fee > 0 && ` • $${card.annual_fee}/yr`}
            </p>
          </div>
          {card.benefits_url && (
            <a
              href={card.benefits_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
            >
              <ExternalLink className="w-4 h-4" />
              <span className="hidden sm:inline">Benefits</span>
            </a>
          )}
        </div>
      </header>

      {/* Renewal Info */}
      {card.days_until_renewal && (
        <div className={cn(
          "mx-4 mt-4 p-4 rounded-xl flex items-center gap-3",
          card.days_until_renewal <= 30 
            ? "bg-amber-50 border border-amber-200" 
            : "bg-gray-50 border border-gray-200"
        )}>
          <CreditCard className={cn(
            "w-5 h-5",
            card.days_until_renewal <= 30 ? "text-amber-600" : "text-gray-500"
          )} />
          <div>
            <p className={cn(
              "text-sm font-medium",
              card.days_until_renewal <= 30 ? "text-amber-800" : "text-gray-700"
            )}>
              {card.days_until_renewal <= 30 ? "Annual fee renews soon" : "Annual fee renewal"}
            </p>
            <p className={cn(
              "text-xs",
              card.days_until_renewal <= 30 ? "text-amber-600" : "text-gray-500"
            )}>
              ${card.annual_fee} in {card.days_until_renewal} days
              {card.next_renewal_date && ` (${card.next_renewal_date})`}
            </p>
          </div>
        </div>
      )}

      {/* Benefits List */}
      <div className="p-4 space-y-3">
        {sortedBenefits.map((benefit, index) => {
          // Show divider before first hidden benefit
          const showHiddenDivider = hasHiddenBenefits && index === firstHiddenIndex;
          const percentage = benefit.amount_limit > 0
            ? Math.min(100, (benefit.amount_used / benefit.amount_limit) * 100)
            : 0;

          // Info-only benefits (like anniversary bonus)
          if (benefit.tracking_mode === 'info') {
            return (
              <React.Fragment key={benefit.slug}>
                {showHiddenDivider && (
                  <div className="text-xs text-gray-400 uppercase tracking-wide pt-2 pb-1 flex items-center gap-2">
                    <EyeOff className="w-3 h-3" />
                    Hidden Benefits
                  </div>
                )}
                <div className="bg-blue-50 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  {statusIcon('info')}
                  <div className="flex-1">
                    <h3 className="font-medium text-blue-900">{benefit.name}</h3>
                    <p className="text-sm text-blue-600">Automatic • ${benefit.value} value</p>
                    {benefit.notes && (
                      <p className="text-sm text-blue-700 mt-2 bg-blue-100 p-2 rounded">
                        💡 {benefit.notes}
                      </p>
                    )}
                  </div>
                </div>
              </div>
              </React.Fragment>
            );
          }

          return (
            <React.Fragment key={benefit.slug}>
              {showHiddenDivider && (
                <div className="text-xs text-gray-400 uppercase tracking-wide pt-2 pb-1 flex items-center gap-2">
                  <EyeOff className="w-3 h-3" />
                  Hidden Benefits
                </div>
              )}
              <div
              className={cn(
                "bg-white rounded-xl p-4",
                benefit.status === 'expiring' && "ring-2 ring-orange-200",
                benefit.hidden && "opacity-60",
              )}
            >
              <div className="flex items-start gap-3">
                {statusIcon(benefit.status)}
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium">{benefit.name}</h3>
                      <p className="text-sm text-gray-500 capitalize">
                        {benefit.cadence}
                        {benefit.reset_type === 'cardmember_year' && ' (card year)'}
                      </p>
                    </div>
                    {/* Hide toggle */}
                    <button
                      onClick={() => handleToggleHidden(benefit)}
                      disabled={hiding === benefit.slug}
                      className="group flex items-center gap-1 p-2 text-gray-400 hover:text-gray-600"
                      title={benefit.hidden ? 'Show benefit' : 'Hide benefit'}
                    >
                      <span className="text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                        {benefit.hidden ? 'Unhide' : 'Hide'}
                      </span>
                      {hiding === benefit.slug ? (
                        <div className="w-5 h-5 animate-spin rounded-full border-2 border-gray-400 border-t-transparent" />
                      ) : benefit.hidden ? (
                        <EyeOff className="w-5 h-5" />
                      ) : (
                        <Eye className="w-5 h-5" />
                      )}
                    </button>
                  </div>

                  {/* Progress */}
                  <div className="mt-3">
                    <div className="flex justify-between text-sm mb-1">
                      <span>${benefit.amount_used.toFixed(2)} used</span>
                      <span className="text-gray-500">${benefit.value} limit</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={cn(
                          "h-full rounded-full transition-all",
                          benefit.status === 'used' ? "bg-green-500" :
                          benefit.status === 'partial' ? "bg-yellow-500" :
                          benefit.status === 'expiring' ? "bg-orange-500" : "bg-blue-500"
                        )}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>

                  {/* Period */}
                  <p className="text-xs text-gray-400 mt-2">
                    Period: {benefit.period_start} to {benefit.period_end}
                    {benefit.days_remaining > 0 && ` • ${benefit.days_remaining} days left`}
                  </p>

                  {/* Notes */}
                  {benefit.notes && (
                    <p className="text-sm text-gray-600 mt-2 bg-gray-50 p-2 rounded">
                      💡 {benefit.notes}
                    </p>
                  )}

                  {/* Manual tracking button */}
                  {benefit.tracking_mode === 'manual' && benefit.status !== 'used' && (
                    <button
                      onClick={() => openAmountModal(benefit)}
                      disabled={marking === benefit.slug}
                      className="mt-3 w-full py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      {benefit.amount_used > 0 ? 'Add More Usage' : 'Record Usage'}
                    </button>
                  )}
                </div>
              </div>
            </div>
            </React.Fragment>
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
