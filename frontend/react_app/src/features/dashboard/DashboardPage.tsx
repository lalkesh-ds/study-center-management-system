import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../../api/analytics'
import { StatCard } from '../../components/shared/StatCard'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { ErrorState } from '../../components/shared/ErrorState'
import { formatCurrencyINR, formatDate } from '../../lib/utils'
import {
  Armchair,
  Users,
  Clock,
  Coins,
  AlertTriangle,
  Layers,
  ArrowUpRight,
  Calendar,
  Sparkles,
} from 'lucide-react'
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts'
import { Link } from 'react-router-dom'

const SHIFT_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']

export const DashboardPage: React.FC = () => {
  const [targetDate, setTargetDate] = useState(() => new Date().toISOString().split('T')[0])

  // Fetch live dashboard summary
  const {
    data: summary,
    isLoading: isSummaryLoading,
    error: summaryError,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ['dashboard-summary', targetDate],
    queryFn: () => analyticsApi.getDashboardSummary(targetDate),
  })

  // Fetch expiring memberships queue (horizon 3 days)
  const {
    data: expiringList,
    isLoading: isExpiringLoading,
    error: expiringError,
  } = useQuery({
    queryKey: ['expiring-memberships', 3],
    queryFn: () => analyticsApi.getExpiringMemberships(3),
  })

  if (summaryError) {
    return (
      <ErrorState
        title="Could not load executive metrics"
        message={(summaryError as Error).message}
        onRetry={() => refetchSummary()}
      />
    )
  }

  // Safe metrics extraction with fallbacks to backend schemas
  const physicalRate = summary?.physical_utilization_rate ?? summary?.physical_utilization_percentage ?? 0
  const occupiedSeats = summary?.occupied_physical_seats ?? summary?.occupied_seats_count ?? 0
  const totalSeats = summary?.total_physical_seats ?? 100

  const slotRate = summary?.slot_occupancy_rate ?? summary?.slot_occupancy_percentage ?? 0
  const bookedSlots = summary?.booked_shift_slots ?? summary?.consumed_slots ?? 0
  const totalSlots = summary?.total_slot_capacity ?? summary?.total_slots ?? 300

  const seatHourRate = summary?.seat_hour_occupancy_rate ?? summary?.seat_hour_occupancy_percentage ?? 0
  const bookedSeatHours = summary?.booked_seat_hours ?? summary?.consumed_seat_hours ?? 0
  const totalSeatHours = summary?.total_seat_hours_capacity ?? summary?.total_seat_hours ?? 1600

  const totalDues = summary?.total_outstanding_dues ?? summary?.total_pending_dues ?? 0
  const expiringSoonCount = summary?.expiring_soon_count ?? 0

  // Shift Distribution Data formatting
  const shiftChartData = summary?.shift_breakdown
    ? Object.entries(summary.shift_breakdown).map(([name, value]) => ({
        name,
        value,
      }))
    : []

  // Capacity KPIs comparison data
  const capacityComparisonData = summary
    ? [
        {
          name: 'Physical Desks',
          rate: Number(physicalRate.toFixed(1)),
          info: `${occupiedSeats} / ${totalSeats} Desks`,
        },
        {
          name: 'Slot-Capacity',
          rate: Number(slotRate.toFixed(1)),
          info: `${bookedSlots} / ${totalSlots} Slots`,
        },
        {
          name: 'Seat-Hours',
          rate: Number(seatHourRate.toFixed(1)),
          info: `${Math.round(Number(bookedSeatHours))} / ${totalSeatHours} Hrs`,
        },
      ]
    : []

  return (
    <div className="space-y-6">
      {/* Top Controls Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-[#0e1629] p-4 rounded-xl border border-white/[0.07]">
        <div className="flex items-center gap-2">
          <Calendar size={18} className="text-indigo-400 shrink-0" />
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest">Audit Date:</span>
          <input
            type="date"
            value={targetDate}
            onChange={(e) => setTargetDate(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg border border-white/[0.1] bg-slate-900 text-xs font-medium text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 [color-scheme:dark]"
          />
        </div>

        <div className="flex items-center gap-2">
          <Link
            to="/memberships"
            className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold shadow-lg shadow-indigo-500/20 transition-all flex items-center gap-1.5"
          >
            <span>New Admission</span>
            <ArrowUpRight size={14} />
          </Link>
          <Link
            to="/attendance"
            className="px-3.5 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.10] text-slate-300 text-xs font-semibold transition-all border border-white/[0.08]"
          >
            Check-In Desk
          </Link>
        </div>
      </div>

      {/* 4 Primary Top Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Physical Utilization"
          value={summary ? `${physicalRate.toFixed(1)}%` : '—'}
          subtitle={summary ? `${occupiedSeats} of ${totalSeats} Desks Occupied` : 'Loading...'}
          icon={Armchair}
          colorScheme="blue"
        />
        <StatCard
          title="Slot-Capacity Occupancy"
          value={summary ? `${slotRate.toFixed(1)}%` : '—'}
          subtitle={summary ? `${bookedSlots} of ${totalSlots} Shift Slots` : 'Loading...'}
          icon={Layers}
          colorScheme="emerald"
        />
        <StatCard
          title="Time-Weighted Seat-Hours"
          value={summary ? `${seatHourRate.toFixed(1)}%` : '—'}
          subtitle={summary ? `${Math.round(Number(bookedSeatHours))} / ${totalSeatHours} Facility Hrs` : 'Loading...'}
          icon={Clock}
          colorScheme="purple"
        />
        <StatCard
          title="Pending Receivables"
          value={summary ? formatCurrencyINR(totalDues) : '—'}
          subtitle={summary ? `${expiringSoonCount} Subscriptions Expiring Soon` : 'Loading...'}
          icon={Coins}
          colorScheme="amber"
        />
      </div>

      {/* Visual Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Capacity Metrics Bar Chart */}
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Multidimensional Capacity Comparison</CardTitle>
              <CardDescription>Physical chairs vs shift-slots vs continuous seat-hours</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="h-72">
            {isSummaryLoading ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">Loading chart...</div>
            ) : capacityComparisonData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={capacityComparisonData} margin={{ top: 20, right: 20, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e2d4a" />
                  <XAxis dataKey="name" stroke="#475569" fontSize={11} tickLine={false} />
                  <YAxis stroke="#475569" fontSize={11} domain={[0, 100]} unit="%" tickLine={false} />
                  <Tooltip
                    formatter={(val: any) => [`${val}%`, 'Occupancy Rate']}
                    contentStyle={{ borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)', fontSize: '12px', background: '#0e1629', color: '#e2e8f0' }}
                  />
                  <Bar dataKey="rate" fill="#3b82f6" radius={[6, 6, 0, 0]} maxBarSize={48}>
                    {capacityComparisonData.map((_, idx) => (
                      <Cell key={`cell-${idx}`} fill={SHIFT_COLORS[idx % SHIFT_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">No data available</div>
            )}
          </CardContent>
        </Card>

        {/* Shift Breakdown Pie Chart */}
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Shift Distribution Breakdown</CardTitle>
              <CardDescription>Active subscriptions partitioned across canonical shifts</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="h-72">
            {isSummaryLoading ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">Loading chart...</div>
            ) : shiftChartData.length > 0 && shiftChartData.some((d) => d.value > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={shiftChartData}
                    innerRadius={60}
                    outerRadius={95}
                    paddingAngle={3}
                    dataKey="value"
                    nameKey="name"
                    label={({ name, percent }: { name?: string; percent?: number }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {shiftChartData.map((_, idx) => (
                      <Cell key={`slice-${idx}`} fill={SHIFT_COLORS[idx % SHIFT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val: any) => [val, 'Students']}
                    contentStyle={{ borderRadius: '10px', border: '1px solid rgba(255,255,255,0.08)', fontSize: '12px', background: '#0e1629', color: '#e2e8f0' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                No active shift allocations on this date
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Action Queue: Expiring Subscriptions Alert */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertTriangle size={18} className="text-amber-500" />
            <div>
              <CardTitle>Renewal Action Queue</CardTitle>
              <CardDescription>Aspirants expiring within the next 3 calendar days</CardDescription>
            </div>
          </div>
          <Link to="/memberships" className="text-xs font-semibold text-blue-600 hover:text-blue-700">
            View All Renewals →
          </Link>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          {isExpiringLoading ? (
            <div className="p-8 text-center text-xs text-slate-400">Scanning active tenures...</div>
          ) : expiringList && expiringList.length > 0 ? (
            <table className="w-full text-left text-xs">
              <thead className="bg-white/[0.03] border-b border-white/[0.07] text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Urgency</th>
                  <th className="py-3 px-4">Student</th>
                  <th className="py-3 px-4">Mobile</th>
                  <th className="py-3 px-4">Desk</th>
                  <th className="py-3 px-4">Shift</th>
                  <th className="py-3 px-4">Expires On</th>
                  <th className="py-3 px-4 text-right">Pending Due</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04] text-slate-300 font-medium">
                {expiringList.map((item) => (
                  <tr key={item.membership_id} className="hover:bg-white/[0.03] transition-colors">
                    <td className="py-3 px-4">
                      {item.days_remaining <= 1 ? (
                        <Badge variant="danger">{item.days_remaining} Day Left</Badge>
                      ) : (
                        <Badge variant="warning">{item.days_remaining} Days Left</Badge>
                      )}
                    </td>
                    <td className="py-3 px-4 font-semibold text-white">{item.student_name}</td>
                    <td className="py-3 px-4 font-mono text-slate-400">{item.student_mobile}</td>
                    <td className="py-3 px-4">Seat #{item.seat_number}</td>
                    <td className="py-3 px-4">{item.shift_name}</td>
                    <td className="py-3 px-4">{formatDate(item.end_date)}</td>
                    <td className="py-3 px-4 text-right font-bold text-slate-900">
                      {formatCurrencyINR(item.due_amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-8 text-center text-xs text-slate-500">
              <Sparkles size={16} className="text-emerald-500 mx-auto mb-1" />
              <span>Zero memberships expiring in the next 3 days. All subscriptions healthy.</span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
