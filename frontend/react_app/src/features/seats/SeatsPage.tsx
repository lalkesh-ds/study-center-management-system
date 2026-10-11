import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { seatsApi } from '../../api/seats'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { Modal } from '../../components/shared/Modal'
import { ErrorState } from '../../components/shared/ErrorState'
import type { DailySeatMatrixItem } from '../../types'
import {
  Calendar,
  Zap,
  Lock,
  Wrench,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  Sparkles,
  AlertCircle,
  Layers,
} from 'lucide-react'

export const SeatsPage: React.FC = () => {
  const queryClient = useQueryClient()
  const [targetDate, setTargetDate] = useState(() => new Date().toISOString().split('T')[0])
  const [shiftFilter, setShiftFilter] = useState<'ALL' | 'MORNING' | 'AFTERNOON' | 'EVENING' | 'FULL_DAY'>('ALL')
  const [selectedSeat, setSelectedSeat] = useState<DailySeatMatrixItem | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  // Fetch 100-seat multi-shift matrix
  const {
    data: seatMatrix = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['seats-availability', targetDate],
    queryFn: () => seatsApi.getSeatAvailability(targetDate),
  })

  // Toggle Maintenance Mutation
  const toggleMutation = useMutation({
    mutationFn: (seatId: number) => seatsApi.toggleMaintenance(seatId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['seats-availability'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
      if (selectedSeat) {
        setSelectedSeat((prev) => (prev ? { ...prev, is_active: !prev.is_active } : null))
      }
    },
  })

  const getSeatStatus = (seat: DailySeatMatrixItem) => {
    if (!seat.is_active) {
      return { label: 'Maintenance', color: 'bg-rose-50 text-rose-700 border-rose-300', badgeVariant: 'danger' as const }
    }

    if (shiftFilter === 'MORNING') {
      return seat.morning_available
        ? { label: 'Available', color: 'bg-emerald-50 text-emerald-700 border-emerald-300', badgeVariant: 'success' as const }
        : { label: 'Occupied', color: 'bg-amber-50 text-amber-700 border-amber-300', badgeVariant: 'warning' as const }
    }

    if (shiftFilter === 'AFTERNOON') {
      return seat.afternoon_available
        ? { label: 'Available', color: 'bg-emerald-50 text-emerald-700 border-emerald-300', badgeVariant: 'success' as const }
        : { label: 'Occupied', color: 'bg-amber-50 text-amber-700 border-amber-300', badgeVariant: 'warning' as const }
    }

    if (shiftFilter === 'EVENING') {
      return seat.evening_available
        ? { label: 'Available', color: 'bg-emerald-50 text-emerald-700 border-emerald-300', badgeVariant: 'success' as const }
        : { label: 'Occupied', color: 'bg-amber-50 text-amber-700 border-amber-300', badgeVariant: 'warning' as const }
    }

    if (shiftFilter === 'FULL_DAY') {
      return seat.full_day_available
        ? { label: 'Available', color: 'bg-emerald-50 text-emerald-700 border-emerald-300', badgeVariant: 'success' as const }
        : { label: 'Occupied', color: 'bg-amber-50 text-amber-700 border-amber-300', badgeVariant: 'warning' as const }
    }

    // ALL perspective
    const m = seat.morning_available
    const a = seat.afternoon_available
    const e = seat.evening_available
    const f = seat.full_day_available

    if (!f && !m && !a && !e) {
      return { label: 'Full Day Booked', color: 'bg-purple-50 text-purple-700 border-purple-300', badgeVariant: 'purple' as const }
    }
    if (m && a && e) {
      return { label: 'Completely Free', color: 'bg-emerald-50 text-emerald-700 border-emerald-300', badgeVariant: 'success' as const }
    }
    return { label: 'Partially Booked', color: 'bg-amber-50 text-amber-700 border-amber-300', badgeVariant: 'warning' as const }
  }

  // Summary Metrics
  const totalChairs = seatMatrix.length
  const maintenanceCount = seatMatrix.filter((s) => !s.is_active).length
  const completelyFreeCount = seatMatrix.filter(
    (s) => s.is_active && s.morning_available && s.afternoon_available && s.evening_available
  ).length
  const occupiedAnyCount = totalChairs - maintenanceCount - completelyFreeCount

  const handleSeatClick = (seat: DailySeatMatrixItem) => {
    setSelectedSeat(seat)
    setIsModalOpen(true)
  }

  if (error) {
    return (
      <ErrorState
        title="Could not load seat matrix"
        message={(error as Error).message}
        onRetry={() => refetch()}
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar size={18} className="text-blue-600 shrink-0" />
            <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Date:</span>
            <input
              type="date"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <Layers size={18} className="text-slate-400 shrink-0" />
            <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Perspective:</span>
            <select
              value={shiftFilter}
              onChange={(e) => setShiftFilter(e.target.value as any)}
              className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">All Shifts Overview</option>
              <option value="MORNING">Morning (07:00 – 11:00)</option>
              <option value="AFTERNOON">Afternoon (11:00 – 15:00)</option>
              <option value="EVENING">Evening (15:00 – 23:00)</option>
              <option value="FULL_DAY">Full Day (07:00 – 23:00)</option>
            </select>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
            <span className="text-slate-600 font-medium">Free</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-amber-500"></span>
            <span className="text-slate-600 font-medium">Partially Booked</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-purple-500"></span>
            <span className="text-slate-600 font-medium">Full Day</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-500"></span>
            <span className="text-slate-600 font-medium">Maintenance</span>
          </span>
        </div>
      </div>

      {/* Summary KPI Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Total Chairs</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{totalChairs || 100}</p>
        </div>
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Completely Free</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{completelyFreeCount}</p>
        </div>
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Active Bookings</p>
          <p className="text-2xl font-bold text-blue-600 mt-1">{occupiedAnyCount}</p>
        </div>
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Maintenance</p>
          <p className="text-2xl font-bold text-rose-600 mt-1">{maintenanceCount}</p>
        </div>
      </div>

      {/* Interactive 10x10 Seat Grid */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Physical Study Floor Plan (100 Desks)</CardTitle>
            <CardDescription>Click any seat to inspect shift allocations, power outlets, lockers, or toggle maintenance status</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-20 text-center text-xs text-slate-400">Loading live facility grid...</div>
          ) : (
            <div className="grid grid-cols-5 sm:grid-cols-10 gap-2.5 sm:gap-3">
              {seatMatrix.map((seat) => {
                const status = getSeatStatus(seat)
                return (
                  <button
                    key={seat.seat_id}
                    onClick={() => handleSeatClick(seat)}
                    className={`relative p-3 rounded-xl border flex flex-col items-center justify-center gap-1 text-center transition-all duration-150 hover:scale-105 hover:shadow-md cursor-pointer ${status.color}`}
                  >
                    <span className="text-sm font-bold tracking-tight">#{seat.seat_number}</span>
                    <span className="text-[10px] font-semibold truncate max-w-full px-1">{status.label}</span>
                    <div className="flex items-center gap-1 text-[10px] opacity-75">
                      {seat.has_power_outlet && <span title="Power Outlet Available"><Zap size={10} /></span>}
                      {seat.has_locker && <span title="Locker Available"><Lock size={10} /></span>}
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Seat Inspector Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={selectedSeat ? `Physical Desk #${selectedSeat.seat_number}` : 'Desk Inspector'}
        subtitle={`Evaluation for ${targetDate}`}
        maxWidth="md"
      >
        {selectedSeat && (
          <div className="space-y-6">
            {/* Status & Amenities */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 border border-slate-200">
              <div className="space-y-1">
                <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Operational Status</p>
                <Badge variant={selectedSeat.is_active ? 'success' : 'danger'}>
                  {selectedSeat.is_active ? 'Active Desk' : 'Under Maintenance'}
                </Badge>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-700 font-medium">
                <span className="flex items-center gap-1">
                  <Zap size={14} className={selectedSeat.has_power_outlet ? 'text-amber-500' : 'text-slate-300'} />
                  Power Outlet: {selectedSeat.has_power_outlet ? 'Yes' : 'No'}
                </span>
                <span className="flex items-center gap-1">
                  <Lock size={14} className={selectedSeat.has_locker ? 'text-blue-500' : 'text-slate-300'} />
                  Locker: {selectedSeat.has_locker ? 'Yes' : 'No'}
                </span>
              </div>
            </div>

            {/* Shift Breakdown Schedule */}
            <div className="space-y-2.5">
              <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Shift Allocation Schedule</h4>
              <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden text-xs">
                {/* Morning */}
                <div className="p-3 flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-slate-900">Morning Shift (07:00 – 11:00)</p>
                    {selectedSeat.morning_occupied_by && (
                      <p className="text-slate-500 text-[11px]">Occupant: {selectedSeat.morning_occupied_by}</p>
                    )}
                  </div>
                  <Badge variant={selectedSeat.morning_available ? 'success' : 'warning'}>
                    {selectedSeat.morning_available ? 'Available' : 'Booked'}
                  </Badge>
                </div>

                {/* Afternoon */}
                <div className="p-3 flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-slate-900">Afternoon Shift (11:00 – 15:00)</p>
                    {selectedSeat.afternoon_occupied_by && (
                      <p className="text-slate-500 text-[11px]">Occupant: {selectedSeat.afternoon_occupied_by}</p>
                    )}
                  </div>
                  <Badge variant={selectedSeat.afternoon_available ? 'success' : 'warning'}>
                    {selectedSeat.afternoon_available ? 'Available' : 'Booked'}
                  </Badge>
                </div>

                {/* Evening */}
                <div className="p-3 flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-slate-900">Evening Shift (15:00 – 23:00)</p>
                    {selectedSeat.evening_occupied_by && (
                      <p className="text-slate-500 text-[11px]">Occupant: {selectedSeat.evening_occupied_by}</p>
                    )}
                  </div>
                  <Badge variant={selectedSeat.evening_available ? 'success' : 'warning'}>
                    {selectedSeat.evening_available ? 'Available' : 'Booked'}
                  </Badge>
                </div>

                {/* Full Day */}
                <div className="p-3 flex items-center justify-between bg-slate-50/50">
                  <div>
                    <p className="font-semibold text-slate-900">Full Day Continuous (07:00 – 23:00)</p>
                    <p className="text-slate-500 text-[11px]">Requires all 3 shift blocks open</p>
                  </div>
                  <Badge variant={selectedSeat.full_day_available ? 'success' : 'neutral'}>
                    {selectedSeat.full_day_available ? 'Eligible' : 'Blocked'}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Maintenance Toggle Action */}
            <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-500 font-medium">Front-Desk Desk Controls</span>
              <button
                disabled={toggleMutation.isPending}
                onClick={() => toggleMutation.mutate(selectedSeat.seat_id)}
                className={`px-4 py-2 rounded-lg text-xs font-semibold shadow-xs transition-colors flex items-center gap-1.5 ${
                  selectedSeat.is_active
                    ? 'bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200'
                    : 'bg-emerald-600 text-white hover:bg-emerald-700'
                }`}
              >
                <Wrench size={14} />
                <span>
                  {toggleMutation.isPending
                    ? 'Updating...'
                    : selectedSeat.is_active
                    ? 'Disable (Put under Maintenance)'
                    : 'Enable (Restore to Service)'}
                </span>
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
