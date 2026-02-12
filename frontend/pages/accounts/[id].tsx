import { useAuth } from "@clerk/nextjs";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import Layout from "../../components/Layout";
import ConfirmModal from "../../components/ConfirmModal";
import { API_URL } from "../../lib/config";

interface Instrument {
  symbol: string;
  name: string;
  instrument_type: string;
  current_price: number;
}

interface Position {
  id: string;
  symbol: string;
  quantity: number;
  current_price?: number;
}

interface Account {
  id: string;
  account_name: string;
  account_purpose: string;
  cash_balance: number;
  positions?: Position[];
}

export default function AccountDetail() {
  const { getToken } = useAuth();
  const router = useRouter();
  const { id } = router.query;
  const [account, setAccount] = useState<Account | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [editingAccount, setEditingAccount] = useState(false);
  const [editedAccount, setEditedAccount] = useState({ name: '', purpose: '', cash_balance: '' });
  const [editingPosition, setEditingPosition] = useState<string | null>(null);
  const [editedQuantity, setEditedQuantity] = useState('');
  const [showAddPosition, setShowAddPosition] = useState(false);
  const [newPosition, setNewPosition] = useState({ symbol: '', quantity: '' });
  const [searchTerm, setSearchTerm] = useState('');
  const [showSymbolSuggestions, setShowSymbolSuggestions] = useState(false);
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    positionId: string;
    symbol: string;
  }>({ isOpen: false, positionId: '', symbol: '' });

  const loadAccount = useCallback(async () => {
    if (!id) return;

    try {
      const token = await getToken();

      // Load account details
      const accountResponse = await fetch(`${API_URL}/api/accounts`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (accountResponse.ok) {
        const accounts = await accountResponse.json();
        const foundAccount = accounts.find((acc: Account) => acc.id === id);

        if (foundAccount) {
          setAccount(foundAccount);
          setEditedAccount({
            name: foundAccount.account_name,
            purpose: foundAccount.account_purpose,
            cash_balance: Number(foundAccount.cash_balance).toLocaleString('en-US'),
          });
        } else {
          setMessage({ type: 'error', text: 'Account not found' });
          setTimeout(() => router.push('/accounts'), 2000);
          return;
        }
      }

      // Load positions
      const positionsResponse = await fetch(
        `${API_URL}/api/accounts/${id}/positions`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (positionsResponse.ok) {
        const data = await positionsResponse.json();
        setPositions(data.positions || []);
      }

      // Load instruments for autocomplete
      const instrumentsResponse = await fetch(
        `${API_URL}/api/instruments`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (instrumentsResponse.ok) {
        const instrumentsData = await instrumentsResponse.json();
        setInstruments(instrumentsData);
      }

    } catch (error) {
      console.error('Error loading account:', error);
      setMessage({ type: 'error', text: 'Failed to load account details' });
    } finally {
      setLoading(false);
    }
  }, [id, getToken, router]);

  useEffect(() => {
    loadAccount();
  }, [loadAccount]);

  const handleSaveAccount = async () => {
    setSaving(true);
    setMessage(null);

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/accounts/${id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          account_name: editedAccount.name,
          account_purpose: editedAccount.purpose,
          cash_balance: parseFloat(editedAccount.cash_balance.replace(/,/g, '')),
        }),
      });

      if (response.ok) {
        const updatedAccount = await response.json();
        setAccount(updatedAccount);
        setEditingAccount(false);
        setMessage({ type: 'success', text: 'Account updated successfully' });
      } else {
        setMessage({ type: 'error', text: 'Failed to update account' });
      }
    } catch (error) {
      console.error('Error updating account:', error);
      setMessage({ type: 'error', text: 'Error updating account' });
    } finally {
      setSaving(false);
    }
  };

  const handleUpdatePosition = async (positionId: string) => {
    const quantity = parseFloat(editedQuantity);
    if (isNaN(quantity) || quantity < 0) {
      setMessage({ type: 'error', text: 'Please enter a valid quantity' });
      return;
    }

    setSaving(true);
    setMessage(null);

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/positions/${positionId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          quantity: quantity,
        }),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Position updated successfully' });
        setEditingPosition(null);
        await loadAccount();
      } else {
        setMessage({ type: 'error', text: 'Failed to update position' });
      }
    } catch (error) {
      console.error('Error updating position:', error);
      setMessage({ type: 'error', text: 'Error updating position' });
    } finally {
      setSaving(false);
    }
  };

  const handleDeletePosition = async (positionId: string) => {
    setSaving(true);
    setMessage(null);

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/positions/${positionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Position deleted successfully' });
        await loadAccount();
      } else {
        setMessage({ type: 'error', text: 'Failed to delete position' });
      }
    } catch (error) {
      console.error('Error deleting position:', error);
      setMessage({ type: 'error', text: 'Error deleting position' });
    } finally {
      setSaving(false);
    }
  };

  const handleAddPosition = async () => {
    if (!newPosition.symbol.trim() || !newPosition.quantity.trim()) {
      setMessage({ type: 'error', text: 'Please enter symbol and quantity' });
      return;
    }

    const quantity = parseFloat(newPosition.quantity);
    if (isNaN(quantity) || quantity <= 0) {
      setMessage({ type: 'error', text: 'Please enter a valid quantity' });
      return;
    }

    setSaving(true);
    setMessage(null);

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/positions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          account_id: id,
          symbol: newPosition.symbol.toUpperCase(),
          quantity: quantity,
        }),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Position added successfully' });
        setShowAddPosition(false);
        setNewPosition({ symbol: '', quantity: '' });
        setSearchTerm('');
        await loadAccount();
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Failed to add position' });
      }
    } catch (error) {
      console.error('Error adding position:', error);
      setMessage({ type: 'error', text: 'Error adding position' });
    } finally {
      setSaving(false);
    }
  };

  const formatCurrencyInput = (value: string) => {
    const cleaned = value.replace(/[^0-9.]/g, '');
    const parts = cleaned.split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return parts.join('.');
  };

  const calculatePositionsValue = () => {
    return positions.reduce((sum, position) => {
      return sum + (Number(position.quantity) * (position.current_price || 0));
    }, 0);
  };

  const calculateTotalValue = () => {
    return (account ? Number(account.cash_balance) : 0) + calculatePositionsValue();
  };

  const filteredInstruments = instruments.filter(inst =>
    inst.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
    inst.name.toLowerCase().includes(searchTerm.toLowerCase())
  ).slice(0, 5);

  if (loading) {
    return (
      <>
        <Head>
          <title>Account Details - Alex AI Financial Advisor</title>
        </Head>
        <Layout>
          <div className="dashboard-premium-wrapper">
            <div className="dashboard-premium">
              <div className="dashboard-content max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="card-premium p-6">
                  <p className="text-center text-[#6B6B6B]">Loading account details...</p>
                </div>
              </div>
            </div>
          </div>
        </Layout>
      </>
    );
  }

  if (!account) {
    return (
      <>
        <Head>
          <title>Account Details - Alex AI Financial Advisor</title>
        </Head>
        <Layout>
          <div className="dashboard-premium-wrapper">
            <div className="dashboard-premium">
              <div className="dashboard-content max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="card-premium p-6">
                  <p className="text-center text-red-400">Account not found</p>
                </div>
              </div>
            </div>
          </div>
        </Layout>
      </>
    );
  }

  return (
    <>
      <Head>
        <title>{account.account_name} - Alex AI Financial Advisor</title>
      </Head>
      <Layout>
        <div className="dashboard-premium-wrapper">
          <div className="dashboard-premium">
            <div className="dashboard-content max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb */}
        <div className="mb-4">
          <button
            onClick={() => router.push('/accounts')}
            className="text-[#D4AF37] hover:text-[#E8D48A] flex items-center gap-1 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Accounts
          </button>
        </div>

        {/* Account Details */}
        <div className="card-premium rounded-xl p-6 mb-6">
          <div className="flex justify-between items-start mb-6">
            <div className="flex-1">
              {editingAccount ? (
                <div className="space-y-4 max-w-md">
                  <div>
                    <label className="block text-sm font-medium text-[#A3A3A3] mb-1">
                      Account Name
                    </label>
                    <input
                      type="text"
                      value={editedAccount.name}
                      onChange={(e) => setEditedAccount({ ...editedAccount, name: e.target.value })}
                      className="input-premium w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#A3A3A3] mb-1">
                      Account Purpose
                    </label>
                    <input
                      type="text"
                      value={editedAccount.purpose}
                      onChange={(e) => setEditedAccount({ ...editedAccount, purpose: e.target.value })}
                      className="input-premium w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#A3A3A3] mb-1">
                      Cash Balance
                    </label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 transform -translate-y-1/2 text-[#6B6B6B]">$</span>
                      <input
                        type="text"
                        value={editedAccount.cash_balance}
                        onChange={(e) => setEditedAccount({ ...editedAccount, cash_balance: formatCurrencyInput(e.target.value) })}
                        className="input-premium w-full pl-8"
                      />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleSaveAccount}
                      disabled={saving}
                      className="btn-premium px-4 py-2 text-sm disabled:opacity-50"
                    >
                      {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                    <button
                      onClick={() => {
                        setEditingAccount(false);
                        setEditedAccount({
                          name: account.account_name,
                          purpose: account.account_purpose,
                          cash_balance: Number(account.cash_balance).toLocaleString('en-US'),
                        });
                      }}
                      className="bg-[#252529] hover:bg-[#333] text-[#A3A3A3] px-4 py-2 rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <h2 className="font-display text-2xl font-bold text-[#FAFAFA]">{account.account_name}</h2>
                  <p className="text-[#6B6B6B] mt-1">{account.account_purpose}</p>
                </>
              )}
            </div>
            {!editingAccount && (
              <button
                onClick={() => setEditingAccount(true)}
                className="text-[#D4AF37] hover:bg-[rgba(212,175,55,0.1)] p-2 rounded transition-colors"
                title="Edit Account"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </button>
            )}
          </div>

          {message && (
            <div className={`mb-4 p-4 rounded-lg ${
              message.type === 'success'
                ? 'bg-green-500/10 border border-green-500/30 text-green-400'
                : 'bg-red-500/10 border border-red-500/30 text-red-400'
            }`}>
              {message.text}
            </div>
          )}

          {/* Account Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 card-highlight rounded-lg">
            <div>
              <p className="stat-label">Cash Balance</p>
              <p className="text-lg font-semibold text-[#FAFAFA]">
                ${Number(account.cash_balance).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div>
              <p className="stat-label">Positions Value</p>
              <p className="text-lg font-semibold text-[#FAFAFA]">
                ${calculatePositionsValue().toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div>
              <p className="stat-label">Total Value</p>
              <p className="text-lg font-semibold value-gold">
                ${calculateTotalValue().toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div>
              <p className="stat-label">Positions</p>
              <p className="text-lg font-semibold text-[#FAFAFA]">{positions.length}</p>
            </div>
          </div>
        </div>

        {/* Positions */}
        <div className="card-premium rounded-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-display text-xl font-bold text-[#FAFAFA]">Positions</h3>
            <button
              onClick={() => setShowAddPosition(true)}
              className="btn-premium px-4 py-2 text-sm flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Position
            </button>
          </div>

          {positions.length === 0 ? (
            <div className="text-center py-8 card-highlight rounded-lg p-6">
              <p className="text-[#A3A3A3]">No positions in this account yet</p>
              <p className="text-sm text-[#6B6B6B] mt-2">Click &ldquo;Add Position&rdquo; to start building your portfolio</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[rgba(255,255,255,0.06)]">
                    <th className="text-left py-3 px-4 font-semibold text-[#A3A3A3] text-sm">Symbol</th>
                    <th className="text-right py-3 px-4 font-semibold text-[#A3A3A3] text-sm">Quantity</th>
                    <th className="text-right py-3 px-4 font-semibold text-[#A3A3A3] text-sm">Price</th>
                    <th className="text-right py-3 px-4 font-semibold text-[#A3A3A3] text-sm">Value</th>
                    <th className="text-center py-3 px-4 font-semibold text-[#A3A3A3] text-sm">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((position) => (
                    <tr key={position.id} className="border-b border-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.03)] transition-colors">
                      <td className="py-4 px-4 font-medium text-[#FAFAFA]">{position.symbol}</td>
                      <td className="py-4 px-4 text-right text-[#A3A3A3]">
                        {editingPosition === position.id ? (
                          <input
                            type="number"
                            value={editedQuantity}
                            onChange={(e) => setEditedQuantity(e.target.value)}
                            className="input-premium w-24 text-right py-1 px-2"
                            step="0.01"
                            min="0"
                          />
                        ) : (
                          Number(position.quantity).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
                        )}
                      </td>
                      <td className="py-4 px-4 text-right text-[#A3A3A3]">
                        ${position.current_price?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || 'N/A'}
                      </td>
                      <td className="py-4 px-4 text-right font-semibold value-gold">
                        ${((position.current_price || 0) * Number(position.quantity)).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex justify-center gap-2">
                          {editingPosition === position.id ? (
                            <>
                              <button
                                onClick={() => handleUpdatePosition(position.id)}
                                disabled={saving}
                                className="text-green-400 hover:bg-green-500/20 p-2 rounded transition-colors disabled:opacity-50"
                                title="Save"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                              </button>
                              <button
                                onClick={() => {
                                  setEditingPosition(null);
                                  setEditedQuantity('');
                                }}
                                className="text-[#6B6B6B] hover:bg-[#252529] p-2 rounded transition-colors"
                                title="Cancel"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                onClick={() => {
                                  setEditingPosition(position.id);
                                  // Format quantity to remove unnecessary decimal places
                                  const qty = Number(position.quantity);
                                  setEditedQuantity(qty % 1 === 0 ? qty.toString() : qty.toFixed(2));
                                }}
                                className="text-[#D4AF37] hover:bg-[rgba(212,175,55,0.1)] p-2 rounded transition-colors"
                                title="Edit"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                </svg>
                              </button>
                              <button
                                onClick={() => setConfirmModal({
                                  isOpen: true,
                                  positionId: position.id,
                                  symbol: position.symbol
                                })}
                                disabled={saving}
                                className="text-red-400 hover:bg-red-500/20 p-2 rounded transition-colors disabled:opacity-50"
                                title="Delete"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Add Position Modal */}
        {showAddPosition && (
          <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
            <div className="card-premium max-w-md w-full p-6">
              <h3 className="text-xl font-bold text-[#FAFAFA] mb-4">Add New Position</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[#A3A3A3] mb-1">
                    Symbol *
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={searchTerm || newPosition.symbol}
                      onChange={(e) => {
                        const value = e.target.value.toUpperCase();
                        setSearchTerm(value);
                        setNewPosition({ ...newPosition, symbol: value });
                        setShowSymbolSuggestions(value.length > 0);
                      }}
                      onFocus={() => setShowSymbolSuggestions(searchTerm.length > 0)}
                      className="input-premium w-full uppercase"
                      placeholder="Enter ticker symbol (e.g., SPY, AAPL)"
                    />

                    {showSymbolSuggestions && filteredInstruments.length > 0 && (
                      <div className="absolute z-10 w-full mt-1 bg-[#1A1A1F] border border-[rgba(255,255,255,0.06)] rounded-lg shadow-lg max-h-48 overflow-y-auto">
                        {filteredInstruments.map((inst) => (
                          <button
                            key={inst.symbol}
                            onClick={() => {
                              setNewPosition({ ...newPosition, symbol: inst.symbol });
                              setSearchTerm('');
                              setShowSymbolSuggestions(false);
                            }}
                            className="w-full text-left px-3 py-2 hover:bg-[#252529] border-b border-[rgba(255,255,255,0.06)] last:border-b-0"
                          >
                            <div className="font-medium text-[#FAFAFA]">{inst.symbol}</div>
                            <div className="text-xs text-[#6B6B6B]">{inst.name}</div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-[#6B6B6B] mt-1">
                    If the symbol is not in our database, it will be added automatically
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#A3A3A3] mb-1">
                    Quantity *
                  </label>
                  <input
                    type="number"
                    value={newPosition.quantity}
                    onChange={(e) => setNewPosition({ ...newPosition, quantity: e.target.value })}
                    className="input-premium w-full"
                    placeholder="0"
                    step="0.01"
                    min="0"
                  />
                </div>
              </div>

              {message && message.type === 'error' && (
                <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                  {message.text}
                </div>
              )}

              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleAddPosition}
                  disabled={saving}
                  className="flex-1 btn-premium py-2 px-4 text-sm"
                >
                  {saving ? 'Adding...' : 'Add Position'}
                </button>
                <button
                  onClick={() => {
                    setShowAddPosition(false);
                    setNewPosition({ symbol: '', quantity: '' });
                    setSearchTerm('');
                    setShowSymbolSuggestions(false);
                    setMessage(null);
                  }}
                  className="flex-1 bg-[#252529] hover:bg-[#333] text-[#A3A3A3] px-4 py-2 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Delete Position Confirmation Modal */}
        <ConfirmModal
          isOpen={confirmModal.isOpen}
          title="Delete Position"
          message={
            <div>
              <p>Are you sure you want to delete your <span className="font-semibold text-[#FAFAFA]">{confirmModal.symbol}</span> position?</p>
              <p className="text-sm mt-2">This will remove this holding from your account.</p>
              <p className="text-sm mt-2 text-red-400 font-semibold">This action cannot be undone.</p>
            </div>
          }
          confirmText="Delete Position"
          cancelText="Cancel"
          confirmButtonClass="bg-red-600 hover:bg-red-700"
          onConfirm={() => {
            handleDeletePosition(confirmModal.positionId);
            setConfirmModal({ isOpen: false, positionId: '', symbol: '' });
          }}
          onCancel={() => setConfirmModal({ isOpen: false, positionId: '', symbol: '' })}
          isProcessing={saving}
        />
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
