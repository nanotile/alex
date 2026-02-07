import { useUser, useAuth } from "@clerk/nextjs";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/router";
import { getApiUrl } from "../lib/config";
import Layout from "../components/Layout";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { Skeleton } from "../components/Skeleton";
import { showToast } from "../components/Toast";
import Head from "next/head";

interface UserData {
  clerk_user_id: string;
  display_name: string;
  years_until_retirement: number;
  target_retirement_income: number;
  asset_class_targets: Record<string, number>;
  region_targets: Record<string, number>;
}

interface Account {
  account_id: string;
  clerk_user_id: string;
  account_name: string;
  account_type: string;
  account_purpose: string;
  cash_balance: number;
  created_at: string;
  updated_at: string;
}

interface Position {
  position_id: string;
  account_id: string;
  symbol: string;
  quantity: number;
  created_at: string;
  updated_at: string;
}

interface Instrument {
  symbol: string;
  name: string;
  instrument_type: string;
  current_price?: number;
  asset_class_allocation?: Record<string, number>;
  region_allocation?: Record<string, number>;
  sector_allocation?: Record<string, number>;
}

// Custom styles for the premium dark theme
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');

  /* Override Layout's light background */
  .dashboard-premium-wrapper {
    background: #0D0D0F !important;
    min-height: 100vh;
    margin: -2rem -1rem -1.5rem -1rem;
    padding: 2rem 1rem 1.5rem 1rem;
  }

  @media (min-width: 640px) {
    .dashboard-premium-wrapper {
      margin: -2rem -1.5rem -1.5rem -1.5rem;
      padding: 2rem 1.5rem 1.5rem 1.5rem;
    }
  }

  @media (min-width: 1024px) {
    .dashboard-premium-wrapper {
      margin: -2rem -2rem -1.5rem -2rem;
      padding: 2rem 2rem 1.5rem 2rem;
    }
  }

  .dashboard-premium {
    --gold: #D4AF37;
    --gold-light: #E8D48A;
    --gold-dark: #A68B2A;
    --charcoal: #0D0D0F;
    --charcoal-light: #1A1A1F;
    --charcoal-lighter: #252529;
    --blue-accent: #3B82F6;
    --blue-glow: rgba(59, 130, 246, 0.15);
    --text-primary: #FAFAFA;
    --text-secondary: #A3A3A3;
    --text-muted: #6B6B6B;
    --border-subtle: rgba(212, 175, 55, 0.15);
    --border-card: rgba(255, 255, 255, 0.06);

    font-family: 'DM Sans', system-ui, sans-serif;
    background: var(--charcoal);
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
  }

  .dashboard-premium::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background:
      radial-gradient(ellipse 80% 50% at 50% -20%, rgba(212, 175, 55, 0.08), transparent),
      radial-gradient(ellipse 60% 40% at 100% 0%, rgba(59, 130, 246, 0.05), transparent);
    pointer-events: none;
    z-index: 0;
  }

  .dashboard-premium::after {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
    opacity: 0.03;
    pointer-events: none;
    z-index: 0;
  }

  .dashboard-content {
    position: relative;
    z-index: 1;
  }

  .font-display {
    font-family: 'Playfair Display', Georgia, serif;
  }

  .card-premium {
    background: linear-gradient(135deg, var(--charcoal-light) 0%, rgba(26, 26, 31, 0.8) 100%);
    border: 1px solid var(--border-card);
    border-radius: 16px;
    backdrop-filter: blur(10px);
    position: relative;
    overflow: hidden;
  }

  .card-premium::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-subtle), transparent);
  }

  .card-highlight {
    background: linear-gradient(135deg, rgba(212, 175, 55, 0.08) 0%, var(--charcoal-light) 50%);
    border: 1px solid var(--border-subtle);
  }

  .card-highlight::after {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: conic-gradient(from 0deg, transparent, rgba(212, 175, 55, 0.03), transparent 30%);
    animation: rotate-glow 20s linear infinite;
    pointer-events: none;
  }

  @keyframes rotate-glow {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .value-gold {
    background: linear-gradient(135deg, var(--gold-light) 0%, var(--gold) 50%, var(--gold-dark) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .geometric-pattern {
    position: absolute;
    top: 0;
    right: 0;
    width: 120px;
    height: 120px;
    opacity: 0.05;
    background:
      linear-gradient(45deg, var(--gold) 25%, transparent 25%),
      linear-gradient(-45deg, var(--gold) 25%, transparent 25%),
      linear-gradient(45deg, transparent 75%, var(--gold) 75%),
      linear-gradient(-45deg, transparent 75%, var(--gold) 75%);
    background-size: 20px 20px;
    background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
  }

  .stat-label {
    color: var(--text-muted);
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }

  .divider-gold {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
    opacity: 0.3;
  }

  .input-premium {
    background: var(--charcoal-lighter);
    border: 1px solid var(--border-card);
    color: var(--text-primary);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.95rem;
    transition: all 0.2s ease;
  }

  .input-premium:focus {
    outline: none;
    border-color: var(--gold);
    box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1);
  }

  .input-premium::placeholder {
    color: var(--text-muted);
  }

  .slider-premium {
    -webkit-appearance: none;
    appearance: none;
    width: 100%;
    height: 6px;
    background: var(--charcoal-lighter);
    border-radius: 3px;
    outline: none;
  }

  .slider-premium::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    background: linear-gradient(135deg, var(--gold-light), var(--gold));
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(212, 175, 55, 0.4);
    transition: transform 0.2s ease;
  }

  .slider-premium::-webkit-slider-thumb:hover {
    transform: scale(1.1);
  }

  .slider-premium::-moz-range-thumb {
    width: 20px;
    height: 20px;
    background: linear-gradient(135deg, var(--gold-light), var(--gold));
    border-radius: 50%;
    cursor: pointer;
    border: none;
    box-shadow: 0 2px 8px rgba(212, 175, 55, 0.4);
  }

  .btn-premium {
    background: linear-gradient(135deg, var(--gold) 0%, var(--gold-dark) 100%);
    color: var(--charcoal);
    font-weight: 600;
    padding: 12px 32px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
  }

  .btn-premium::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s ease;
  }

  .btn-premium:hover::before {
    left: 100%;
  }

  .btn-premium:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(212, 175, 55, 0.3);
  }

  .btn-premium:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  .btn-secondary {
    background: transparent;
    border: 1px solid var(--gold);
    color: var(--gold);
    font-weight: 600;
    padding: 12px 32px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .btn-secondary:hover {
    background: rgba(212, 175, 55, 0.1);
  }

  .ring-chart-container {
    position: relative;
  }

  .ring-chart-center {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
  }

  .allocation-bar {
    height: 8px;
    background: var(--charcoal-lighter);
    border-radius: 4px;
    overflow: hidden;
    position: relative;
  }

  .allocation-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
  }

  .fade-in {
    animation: fadeIn 0.6s ease-out forwards;
    opacity: 0;
  }

  .fade-in-delay-1 { animation-delay: 0.1s; }
  .fade-in-delay-2 { animation-delay: 0.2s; }
  .fade-in-delay-3 { animation-delay: 0.3s; }
  .fade-in-delay-4 { animation-delay: 0.4s; }
  .fade-in-delay-5 { animation-delay: 0.5s; }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .number-ticker {
    display: inline-block;
    transition: all 0.3s ease;
  }
`;

const CHART_COLORS = ['#D4AF37', '#3B82F6', '#10B981', '#8B5CF6', '#F59E0B'];

export default function Dashboard() {
  const router = useRouter();
  const { user, isLoaded: userLoaded } = useUser();
  const { getToken } = useAuth();
  const [userData, setUserData] = useState<UserData | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [positions, setPositions] = useState<Record<string, Position[]>>({});
  const [instruments, setInstruments] = useState<Record<string, Instrument>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastAnalysisDate, setLastAnalysisDate] = useState<string | null>(null);

  // Form state for editable fields
  const [displayName, setDisplayName] = useState("");
  const [yearsUntilRetirement, setYearsUntilRetirement] = useState(0);
  const [targetRetirementIncome, setTargetRetirementIncome] = useState(0);
  const [equityTarget, setEquityTarget] = useState(0);
  const [fixedIncomeTarget, setFixedIncomeTarget] = useState(0);
  const [northAmericaTarget, setNorthAmericaTarget] = useState(0);
  const [internationalTarget, setInternationalTarget] = useState(0);

  // Calculate portfolio summary
  const calculatePortfolioSummary = useCallback(() => {
    let totalValue = 0;
    const assetClassBreakdown: Record<string, number> = {
      equity: 0,
      fixed_income: 0,
      alternatives: 0,
      cash: 0
    };

    accounts.forEach(account => {
      const cashBalance = Number(account.cash_balance);
      totalValue += cashBalance;
      assetClassBreakdown.cash += cashBalance;
    });

    Object.entries(positions).forEach(([, accountPositions]) => {
      accountPositions.forEach(position => {
        const instrument = instruments[position.symbol];
        if (instrument?.current_price) {
          const positionValue = Number(position.quantity) * Number(instrument.current_price);
          totalValue += positionValue;

          if (instrument.asset_class_allocation) {
            Object.entries(instrument.asset_class_allocation).forEach(([assetClass, percentage]) => {
              assetClassBreakdown[assetClass] = (assetClassBreakdown[assetClass] || 0) + (positionValue * percentage / 100);
            });
          }
        }
      });
    });

    return { totalValue, assetClassBreakdown };
  }, [accounts, positions, instruments]);

  // Load user data and accounts
  useEffect(() => {
    async function loadData() {
      if (!userLoaded || !user) return;

      try {
        const token = await getToken();
        if (!token) {
          setError("Not authenticated");
          setLoading(false);
          return;
        }

        const apiUrl = getApiUrl();
        console.log('Dashboard: Fetching from API URL:', apiUrl);
        const userResponse = await fetch(`${apiUrl}/api/user`, {
          headers: { "Authorization": `Bearer ${token}` },
        });

        if (!userResponse.ok) {
          throw new Error(`Failed to sync user: ${userResponse.status}`);
        }

        const response = await userResponse.json();
        const userData = response.user;
        setUserData(userData);
        setDisplayName(userData.display_name || "");
        setYearsUntilRetirement(userData.years_until_retirement || 0);
        const income = userData.target_retirement_income
          ? (typeof userData.target_retirement_income === 'string'
            ? parseFloat(userData.target_retirement_income)
            : userData.target_retirement_income)
          : 0;
        setTargetRetirementIncome(income);
        setEquityTarget(userData.asset_class_targets?.equity || 0);
        setFixedIncomeTarget(userData.asset_class_targets?.fixed_income || 0);
        setNorthAmericaTarget(userData.region_targets?.north_america || 0);
        setInternationalTarget(userData.region_targets?.international || 0);

        const accountsResponse = await fetch(`${getApiUrl()}/api/accounts`, {
          headers: { "Authorization": `Bearer ${token}` },
        });

        if (accountsResponse.ok) {
          const accountsData = await accountsResponse.json();
          setAccounts(accountsData);

          const positionsMap: Record<string, Position[]> = {};
          const instrumentsMap: Record<string, Instrument> = {};

          for (const account of accountsData) {
            if (!account.id) continue;

            const positionsResponse = await fetch(`${getApiUrl()}/api/accounts/${account.id}/positions`, {
              headers: { "Authorization": `Bearer ${token}` },
            });

            if (positionsResponse.ok) {
              const positionsData = await positionsResponse.json();
              positionsMap[account.id] = positionsData.positions || [];

              for (const position of positionsData.positions || []) {
                if (position.instrument) {
                  instrumentsMap[position.symbol] = position.instrument as Instrument;
                }
              }
            }
          }

          setPositions(positionsMap);
          setInstruments(instrumentsMap);
        }

        try {
          const jobsResponse = await fetch(`${getApiUrl()}/api/jobs`, {
            headers: { "Authorization": `Bearer ${token}` },
          });
          if (jobsResponse.ok) {
            const jobsData = await jobsResponse.json();
            const completedJobs = (jobsData.jobs || [])
              .filter((j: { status: string }) => j.status === 'completed')
              .sort((a: { created_at: string }, b: { created_at: string }) =>
                new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
              );
            if (completedJobs.length > 0) {
              setLastAnalysisDate(completedJobs[0].created_at);
            }
          }
        } catch (jobsErr) {
          console.error("Error fetching jobs:", jobsErr);
        }

      } catch (err) {
        console.error("Error loading data:", err);
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [userLoaded, user, getToken]);

  // Listen for analysis completion events
  useEffect(() => {
    if (!userLoaded || !user) return;

    const handleAnalysisCompleted = async () => {
      try {
        const token = await getToken();
        if (!token) return;

        const accountsResponse = await fetch(`${getApiUrl()}/api/accounts`, {
          headers: { "Authorization": `Bearer ${token}` },
        });

        if (accountsResponse.ok) {
          const accountsData = await accountsResponse.json();
          setAccounts(accountsData.accounts || []);

          const positionsData: Record<string, Position[]> = {};
          const instrumentsData: Record<string, Instrument> = {};

          for (const account of accountsData.accounts || []) {
            const positionsResponse = await fetch(
              `${getApiUrl()}/api/accounts/${account.id}/positions`,
              { headers: { "Authorization": `Bearer ${token}` } }
            );

            if (positionsResponse.ok) {
              const data = await positionsResponse.json();
              positionsData[account.id] = data.positions || [];

              for (const position of data.positions || []) {
                if (position.instrument) {
                  instrumentsData[position.symbol] = position.instrument;
                }
              }
            }
          }

          setPositions(positionsData);
          setInstruments(instrumentsData);
        }
      } catch (err) {
        console.error("Error refreshing dashboard data:", err);
      }
    };

    window.addEventListener('analysis:completed', handleAnalysisCompleted);
    return () => window.removeEventListener('analysis:completed', handleAnalysisCompleted);
  }, [userLoaded, user, getToken, calculatePortfolioSummary]);

  // Save user settings
  const handleSaveSettings = async () => {
    if (!userData) return;

    if (!displayName || displayName.trim().length === 0) {
      showToast('error', 'Display name is required');
      return;
    }

    if (yearsUntilRetirement < 0 || yearsUntilRetirement > 50) {
      showToast('error', 'Years until retirement must be between 0 and 50');
      return;
    }

    if (targetRetirementIncome < 0) {
      showToast('error', 'Target retirement income must be positive');
      return;
    }

    const equityFixed = equityTarget + fixedIncomeTarget;
    if (Math.abs(equityFixed - 100) > 0.01) {
      showToast('error', 'Equity and Fixed Income must sum to 100%');
      return;
    }

    const regionTotal = northAmericaTarget + internationalTarget;
    if (Math.abs(regionTotal - 100) > 0.01) {
      showToast('error', 'North America and International must sum to 100%');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      const updateData = {
        display_name: displayName.trim(),
        years_until_retirement: yearsUntilRetirement,
        target_retirement_income: targetRetirementIncome,
        asset_class_targets: {
          equity: equityTarget,
          fixed_income: fixedIncomeTarget
        },
        region_targets: {
          north_america: northAmericaTarget,
          international: internationalTarget
        }
      };

      const response = await fetch(`${getApiUrl()}/api/user`, {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        throw new Error(`Failed to save settings: ${response.status}`);
      }

      const updatedUser = await response.json();
      setUserData(updatedUser);
      showToast('success', 'Settings saved successfully!');

    } catch (err) {
      console.error("Error saving settings:", err);
      showToast('error', err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const { totalValue, assetClassBreakdown } = calculatePortfolioSummary();

  const pieChartData = Object.entries(assetClassBreakdown)
    .filter(([, value]) => value > 0)
    .map(([key, value]) => ({
      name: key.charAt(0).toUpperCase() + key.slice(1).replace('_', ' '),
      value: Math.round(value),
      percentage: totalValue > 0 ? Math.round(value / totalValue * 100) : 0
    }));

  // Get total positions count
  const totalPositions = Object.values(positions).reduce((sum, p) => sum + p.length, 0);

  return (
    <>
      <Head>
        <title>Dashboard - Alex AI Financial Advisor</title>
      </Head>
      <style dangerouslySetInnerHTML={{ __html: styles }} />
      <Layout>
        <div className="dashboard-premium-wrapper">
          <div className="dashboard-premium">
            <div className="dashboard-content max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">

            {/* Header */}
            <div className="fade-in mb-12">
              <p className="stat-label mb-2">Welcome back</p>
              <h1 className="font-display text-4xl md:text-5xl font-semibold text-[#FAFAFA] mb-2">
                {displayName || user?.firstName || 'Investor'}
              </h1>
              <p className="text-[#6B6B6B]">
                {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
            </div>

            {loading ? (
              <div className="space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="card-premium p-8">
                      <Skeleton className="h-4 w-24 mb-4 bg-[#252529]" />
                      <Skeleton className="h-12 w-48 bg-[#252529]" />
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {/* Portfolio Value Hero Card */}
                <div className="card-premium card-highlight p-8 md:p-12 mb-8 fade-in fade-in-delay-1">
                  <div className="geometric-pattern" />
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
                    <div>
                      <p className="stat-label mb-3">Total Portfolio Value</p>
                      <h2 className="font-display text-5xl md:text-6xl lg:text-7xl font-semibold value-gold mb-4">
                        ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                      </h2>
                      <div className="flex items-center gap-6 text-sm">
                        <div>
                          <span className="text-[#6B6B6B]">Accounts: </span>
                          <span className="text-[#FAFAFA] font-semibold">{accounts.length}</span>
                        </div>
                        <div className="w-px h-4 bg-[#333]" />
                        <div>
                          <span className="text-[#6B6B6B]">Positions: </span>
                          <span className="text-[#FAFAFA] font-semibold">{totalPositions}</span>
                        </div>
                        <div className="w-px h-4 bg-[#333]" />
                        <div>
                          <span className="text-[#6B6B6B]">Cash: </span>
                          <span className="text-[#10B981] font-semibold">
                            ${assetClassBreakdown.cash?.toLocaleString('en-US', { minimumFractionDigits: 0 }) || '0'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Asset Allocation Ring */}
                    <div className="ring-chart-container h-48 md:h-64">
                      {pieChartData.length > 0 ? (
                        <>
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={pieChartData}
                                cx="50%"
                                cy="50%"
                                innerRadius="60%"
                                outerRadius="90%"
                                paddingAngle={2}
                                dataKey="value"
                                stroke="none"
                              >
                                {pieChartData.map((_, index) => (
                                  <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                                ))}
                              </Pie>
                              <Tooltip
                                formatter={(value: number) => `$${value.toLocaleString()}`}
                                contentStyle={{
                                  background: '#1A1A1F',
                                  border: '1px solid rgba(212, 175, 55, 0.2)',
                                  borderRadius: '8px',
                                  color: '#FAFAFA'
                                }}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                          <div className="ring-chart-center">
                            <p className="stat-label text-xs">Allocation</p>
                            <p className="font-display text-2xl text-[#FAFAFA]">
                              {pieChartData.length}
                            </p>
                            <p className="text-[#6B6B6B] text-xs">classes</p>
                          </div>
                        </>
                      ) : (
                        <div className="flex items-center justify-center h-full">
                          <p className="text-[#6B6B6B]">No positions yet</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Quick Stats Row */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                  {/* Retirement Timeline */}
                  <div className="card-premium p-6 fade-in fade-in-delay-2">
                    <p className="stat-label mb-2">Years to Retirement</p>
                    <div className="flex items-end gap-2">
                      <span className="font-display text-4xl text-[#3B82F6]">{yearsUntilRetirement}</span>
                      <span className="text-[#6B6B6B] mb-1">years</span>
                    </div>
                    <div className="mt-4 allocation-bar">
                      <div
                        className="allocation-fill bg-gradient-to-r from-[#3B82F6] to-[#8B5CF6]"
                        style={{ width: `${Math.max(5, 100 - (yearsUntilRetirement * 2))}%` }}
                      />
                    </div>
                    <p className="text-xs text-[#6B6B6B] mt-2">
                      Target: ${targetRetirementIncome.toLocaleString()}/year
                    </p>
                  </div>

                  {/* Last Analysis */}
                  <div className="card-premium p-6 fade-in fade-in-delay-3">
                    <p className="stat-label mb-2">Last Analysis</p>
                    {lastAnalysisDate ? (
                      <>
                        <button
                          onClick={() => router.push('/analysis')}
                          className="font-display text-2xl text-[#FAFAFA] hover:text-[#D4AF37] transition-colors text-left"
                        >
                          {new Date(lastAnalysisDate).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric'
                          })}
                        </button>
                        <p className="text-xs text-[#6B6B6B] mt-2">
                          {Math.floor((Date.now() - new Date(lastAnalysisDate).getTime()) / (1000 * 60 * 60 * 24))} days ago
                        </p>
                      </>
                    ) : (
                      <button
                        onClick={() => router.push('/advisor-team')}
                        className="btn-secondary text-sm mt-2"
                      >
                        Run First Analysis
                      </button>
                    )}
                  </div>

                  {/* Asset Breakdown Legend */}
                  <div className="card-premium p-6 fade-in fade-in-delay-4">
                    <p className="stat-label mb-3">Asset Classes</p>
                    <div className="space-y-2">
                      {pieChartData.map((item, index) => (
                        <div key={item.name} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }}
                            />
                            <span className="text-sm text-[#A3A3A3]">{item.name}</span>
                          </div>
                          <span className="text-sm text-[#FAFAFA] font-medium">{item.percentage}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Divider */}
                <div className="divider-gold my-12" />

                {/* Settings Section */}
                <div className="fade-in fade-in-delay-5">
                  <div className="flex items-center justify-between mb-8">
                    <div>
                      <h2 className="font-display text-2xl text-[#FAFAFA] mb-1">Investment Profile</h2>
                      <p className="text-[#6B6B6B] text-sm">Configure your retirement goals and target allocations</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Personal Info */}
                    <div className="card-premium p-6">
                      <h3 className="stat-label mb-6">Personal Details</h3>

                      <div className="space-y-5">
                        <div>
                          <label className="block text-sm text-[#A3A3A3] mb-2">Display Name</label>
                          <input
                            type="text"
                            value={displayName}
                            onChange={(e) => setDisplayName(e.target.value)}
                            className="input-premium w-full"
                            placeholder="Your name"
                          />
                        </div>

                        <div>
                          <label className="block text-sm text-[#A3A3A3] mb-2">Target Retirement Income</label>
                          <div className="relative">
                            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#6B6B6B]">$</span>
                            <input
                              type="text"
                              value={targetRetirementIncome ? targetRetirementIncome.toLocaleString('en-US') : ''}
                              onChange={(e) => {
                                const value = e.target.value.replace(/,/g, '');
                                const num = parseInt(value) || 0;
                                if (!isNaN(num)) setTargetRetirementIncome(num);
                              }}
                              className="input-premium w-full pl-8"
                              placeholder="80,000"
                            />
                            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[#6B6B6B] text-sm">/year</span>
                          </div>
                        </div>

                        <div>
                          <div className="flex justify-between mb-2">
                            <label className="text-sm text-[#A3A3A3]">Years Until Retirement</label>
                            <span className="text-sm font-semibold text-[#D4AF37]">{yearsUntilRetirement}</span>
                          </div>
                          <input
                            type="range"
                            min="0"
                            max="50"
                            value={yearsUntilRetirement}
                            onChange={(e) => setYearsUntilRetirement(Number(e.target.value))}
                            className="slider-premium"
                          />
                          <div className="flex justify-between text-xs text-[#6B6B6B] mt-1">
                            <span>Now</span>
                            <span>25 yrs</span>
                            <span>50 yrs</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Target Allocations */}
                    <div className="space-y-6">
                      {/* Asset Class Targets */}
                      <div className="card-premium p-6">
                        <h3 className="stat-label mb-6">Asset Class Targets</h3>

                        <div className="space-y-4">
                          <div>
                            <div className="flex justify-between mb-2">
                              <span className="text-sm text-[#A3A3A3]">Equity</span>
                              <span className="text-sm font-semibold text-[#D4AF37]">{equityTarget}%</span>
                            </div>
                            <input
                              type="range"
                              min="0"
                              max="100"
                              value={equityTarget}
                              onChange={(e) => {
                                const val = Number(e.target.value);
                                setEquityTarget(val);
                                setFixedIncomeTarget(100 - val);
                              }}
                              className="slider-premium"
                            />
                          </div>

                          <div>
                            <div className="flex justify-between mb-2">
                              <span className="text-sm text-[#A3A3A3]">Fixed Income</span>
                              <span className="text-sm font-semibold text-[#3B82F6]">{fixedIncomeTarget}%</span>
                            </div>
                            <input
                              type="range"
                              min="0"
                              max="100"
                              value={fixedIncomeTarget}
                              onChange={(e) => {
                                const val = Number(e.target.value);
                                setFixedIncomeTarget(val);
                                setEquityTarget(100 - val);
                              }}
                              className="slider-premium"
                            />
                          </div>
                        </div>

                        {/* Visual allocation bar */}
                        <div className="mt-4 h-3 rounded-full overflow-hidden flex">
                          <div
                            className="h-full bg-gradient-to-r from-[#D4AF37] to-[#E8D48A]"
                            style={{ width: `${equityTarget}%` }}
                          />
                          <div
                            className="h-full bg-gradient-to-r from-[#3B82F6] to-[#60A5FA]"
                            style={{ width: `${fixedIncomeTarget}%` }}
                          />
                        </div>
                      </div>

                      {/* Regional Targets */}
                      <div className="card-premium p-6">
                        <h3 className="stat-label mb-6">Regional Targets</h3>

                        <div className="space-y-4">
                          <div>
                            <div className="flex justify-between mb-2">
                              <span className="text-sm text-[#A3A3A3]">North America</span>
                              <span className="text-sm font-semibold text-[#10B981]">{northAmericaTarget}%</span>
                            </div>
                            <input
                              type="range"
                              min="0"
                              max="100"
                              value={northAmericaTarget}
                              onChange={(e) => {
                                const val = Number(e.target.value);
                                setNorthAmericaTarget(val);
                                setInternationalTarget(100 - val);
                              }}
                              className="slider-premium"
                            />
                          </div>

                          <div>
                            <div className="flex justify-between mb-2">
                              <span className="text-sm text-[#A3A3A3]">International</span>
                              <span className="text-sm font-semibold text-[#8B5CF6]">{internationalTarget}%</span>
                            </div>
                            <input
                              type="range"
                              min="0"
                              max="100"
                              value={internationalTarget}
                              onChange={(e) => {
                                const val = Number(e.target.value);
                                setInternationalTarget(val);
                                setNorthAmericaTarget(100 - val);
                              }}
                              className="slider-premium"
                            />
                          </div>
                        </div>

                        {/* Visual allocation bar */}
                        <div className="mt-4 h-3 rounded-full overflow-hidden flex">
                          <div
                            className="h-full bg-gradient-to-r from-[#10B981] to-[#34D399]"
                            style={{ width: `${northAmericaTarget}%` }}
                          />
                          <div
                            className="h-full bg-gradient-to-r from-[#8B5CF6] to-[#A78BFA]"
                            style={{ width: `${internationalTarget}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Save Button */}
                  <div className="mt-8 flex justify-end gap-4">
                    <button
                      onClick={handleSaveSettings}
                      disabled={saving || loading}
                      className="btn-premium"
                    >
                      {saving ? 'Saving...' : 'Save Profile'}
                    </button>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
                  <button
                    onClick={() => router.push('/advisor-team')}
                    className="card-premium p-6 text-left group hover:border-[rgba(212,175,55,0.3)] transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg text-[#FAFAFA] font-medium mb-1 group-hover:text-[#D4AF37] transition-colors">
                          Run Analysis
                        </h3>
                        <p className="text-sm text-[#6B6B6B]">
                          Get AI-powered insights from your advisor team
                        </p>
                      </div>
                      <div className="w-10 h-10 rounded-full bg-[#252529] flex items-center justify-center group-hover:bg-[#D4AF37] transition-colors">
                        <svg className="w-5 h-5 text-[#D4AF37] group-hover:text-[#0D0D0F] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                      </div>
                    </div>
                  </button>

                  <button
                    onClick={() => router.push('/accounts')}
                    className="card-premium p-6 text-left group hover:border-[rgba(212,175,55,0.3)] transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg text-[#FAFAFA] font-medium mb-1 group-hover:text-[#D4AF37] transition-colors">
                          Manage Accounts
                        </h3>
                        <p className="text-sm text-[#6B6B6B]">
                          Add or modify your investment accounts
                        </p>
                      </div>
                      <div className="w-10 h-10 rounded-full bg-[#252529] flex items-center justify-center group-hover:bg-[#D4AF37] transition-colors">
                        <svg className="w-5 h-5 text-[#D4AF37] group-hover:text-[#0D0D0F] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                      </div>
                    </div>
                  </button>
                </div>
              </>
            )}
            </div>
          </div>
        </div>
      </Layout>
    </>
  );
}
