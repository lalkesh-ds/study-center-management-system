import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../../api/analytics'
import { paymentsApi } from '../../api/payments'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card'
import { StatCard } from '../../components/shared/StatCard'
import { ErrorState } from '../../components/shared/ErrorState'
import { formatCurrencyINR, formatDate } from '../../lib/utils'
import {
  BarChart3,
  Calendar,
  FileDown,
  TrendingUp,
  Receipt,
  AlertCircle,
  Coins,
  CreditCard,
} from 'lucide-react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

const METHOD_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']

export const AnalyticsPage: React.FC = () => {
  const thirtyDaysAgo = new Date(Date.now() - 30 * 86400000).toISOString().split('T')[0]
  const today = new Date().toISOString().split('T')[0]

  const [startDate, setStartDate] = useState(thirtyDaysAgo)
  const [endDate, setEndDate] = useState(today)

  // Fetch Revenue Report
  const {
    data: revenueReport,
    isLoading: isRevLoading,
    error: revError,
    refetch: refetchRev,
  } = useQuery({
    queryKey: ['revenue-report', startDate, endDate],
    queryFn: () => analyticsApi.getRevenueReport(startDate, endDate),
  })

  // Format method breakdown for charts
  const methodChartData = revenueReport
    ? [
        { method: 'UPI', revenue: Number(revenueReport.upi_total || 0) },
        { method: 'Cash', revenue: Number(revenueReport.cash_total || 0) },
        { method: 'Card', revenue: Number(revenueReport.card_total || 0) },
        { method: 'Net Banking', revenue: Number(revenueReport.net_banking_total || 0) },
      ]
    : []

  const totalRevenue = revenueReport ? (revenueReport.total_revenue ?? revenueReport.total_collections ?? 0) : 0

  return (
    <div className="space-y-6">
      {/* Date Range Selector */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
        <div className="flex flex-wrap items-center gap-3">
          <Calendar size={18} className="text-blue-600" />
          <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Date Horizon:</span>
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-xs text-slate-400">to</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <a
          href={paymentsApi.exportRevenueCsv(startDate, endDate)}
          target="_blank"
          rel="noreferrer"
          className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition-colors flex items-center justify-center gap-1.5 shrink-0"
        >
          <FileDown size={14} />
          <span>Export Revenue Report (CSV)</span>
        </a>
      </div>

      {revError ? (
        <ErrorState message={(revError as Error).message} onRetry={() => refetchRev()} />
      ) : (
        <>
          {/* Revenue Top Stat Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard
              title="Net Collections"
              value={revenueReport ? formatCurrencyINR(totalRevenue) : '—'}
              subtitle="Total completed collections in date range"
              icon={Coins}
              colorScheme="emerald"
            />
            <StatCard
              title="Transaction Volume"
              value={revenueReport ? revenueReport.transaction_count : '—'}
              subtitle="Receipts issued by cashier terminal"
              icon={Receipt}
              colorScheme="blue"
            />
            <StatCard
              title="UPI Digital Share"
              value={
                revenueReport && Number(totalRevenue) > 0
                  ? `${((Number(revenueReport.upi_total || 0) / Number(totalRevenue)) * 100).toFixed(0)}%`
                  : '0%'
              }
              subtitle="Instant QR payment collections"
              icon={AlertCircle}
              colorScheme="amber"
            />
          </div>

          {/* Revenue Visual Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Bar Chart Collections */}
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Collections by Payment Channel</CardTitle>
                  <CardDescription>Breakdown by CASH, UPI, CARD, and NET_BANKING</CardDescription>
                </div>
              </CardHeader>
              <CardContent className="h-72">
                {isRevLoading ? (
                  <div className="h-full flex items-center justify-center text-xs text-slate-400">Loading charts...</div>
                ) : methodChartData.length > 0 && methodChartData.some((d) => d.revenue > 0) ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={methodChartData} margin={{ top: 20, right: 20, left: 10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="method" stroke="#64748b" fontSize={11} tickLine={false} />
                      <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(val) => `₹${val}`} />
                      <Tooltip
                        formatter={(val: any) => [formatCurrencyINR(val), 'Revenue']}
                        contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                      />
                      <Bar dataKey="revenue" fill="#3b82f6" radius={[6, 6, 0, 0]} maxBarSize={48}>
                        {methodChartData.map((_, idx) => (
                          <Cell key={`bar-${idx}`} fill={METHOD_COLORS[idx % METHOD_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-xs text-slate-400">
                    No transactions recorded in this period.
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Pie Chart Channel Share */}
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Channel Share Distribution</CardTitle>
                  <CardDescription>Proportional share of total facility receipts</CardDescription>
                </div>
              </CardHeader>
              <CardContent className="h-72">
                {isRevLoading ? (
                  <div className="h-full flex items-center justify-center text-xs text-slate-400">Loading charts...</div>
                ) : methodChartData.length > 0 && methodChartData.some((d) => d.revenue > 0) ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={methodChartData}
                        innerRadius={55}
                        outerRadius={90}
                        paddingAngle={3}
                        dataKey="revenue"
                        nameKey="method"
                        label={({ method, percent }: { method?: string; percent?: number }) => `${method}: ${((percent || 0) * 100).toFixed(0)}%`}
                        labelLine={false}
                      >
                        {methodChartData.map((_, idx) => (
                          <Cell key={`pie-${idx}`} fill={METHOD_COLORS[idx % METHOD_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(val: any) => [formatCurrencyINR(val), 'Collected']}
                        contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-xs text-slate-400">
                    No transactions recorded in this period.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
