import { useAuth } from "@clerk/nextjs";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/router";
import Layout from "../components/Layout";
import ConfirmModal from "../components/ConfirmModal";
import { API_URL } from "../lib/config";
import { SkeletonTable } from "../components/Skeleton";
import Head from "next/head";

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

export default function Accounts() {
  const { getToken } = useAuth();
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [populatingData, setPopulatingData] = useState(false);
  const [resettingAccounts, setResettingAccounts] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newAccount, setNewAccount] = useState({ name: '', purpose: '', cash_balance: '' });
  const [savingAccount, setSavingAccount] = useState(false);
  const [deletingAccountId, setDeletingAccountId] = useState<string | null>(null);
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    type: 'reset' | 'delete';
    accountId?: string;
    accountName?: string;
  }>({ isOpen: false, type: 'reset' });

  const loadAccounts = useCallback(async () => {
    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/accounts`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        // For each account, load positions
        const accountsWithPositions = await Promise.all(
          data.map(async (account: Account) => {
            // Skip if account has no ID
            if (!account.id) {
              return { ...account, positions: [] };
            }

            try {
              const positionsResponse = await fetch(
                `${API_URL}/api/accounts/${account.id}/positions`,
                {
                  headers: {
                    'Authorization': `Bearer ${token}`,
                  },
                }
              );
              if (positionsResponse.ok) {
                const data = await positionsResponse.json();
                const positions = data.positions || [];
                return { ...account, positions };
              }
            } catch (err) {
              console.error(`Error loading positions for account ${account.id}:`, err);
            }
            return { ...account, positions: [] };
          })
        );
        setAccounts(accountsWithPositions);
      }
    } catch (error) {
      console.error('Error loading accounts:', error);
      setMessage({ type: 'error', text: 'Failed to load accounts' });
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    loadAccounts();
  }, [loadAccounts]);

  // Listen for analysis completion events to refresh data
  useEffect(() => {
    const handleAnalysisCompleted = () => {
      // Refresh accounts to get updated prices after analysis
      loadAccounts();
    };

    // Listen for the completion event
    window.addEventListener('analysis:completed', handleAnalysisCompleted);

    return () => {
      window.removeEventListener('analysis:completed', handleAnalysisCompleted);
    };
  }, [loadAccounts]);

  const populateTestData = async () => {
    setPopulatingData(true);
    setMessage(null);

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/populate-test-data`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMessage({ type: 'success', text: data.message });
        await loadAccounts(); // Reload accounts after population
      } else {
        setMessage({ type: 'error', text: 'Failed to populate test data' });
      }
    } catch (error) {
      console.error('Error populating test data:', error);
      setMessage({ type: 'error', text: 'Error populating test data' });
    } finally {
      setPopulatingData(false);
    }
  };

  const resetAccounts = async () => {
    setResettingAccounts(true);
    setMessage(null);

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/reset-accounts`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMessage({ type: 'success', text: data.message });
        // Clear accounts immediately after successful reset
        setAccounts([]);
        // Then reload to confirm empty state
        await loadAccounts();
      } else {
        setMessage({ type: 'error', text: 'Failed to reset accounts' });
      }
    } catch (error) {
      console.error('Error resetting accounts:', error);
      setMessage({ type: 'error', text: 'Error resetting accounts' });
    } finally {
      setResettingAccounts(false);
    }
  };

  const calculateAccountTotal = (account: Account) => {
    const positionsValue = account.positions?.reduce((sum, position) => {
      const value = Number(position.quantity) * (Number(position.current_price) || 0);
      return sum + value;
    }, 0) || 0;
    return Number(account.cash_balance) + positionsValue;
  };

  const calculatePortfolioTotal = () => {
    return accounts.reduce((sum, account) => sum + calculateAccountTotal(account), 0);
  };

  const handleAddAccount = async () => {
    if (!newAccount.name.trim()) {
      setMessage({ type: 'error', text: 'Please enter an account name' });
      return;
    }

    setSavingAccount(true);
    setMessage(null);

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/accounts`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          account_name: newAccount.name,
          account_purpose: newAccount.purpose || 'Investment Account',
          cash_balance: parseFloat(newAccount.cash_balance.replace(/,/g, '')) || 0,
        }),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Account created successfully' });
        setShowAddModal(false);
        setNewAccount({ name: '', purpose: '', cash_balance: '' });
        await loadAccounts();
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Failed to create account' });
      }
    } catch (error) {
      console.error('Error creating account:', error);
      setMessage({ type: 'error', text: 'Error creating account' });
    } finally {
      setSavingAccount(false);
    }
  };

  const handleDeleteAccount = async (accountId: string) => {
    setDeletingAccountId(accountId);
    setMessage(null);

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/accounts/${accountId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Account deleted successfully' });
        await loadAccounts();
      } else {
        setMessage({ type: 'error', text: 'Failed to delete account' });
      }
    } catch (error) {
      console.error('Error deleting account:', error);
      setMessage({ type: 'error', text: 'Error deleting account' });
    } finally {
      setDeletingAccountId(null);
    }
  };

  const formatCurrencyInput = (value: string) => {
    // Remove non-numeric characters except decimal
    const cleaned = value.replace(/[^0-9.]/g, '');
    // Format with commas
    const parts = cleaned.split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return parts.join('.');
  };

  return (
    <>
      <Head>
        <title>Accounts - Alex AI Financial Advisor</title>
      </Head>
      <Layout>
      <div className="dashboard-premium-wrapper">
        <div className="dashboard-premium">
          <div className="dashboard-content max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card-premium rounded-xl p-6 mb-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="font-display text-2xl font-bold text-[#FAFAFA]">Investment Accounts</h2>
              <p className="text-sm text-[#6B6B6B] mt-1">Manage your investment accounts and portfolios</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowAddModal(true)}
                className="btn-premium px-4 py-2 flex items-center gap-2 text-sm"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Account
              </button>
              {accounts.length === 0 && !loading && (
                <button
                  onClick={populateTestData}
                  disabled={populatingData}
                  className="btn-secondary px-4 py-2 text-sm disabled:opacity-50"
                >
                  {populatingData ? 'Populating...' : 'Populate Test Data'}
                </button>
              )}
              {accounts.length > 0 && (
                <button
                  onClick={() => setConfirmModal({ isOpen: true, type: 'reset' })}
                  disabled={resettingAccounts}
                  className="bg-[#252529] hover:bg-[#333] text-[#A3A3A3] px-4 py-2 rounded-lg transition-colors disabled:opacity-50 text-sm"
                >
                  {resettingAccounts ? 'Resetting...' : 'Reset All'}
                </button>
              )}
            </div>
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

          {loading ? (
            <SkeletonTable rows={3} />
          ) : accounts.length === 0 ? (
            <div className="bg-[#3B82F6]/10 border border-[#3B82F6]/30 rounded-lg p-6 text-center">
              <p className="text-[#3B82F6] font-semibold mb-2">
                No accounts found
              </p>
              <p className="text-sm text-[#6B6B6B]">
                Click the &quot;Populate Test Data&quot; button above to create sample accounts with positions
              </p>
            </div>
          ) : (
            <>
              {/* Portfolio Summary */}
              <div className="card-premium card-highlight rounded-lg p-4 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <p className="stat-label">Total Portfolio Value</p>
                    <p className="text-2xl font-bold value-gold">
                      ${calculatePortfolioTotal().toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div>
                    <p className="stat-label">Number of Accounts</p>
                    <p className="text-2xl font-bold text-[#FAFAFA]">{accounts.length}</p>
                  </div>
                  <div>
                    <p className="stat-label">Total Positions</p>
                    <p className="text-2xl font-bold text-[#FAFAFA]">
                      {accounts.reduce((sum, acc) => sum + (acc.positions?.length || 0), 0)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Accounts Table */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-[rgba(255,255,255,0.06)]">
                      <th scope="col" className="text-left py-3 px-4 font-semibold text-[#A3A3A3] text-sm">Account Name</th>
                      <th scope="col" className="text-left py-3 px-4 font-semibold text-[#A3A3A3] text-sm hidden md:table-cell">Type</th>
                      <th scope="col" className="text-right py-3 px-4 font-semibold text-[#A3A3A3] text-sm">Positions</th>
                      <th scope="col" className="text-right py-3 px-4 font-semibold text-[#A3A3A3] text-sm">Cash</th>
                      <th scope="col" className="text-right py-3 px-4 font-semibold text-[#A3A3A3] text-sm">Total Value</th>
                      <th scope="col" className="text-center py-3 px-4 font-semibold text-[#A3A3A3] text-sm">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accounts.map((account) => {
                      const positionsValue = calculateAccountTotal(account) - Number(account.cash_balance);
                      return (
                        <tr key={account.id} className="border-b border-[rgba(255,255,255,0.06)] hover:bg-[rgba(255,255,255,0.03)] transition-colors">
                          <td className="py-4 px-4">
                            <div>
                              <p className="font-semibold text-[#FAFAFA]">{account.account_name}</p>
                              <p className="text-xs text-[#6B6B6B] md:hidden">{account.account_purpose}</p>
                            </div>
                          </td>
                          <td className="py-4 px-4 hidden md:table-cell">
                            <span className="text-sm text-[#A3A3A3]">{account.account_purpose}</span>
                          </td>
                          <td className="py-4 px-4 text-right">
                            <div>
                              <p className="font-medium text-[#FAFAFA]">{account.positions?.length || 0}</p>
                              {positionsValue > 0 && (
                                <p className="text-xs text-[#6B6B6B]">
                                  ${positionsValue.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                                </p>
                              )}
                            </div>
                          </td>
                          <td className="py-4 px-4 text-right text-[#A3A3A3]">
                            ${Number(account.cash_balance).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </td>
                          <td className="py-4 px-4 text-right">
                            <p className="font-semibold value-gold">
                              ${calculateAccountTotal(account).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </p>
                          </td>
                          <td className="py-4 px-4">
                            <div className="flex justify-center gap-2">
                              <button
                                onClick={() => router.push(`/accounts/${account.id}`)}
                                className="text-[#D4AF37] hover:bg-[rgba(212,175,55,0.1)] p-2 rounded transition-colors"
                                title="View/Edit"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                </svg>
                              </button>
                              <button
                                onClick={() => setConfirmModal({
                                  isOpen: true,
                                  type: 'delete',
                                  accountId: account.id,
                                  accountName: account.account_name
                                })}
                                disabled={deletingAccountId === account.id}
                                className="text-red-400 hover:bg-red-500/20 p-2 rounded transition-colors disabled:opacity-50"
                                title="Delete"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>

        {/* Add Account Modal */}
        {showAddModal && (
          <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
            <div className="card-premium max-w-md w-full p-6">
              <h3 className="text-xl font-bold text-[#FAFAFA] mb-4">Add New Account</h3>

              <div className="space-y-4">
                <div>
                  <label htmlFor="new-account-name" className="block text-sm font-medium text-[#A3A3A3] mb-1">
                    Account Name *
                  </label>
                  <input
                    id="new-account-name"
                    type="text"
                    value={newAccount.name}
                    onChange={(e) => setNewAccount({ ...newAccount, name: e.target.value })}
                    className="input-premium w-full"
                    placeholder="e.g., 401k, Roth IRA, Brokerage"
                  />
                </div>

                <div>
                  <label htmlFor="new-account-purpose" className="block text-sm font-medium text-[#A3A3A3] mb-1">
                    Account Purpose
                  </label>
                  <input
                    id="new-account-purpose"
                    type="text"
                    value={newAccount.purpose}
                    onChange={(e) => setNewAccount({ ...newAccount, purpose: e.target.value })}
                    className="input-premium w-full"
                    placeholder="e.g., Long-term Growth, Retirement"
                  />
                </div>

                <div>
                  <label htmlFor="new-account-cash" className="block text-sm font-medium text-[#A3A3A3] mb-1">
                    Initial Cash Balance
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 transform -translate-y-1/2 text-[#6B6B6B]">$</span>
                    <input
                      id="new-account-cash"
                      type="text"
                      value={newAccount.cash_balance}
                      onChange={(e) => setNewAccount({ ...newAccount, cash_balance: formatCurrencyInput(e.target.value) })}
                      className="input-premium w-full pl-8"
                      placeholder="0.00"
                    />
                  </div>
                </div>
              </div>

              {message && message.type === 'error' && (
                <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                  {message.text}
                </div>
              )}

              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleAddAccount}
                  disabled={savingAccount}
                  className="flex-1 btn-premium py-2 px-4 text-sm"
                >
                  {savingAccount ? 'Creating...' : 'Create Account'}
                </button>
                <button
                  onClick={() => {
                    setShowAddModal(false);
                    setNewAccount({ name: '', purpose: '', cash_balance: '' });
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

        {/* Confirmation Modal */}
        <ConfirmModal
          isOpen={confirmModal.isOpen}
          title={confirmModal.type === 'reset' ? 'Reset All Accounts' : 'Delete Account'}
          message={
            confirmModal.type === 'reset' ? (
              <div>
                <p className="font-semibold mb-2 text-[#FAFAFA]">Are you sure you want to delete all your accounts?</p>
                <p className="text-sm">This will permanently remove:</p>
                <ul className="list-disc list-inside text-sm mt-1 ml-2">
                  <li>All {accounts.length} account{accounts.length !== 1 ? 's' : ''}</li>
                  <li>All positions in those accounts</li>
                  <li>All transaction history</li>
                </ul>
                <p className="text-sm mt-3 text-red-400 font-semibold">This action cannot be undone.</p>
              </div>
            ) : (
              <div>
                <p>Are you sure you want to delete <span className="font-semibold text-[#FAFAFA]">&ldquo;{confirmModal.accountName}&rdquo;</span>?</p>
                <p className="text-sm mt-2">This will also delete all positions in this account.</p>
                <p className="text-sm mt-2 text-red-400 font-semibold">This action cannot be undone.</p>
              </div>
            )
          }
          confirmText={confirmModal.type === 'reset' ? 'Delete All Accounts' : 'Delete Account'}
          cancelText="Cancel"
          confirmButtonClass="bg-red-600 hover:bg-red-700"
          onConfirm={() => {
            if (confirmModal.type === 'reset') {
              resetAccounts();
            } else if (confirmModal.accountId) {
              handleDeleteAccount(confirmModal.accountId);
            }
            setConfirmModal({ isOpen: false, type: 'reset' });
          }}
          onCancel={() => setConfirmModal({ isOpen: false, type: 'reset' })}
          isProcessing={resettingAccounts || deletingAccountId !== null}
        />
          </div>
        </div>
      </div>
      </Layout>
    </>
  );
}
