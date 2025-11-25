/**
 * Mock data for frontend tests
 */

export const mockUser = {
  id: 'test_user_001',
  email: 'test@example.com',
  firstName: 'Test',
  lastName: 'User',
  fullName: 'Test User',
}

export const mockPortfolioData = {
  accounts: [
    {
      id: 'acc_001',
      name: 'Retirement Account',
      type: 'ira',
      cash_balance: 5000,
      positions: [
        {
          id: 'pos_001',
          symbol: 'VTI',
          quantity: 100,
          cost_basis: 20000,
          instrument: {
            symbol: 'VTI',
            name: 'Vanguard Total Stock Market ETF',
            instrument_type: 'etf',
            asset_class: 'equity',
            current_price: 220,
            expense_ratio: 0.03,
          },
        },
        {
          id: 'pos_002',
          symbol: 'BND',
          quantity: 200,
          cost_basis: 14000,
          instrument: {
            symbol: 'BND',
            name: 'Vanguard Total Bond Market ETF',
            instrument_type: 'etf',
            asset_class: 'bond',
            current_price: 75,
            expense_ratio: 0.04,
          },
        },
      ],
    },
    {
      id: 'acc_002',
      name: 'Taxable Account',
      type: 'taxable',
      cash_balance: 2000,
      positions: [
        {
          id: 'pos_003',
          symbol: 'VXUS',
          quantity: 50,
          cost_basis: 2800,
          instrument: {
            symbol: 'VXUS',
            name: 'Vanguard Total International Stock ETF',
            instrument_type: 'etf',
            asset_class: 'equity',
            current_price: 60,
            expense_ratio: 0.07,
          },
        },
      ],
    },
  ],
}

export const mockAnalysisJob = {
  id: 'job_001',
  status: 'pending',
  created_at: '2024-01-15T10:00:00Z',
  job_type: 'portfolio_analysis',
}

export const mockCompletedAnalysis = {
  id: 'job_001',
  status: 'completed',
  created_at: '2024-01-15T10:00:00Z',
  completed_at: '2024-01-15T10:05:00Z',
  job_type: 'portfolio_analysis',
  report_payload: {
    analysis: `
# Portfolio Analysis Report

Your portfolio demonstrates good diversification across asset classes with
a total value of approximately $45,000.

## Asset Allocation

- 60% in domestic equities (VTI)
- 25% in bonds (BND)
- 15% in international equities (VXUS)

This balanced approach aligns well with a moderate risk tolerance.

## Key Strengths

- Appropriate equity/bond balance
- Low-cost index fund approach
- Geographic diversification

## Recommendations

- Consider increasing international allocation to 20-25%
- Maintain current savings rate
- Review allocation annually
    `.trim(),
  },
  charts_payload: {
    asset_allocation: {
      title: 'Asset Allocation',
      type: 'pie',
      data: [
        { name: 'US Equities', value: 60, fill: '#3b82f6' },
        { name: 'Bonds', value: 25, fill: '#10b981' },
        { name: 'International', value: 15, fill: '#f59e0b' },
      ],
    },
    performance: {
      title: 'Portfolio Performance',
      type: 'line',
      data: [
        { date: '2024-01', value: 40000 },
        { date: '2024-02', value: 41500 },
        { date: '2024-03', value: 43000 },
        { date: '2024-04', value: 45000 },
      ],
    },
  },
  retirement_payload: {
    success_rate: 85.5,
    projected_value: 1250000,
    years_to_retirement: 20,
    monthly_income: 5200,
    scenarios: [
      { percentile: 10, value: 800000 },
      { percentile: 50, value: 1250000 },
      { percentile: 90, value: 1800000 },
    ],
  },
  summary_payload: {
    summary: 'Your portfolio is well-diversified with a balanced risk profile.',
    key_findings: [
      'Good asset allocation for moderate risk tolerance',
      'Low expense ratios across holdings',
      'Strong projected retirement outcomes',
    ],
    recommendations: [
      'Increase international exposure',
      'Continue current savings rate',
      'Annual rebalancing recommended',
    ],
  },
}

export const mockAccounts = [
  {
    id: 'acc_001',
    name: 'Retirement Account',
    type: 'ira',
    cash_balance: 5000,
    total_value: 42000,
    created_at: '2023-01-15T00:00:00Z',
  },
  {
    id: 'acc_002',
    name: 'Taxable Account',
    type: 'taxable',
    cash_balance: 2000,
    total_value: 5000,
    created_at: '2023-06-20T00:00:00Z',
  },
]

export const mockJobHistory = [
  {
    id: 'job_003',
    status: 'completed',
    created_at: '2024-01-10T09:00:00Z',
    completed_at: '2024-01-10T09:05:00Z',
  },
  {
    id: 'job_002',
    status: 'completed',
    created_at: '2024-01-05T14:30:00Z',
    completed_at: '2024-01-05T14:35:00Z',
  },
  {
    id: 'job_001',
    status: 'completed',
    created_at: '2024-01-01T10:00:00Z',
    completed_at: '2024-01-01T10:05:00Z',
  },
]

export const mockApiError = {
  error: 'Internal Server Error',
  message: 'Failed to process request',
  statusCode: 500,
}
