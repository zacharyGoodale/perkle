import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { cards, type CardConfig, type UserCard } from '../lib/api';
import { Plus, Trash2, Check, X, Calendar } from 'lucide-react';

export default function Cards() {
  const { token } = useAuth();
  const [availableCards, setAvailableCards] = useState<CardConfig[]>([]);
  const [myCards, setMyCards] = useState<UserCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState<string | null>(null);
  const [showAnniversaryModal, setShowAnniversaryModal] = useState<CardConfig | null>(null);
  const [anniversaryMonth, setAnniversaryMonth] = useState('');
  const [anniversaryDay, setAnniversaryDay] = useState('');

  useEffect(() => {
    if (!token) return;

    Promise.all([
      cards.getAvailable(),
      cards.getMy(token),
    ])
      .then(([available, mine]) => {
        setAvailableCards(available);
        setMyCards(mine);
      })
      .finally(() => setLoading(false));
  }, [token]);

  // All cards prompt for anniversary date so renewal warnings work
  const needsAnniversary = (_cardConfig: CardConfig) => {
    return true; // Always prompt for anniversary to enable renewal reminders
  };

  const handleAddCard = async (cardConfig: CardConfig, anniversary?: string) => {
    if (!token) return;
    setAdding(cardConfig.id);

    try {
      const newCard = await cards.add(token, cardConfig.id, undefined, anniversary);
      setMyCards([...myCards, newCard]);
      setShowAnniversaryModal(null); setAnniversaryMonth(''); setAnniversaryDay('');
      setAnniversaryMonth(''); setAnniversaryDay('');
    } catch (err) {
      console.error(err);
    } finally {
      setAdding(null);
    }
  };

  const handleCardClick = (cardConfig: CardConfig) => {
    if (needsAnniversary(cardConfig)) {
      setShowAnniversaryModal(cardConfig);
    } else {
      handleAddCard(cardConfig);
    }
  };

  const handleRemoveCard = async (userCardId: string) => {
    if (!token) return;

    try {
      await cards.remove(token, userCardId);
      setMyCards(myCards.filter(c => c.id !== userCardId));
    } catch (err) {
      console.error(err);
    }
  };

  const myCardConfigIds = new Set(myCards.map(c => c.card_config_id));

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Anniversary Date Modal */}
      {showAnniversaryModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 max-w-sm w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Add {showAnniversaryModal.name}</h3>
              <button 
                onClick={() => {
                  setShowAnniversaryModal(null);
                  setAnniversaryMonth(''); setAnniversaryDay('');
                }}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-1" />
                Card Anniversary (Month & Day)
              </label>
              <div className="flex gap-2">
                <select
                  value={anniversaryMonth}
                  onChange={(e) => setAnniversaryMonth(e.target.value)}
                  className="flex-1 p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Month</option>
                  <option value="01">January</option>
                  <option value="02">February</option>
                  <option value="03">March</option>
                  <option value="04">April</option>
                  <option value="05">May</option>
                  <option value="06">June</option>
                  <option value="07">July</option>
                  <option value="08">August</option>
                  <option value="09">September</option>
                  <option value="10">October</option>
                  <option value="11">November</option>
                  <option value="12">December</option>
                </select>
                <select
                  value={anniversaryDay}
                  onChange={(e) => setAnniversaryDay(e.target.value)}
                  className="flex-1 p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Day</option>
                  {Array.from({ length: 31 }, (_, i) => (
                    <option key={i + 1} value={String(i + 1).padStart(2, '0')}>
                      {i + 1}
                    </option>
                  ))}
                </select>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                The day your annual fee posts or when you were approved.
              </p>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => handleAddCard(showAnniversaryModal, anniversaryMonth && anniversaryDay ? `${anniversaryMonth}-${anniversaryDay}` : undefined)}
                disabled={adding === showAnniversaryModal.id}
                className="flex-1 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {adding === showAnniversaryModal.id ? 'Adding...' : 'Add Card'}
              </button>
              <button
                onClick={() => handleAddCard(showAnniversaryModal)}
                disabled={adding === showAnniversaryModal.id}
                className="px-4 py-3 border rounded-lg hover:bg-gray-50"
              >
                Skip
              </button>
            </div>
          </div>
        </div>
      )}

      <header className="bg-white border-b px-4 py-4">
        <h1 className="text-xl font-bold">💳 My Cards</h1>
      </header>

      <div className="p-4 space-y-6">
        {/* My Cards */}
        {myCards.length > 0 && (
          <section>
            <h2 className="text-sm font-medium text-gray-500 mb-3">IN PORTFOLIO</h2>
            <div className="space-y-2">
              {myCards.map((card) => (
                <div
                  key={card.id}
                  className="bg-white rounded-xl p-4 flex items-center justify-between"
                >
                  <div>
                    <p className="font-medium">{card.card_name}</p>
                    <p className="text-sm text-gray-500">{card.card_issuer}</p>
                  </div>
                  <button
                    onClick={() => handleRemoveCard(card.id)}
                    className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Available Cards */}
        <section>
          <h2 className="text-sm font-medium text-gray-500 mb-3">AVAILABLE CARDS</h2>
          <div className="space-y-2">
            {availableCards
              .filter(c => !myCardConfigIds.has(c.id))
              .map((card) => (
                <div
                  key={card.id}
                  className="bg-white rounded-xl p-4 flex items-center justify-between"
                >
                  <div>
                    <p className="font-medium">{card.name}</p>
                    <p className="text-sm text-gray-500">
                      {card.issuer} • ${card.annual_fee}/yr • {card.benefits.length} benefits
                    </p>
                  </div>
                  <button
                    onClick={() => handleCardClick(card)}
                    disabled={adding === card.id}
                    className="p-2 bg-blue-100 text-blue-600 rounded-full hover:bg-blue-200 transition-colors disabled:opacity-50"
                  >
                    {adding === card.id ? (
                      <div className="w-5 h-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
                    ) : (
                      <Plus className="w-5 h-5" />
                    )}
                  </button>
                </div>
              ))}
            {availableCards.filter(c => !myCardConfigIds.has(c.id)).length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <Check className="w-12 h-12 mx-auto mb-2 text-green-500" />
                <p>All available cards added!</p>
              </div>
            )}
          </div>
        </section>
      </div>

      {/* Bottom Nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t px-4 py-2 flex justify-around">
        <Link to="/" className="flex flex-col items-center py-2 px-4 text-gray-600">
          <span className="text-xl">📊</span>
          <span className="text-xs mt-1">Dashboard</span>
        </Link>
        <Link to="/upload" className="flex flex-col items-center py-2 px-4 text-gray-600">
          <span className="text-xl">📤</span>
          <span className="text-xs mt-1">Upload</span>
        </Link>
        <Link to="/cards" className="flex flex-col items-center py-2 px-4 text-blue-600">
          <span className="text-xl">💳</span>
          <span className="text-xs mt-1">Cards</span>
        </Link>
      </nav>
    </div>
  );
}
