import React from 'react'

// Mock Recharts components for testing
export const ResponsiveContainer = ({ children }: { children: React.ReactNode }) => (
  <div data-testid="responsive-container">{children}</div>
)

export const LineChart = ({ children, data }: any) => (
  <div data-testid="line-chart" data-chart-data={JSON.stringify(data)}>
    {children}
  </div>
)

export const BarChart = ({ children, data }: any) => (
  <div data-testid="bar-chart" data-chart-data={JSON.stringify(data)}>
    {children}
  </div>
)

export const PieChart = ({ children, data }: any) => (
  <div data-testid="pie-chart" data-chart-data={JSON.stringify(data)}>
    {children}
  </div>
)

export const AreaChart = ({ children, data }: any) => (
  <div data-testid="area-chart" data-chart-data={JSON.stringify(data)}>
    {children}
  </div>
)

export const Line = ({ dataKey }: any) => (
  <div data-testid="line" data-key={dataKey} />
)

export const Bar = ({ dataKey }: any) => (
  <div data-testid="bar" data-key={dataKey} />
)

export const Area = ({ dataKey }: any) => (
  <div data-testid="area" data-key={dataKey} />
)

export const Pie = ({ data }: any) => (
  <div data-testid="pie" data-pie-data={JSON.stringify(data)} />
)

export const Cell = ({ fill }: any) => (
  <div data-testid="cell" data-fill={fill} />
)

export const XAxis = ({ dataKey }: any) => (
  <div data-testid="x-axis" data-key={dataKey} />
)

export const YAxis = () => <div data-testid="y-axis" />

export const CartesianGrid = () => <div data-testid="cartesian-grid" />

export const Tooltip = () => <div data-testid="tooltip" />

export const Legend = () => <div data-testid="legend" />
