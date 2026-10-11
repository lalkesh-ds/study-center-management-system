import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { membershipsApi } from '../../api/memberships'
import { studentsApi } from '../../api/students'
import { shiftsApi } from '../../api/shifts'
import { seatsApi } from '../../api/seats'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { Modal } from '../../components/shared/Modal'
import { ErrorState } from '../../components/shared/ErrorState'
import { EmptyState } from '../../components/shared/EmptyState'
import { formatDate, formatCurrencyINR } from '../../lib/utils'
import type {
  Membership,
  MembershipCreatePayload,
  MembershipRenewPayload,
  MembershipCancelPayload,
} from '../../types'
import {
  PlusCircle,
  RefreshCw,
  XCircle,
  ListFilter,
  CheckCircle,
  AlertCircle,
  Loader2,
  Coins,
} from 'lucide-react'

export const MembershipsPage: React.FC = () => {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'admissions' | 'renewals' | 'cancellations' | 'all'>('all')
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ACTIVE' | 'CANCELLED'>('ALL')

  // Admissions Form State
  const today = new Date().toISOString().split('T')[0]
  const thirtyDaysLater = new Date(Date.now() + 29 * 86400000).toISOString().split('T')[0]

  const [admissionForm, setAdmissionForm] = useState<MembershipCreatePayload>({
    student_id: '',
    seat_id: 1,
    shift_id: 1,
    start_date: today,
    end_date: thirtyDaysLater,
    discount_amount: 0,
    initial_payment_amount: 800,
    initial_payment_method: 'CASH',
    initial_payment_ref: '',
  })
  const [collectPayment, setCollectPayment] = useState(true)
  const [admissionError, setAdmissionError] = useState<string | null>(null)
  const [admissionSuccess, setAdmissionSuccess] = useState<string | null>(null)

  // Renewals State
  const [selectedRenewMem, setSelectedRenewMem] = useState<Membership | null>(null)
  const [renewForm, setRenewForm] = useState<MembershipRenewPayload>({
    start_date: '',
    end_date: '',
    target_seat_id: null,
    target_shift_id: null,
    discount_amount: 0,
    initial_payment_amount: null,
    initial_payment_method: 'CASH',
  })
  const [retainSeat, setRetainSeat] = useState(true)
  const [retainShift, setRetainShift] = useState(true)
  const [renewError, setRenewError] = useState<string | null>(null)
  const [renewSuccess, setRenewSuccess] = useState<string | null>(null)

  // Cancellations State
  const [selectedCancelMem, setSelectedCancelMem] = useState<Membership | null>(null)
  const [cancelReason, setCancelReason] = useState('')
  const [cancelError, setCancelError] = useState<string | null>(null)
  const [cancelSuccess, setCancelSuccess] = useState<string | null>(null)

  // Queries
  const { data: membershipsData, isLoading, error, refetch } = useQuery({
    queryKey: ['memberships-list', statusFilter],
    queryFn: () => membershipsApi.listMemberships(statusFilter === 'ALL' ? undefined : statusFilter, undefined, undefined, 0, 100),
  })
  const memberships = membershipsData?.items || []

  const { data: studentsData } = useQuery({
    queryKey: ['students-for-admission'],
    queryFn: () => studentsApi.listStudents(undefined, 0, 100),
  })
  const students = studentsData?.items || []

  const { data: shifts = [] } = useQuery({
    queryKey: ['shifts-master'],
    queryFn: () => shiftsApi.listShifts(),
  })

  const { data: allSeats = [] } = useQuery({
    queryKey: ['seats-all'],
    queryFn: () => seatsApi.listSeats(),
  })

  // Selected Shift base fee
  const currentShift = shifts.find((s) => s.id === Number(admissionForm.shift_id))
  const shiftBaseFee = currentShift ? Number(currentShift.base_fee) : 800
  const finalCalculatedFee = Math.max(0, shiftBaseFee - (admissionForm.discount_amount || 0))

  // Admission Mutation
  const admissionMutation = useMutation({
    mutationFn: (payload: MembershipCreatePayload) => membershipsApi.createAdmission(payload),
    onSuccess: (res) => {
      setAdmissionSuccess(`Admission confirmed for Seat #${res.seat_number} (${res.shift_name})!`)
      setAdmissionError(null)
      queryClient.invalidateQueries({ queryKey: ['memberships-list'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
      queryClient.invalidateQueries({ queryKey: ['seats-availability'] })
    },
    onError: (err: any) => {
      setAdmissionError(err.message || 'Seat reservation rejected due to scheduling conflict.')
      setAdmissionSuccess(null)
    },
  })

  // Renewal Mutation
  const renewMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: MembershipRenewPayload }) =>
      membershipsApi.renewMembership(id, payload),
    onSuccess: (res) => {
      setRenewSuccess(`Subscription renewed! New contract valid from ${formatDate(res.start_date)} to ${formatDate(res.end_date)}.`)
      setRenewError(null)
      setSelectedRenewMem(null)
      queryClient.invalidateQueries({ queryKey: ['memberships-list'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
      queryClient.invalidateQueries({ queryKey: ['seats-availability'] })
    },
    onError: (err: any) => {
      setRenewError(err.message || 'Renewal rejected due to allocation collision.')
      setRenewSuccess(null)
    },
  })

  // Cancellation Mutation
  const cancelMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: MembershipCancelPayload }) =>
      membershipsApi.cancelMembership(id, payload),
    onSuccess: (res) => {
      setCancelSuccess(`Membership for Seat #${res.seat_number} cancelled. Seat immediately freed for booking.`)
      setCancelError(null)
      setSelectedCancelMem(null)
      setCancelReason('')
      queryClient.invalidateQueries({ queryKey: ['memberships-list'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
      queryClient.invalidateQueries({ queryKey: ['seats-availability'] })
    },
    onError: (err: any) => {
      setCancelError(err.message || 'Cancellation failed.')
      setCancelSuccess(null)
    },
  })

  const handleAdmissionSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!admissionForm.student_id) {
      setAdmissionError('Please select an enrolled student aspirant.')
      return
    }

    const payload: MembershipCreatePayload = {
      ...admissionForm,
      seat_id: Number(admissionForm.seat_id),
      shift_id: Number(admissionForm.shift_id),
      discount_amount: Number(admissionForm.discount_amount) || 0,
      initial_payment_amount: collectPayment ? Number(admissionForm.initial_payment_amount) : null,
      initial_payment_method: collectPayment ? admissionForm.initial_payment_method : null,
      initial_payment_ref: collectPayment ? admissionForm.initial_payment_ref : null,
    }

    admissionMutation.mutate(payload)
  }

  const handleStartRenew = (m: Membership) => {
    setSelectedRenewMem(m)
    const currentEnd = new Date(m.end_date)
    const nextStart = new Date(currentEnd.getTime() + 86400000).toISOString().split('T')[0]
    const nextEnd = new Date(currentEnd.getTime() + 30 * 86400000).toISOString().split('T')[0]

    setRenewForm({
      start_date: nextStart,
      end_date: nextEnd,
      target_seat_id: null,
      target_shift_id: null,
      discount_amount: 0,
      initial_payment_amount: null,
      initial_payment_method: 'CASH',
    })
    setRetainSeat(true)
    setRetainShift(true)
    setRenewError(null)
    setRenewSuccess(null)
  }

  const handleRenewSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedRenewMem) return

    const payload: MembershipRenewPayload = {
      ...renewForm,
      target_seat_id: retainSeat ? null : Number(renewForm.target_seat_id),
      target_shift_id: retainShift ? null : Number(renewForm.target_shift_id),
      discount_amount: Number(renewForm.discount_amount) || 0,
      initial_payment_amount: renewForm.initial_payment_amount ? Number(renewForm.initial_payment_amount) : null,
    }

    renewMutation.mutate({ id: selectedRenewMem.id, payload })
  }

  const handleCancelSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCancelMem) return
    if (!cancelReason.trim()) {
      setCancelError('Please provide a mandatory reason for cancellation.')
      return
    }
    cancelMutation.mutate({ id: selectedCancelMem.id, payload: { cancel_reason: cancelReason.trim() } })
  }

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${
            activeTab === 'all'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          All Memberships Directory
        </button>
        <button
          onClick={() => setActiveTab('admissions')}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
            activeTab === 'admissions'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <PlusCircle size={14} />
          <span>New Admission Booking</span>
        </button>
      </div>

      {activeTab === 'all' ? (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center gap-2">
              <ListFilter size={16} className="text-slate-400" />
              <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="ALL">All Subscriptions</option>
                <option value="ACTIVE">Active</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>
            <span className="text-xs text-slate-500 font-medium">Total: {memberships.length} records</span>
          </div>

          {/* Memberships Table */}
          <Card>
            <CardContent className="p-0 overflow-x-auto">
              {isLoading ? (
                <div className="py-20 text-center text-xs text-slate-400">Loading memberships...</div>
              ) : error ? (
                <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
              ) : memberships.length === 0 ? (
                <EmptyState
                  title="No memberships found"
                  description="No membership subscription records match your criteria."
                  action={{ label: 'Book Admission', onClick: () => setActiveTab('admissions') }}
                />
              ) : (
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Desk</th>
                      <th className="py-3 px-4">Student</th>
                      <th className="py-3 px-4">Shift</th>
                      <th className="py-3 px-4">Tenure Period</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Fee Structure</th>
                      <th className="py-3 px-4">Payment</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
                    {memberships.map((m) => (
                      <tr key={m.id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-3 px-4 font-bold text-slate-900">Seat #{m.seat_number}</td>
                        <td className="py-3 px-4 font-semibold text-slate-900">{m.student_name || 'Aspirant'}</td>
                        <td className="py-3 px-4">{m.shift_name}</td>
                        <td className="py-3 px-4">
                          <span className="font-medium text-slate-900">{formatDate(m.start_date)}</span>
                          <span className="text-slate-400"> → </span>
                          <span className="font-medium text-slate-900">{formatDate(m.end_date)}</span>
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant={m.status === 'ACTIVE' ? 'success' : 'danger'}>{m.status}</Badge>
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-bold text-slate-900">{formatCurrencyINR(m.final_fee)}</span>
                          {Number(m.discount_amount) > 0 && (
                            <span className="text-[10px] text-emerald-600 block">(-{formatCurrencyINR(m.discount_amount)} disc)</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-medium text-slate-800">Paid: {formatCurrencyINR(m.total_paid)}</span>
                          {Number(m.due_amount) > 0 && (
                            <span className="text-[10px] text-rose-600 font-bold block">
                              Due: {formatCurrencyINR(m.due_amount)}
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right">
                          {m.status === 'ACTIVE' && (
                            <div className="flex items-center justify-end gap-1.5">
                              <button
                                onClick={() => handleStartRenew(m)}
                                className="px-2 py-1 rounded bg-blue-50 text-blue-700 hover:bg-blue-100 text-[11px] font-semibold transition-colors"
                              >
                                Renew
                              </button>
                              <button
                                onClick={() => setSelectedCancelMem(m)}
                                className="px-2 py-1 rounded bg-rose-50 text-rose-700 hover:bg-rose-100 text-[11px] font-semibold transition-colors"
                              >
                                Cancel
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </CardContent>
          </Card>
        </div>
      ) : (
        /* Admissions Form */
        <Card className="max-w-3xl">
          <CardHeader>
            <div>
              <CardTitle>Deterministic Seat Admission & Booking</CardTitle>
              <CardDescription>
                Reserves a physical desk for the chosen shift and dates with guaranteed zero double-booking
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAdmissionSubmit} className="space-y-5 text-xs">
              {admissionError && (
                <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 font-medium">
                  {admissionError}
                </div>
              )}
              {admissionSuccess && (
                <div className="p-3.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 font-medium">
                  {admissionSuccess}
                </div>
              )}

              {/* Student & Desk */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Select Registered Student *</label>
                  <select
                    required
                    value={admissionForm.student_id}
                    onChange={(e) => setAdmissionForm({ ...admissionForm, student_id: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">-- Choose Student --</option>
                    {students.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.full_name} ({s.student_code} - {s.mobile_number || s.mobile})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Physical Desk Number (1 to 100) *</label>
                  <select
                    required
                    value={admissionForm.seat_id}
                    onChange={(e) => setAdmissionForm({ ...admissionForm, seat_id: Number(e.target.value) })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 font-bold"
                  >
                    {allSeats.map((s) => (
                      <option key={s.id} value={s.id} disabled={!s.is_active}>
                        Desk #{s.seat_number} {!s.is_active ? '⚠️ (Under Maintenance)' : s.has_power_outlet ? '• Power Socket' : ''}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Shift & Pricing */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Operating Shift *</label>
                  <select
                    value={admissionForm.shift_id}
                    onChange={(e) => setAdmissionForm({ ...admissionForm, shift_id: Number(e.target.value) })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {shifts.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name} (Base Fee: ₹{s.base_fee})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Concession / Discount (₹)</label>
                  <input
                    type="number"
                    min={0}
                    max={shiftBaseFee}
                    value={admissionForm.discount_amount || 0}
                    onChange={(e) =>
                      setAdmissionForm({
                        ...admissionForm,
                        discount_amount: Number(e.target.value),
                        initial_payment_amount: Math.max(0, shiftBaseFee - Number(e.target.value)),
                      })
                    }
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Dates */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Start Date *</label>
                  <input
                    type="date"
                    required
                    value={admissionForm.start_date}
                    onChange={(e) => setAdmissionForm({ ...admissionForm, start_date: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">End Date (Inclusive) *</label>
                  <input
                    type="date"
                    required
                    value={admissionForm.end_date}
                    onChange={(e) => setAdmissionForm({ ...admissionForm, end_date: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Pricing Summary Strip */}
              <div className="p-3 rounded-lg bg-blue-50/70 border border-blue-200 flex items-center justify-between font-medium text-slate-800">
                <span>Base Shift Fee: ₹{shiftBaseFee.toFixed(2)}</span>
                <span>Discount: ₹{(admissionForm.discount_amount || 0).toFixed(2)}</span>
                <span className="font-bold text-blue-900 text-sm">Payable Amount: ₹{finalCalculatedFee.toFixed(2)}</span>
              </div>

              {/* Initial Payment Collection */}
              <div className="space-y-3 pt-2 border-t border-slate-200">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="collectPay"
                    checked={collectPayment}
                    onChange={(e) => setCollectPayment(e.target.checked)}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <label htmlFor="collectPay" className="font-bold text-slate-800 cursor-pointer">
                    Collect Initial Installment at Admission Time
                  </label>
                </div>

                {collectPayment && (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="space-y-1">
                      <label className="font-semibold text-slate-700">Amount Collected (₹)</label>
                      <input
                        type="number"
                        min={1}
                        max={finalCalculatedFee}
                        value={admissionForm.initial_payment_amount || 0}
                        onChange={(e) =>
                          setAdmissionForm({ ...admissionForm, initial_payment_amount: Number(e.target.value) })
                        }
                        className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="font-semibold text-slate-700">Payment Channel</label>
                      <select
                        value={admissionForm.initial_payment_method || 'CASH'}
                        onChange={(e) =>
                          setAdmissionForm({ ...admissionForm, initial_payment_method: e.target.value as any })
                        }
                        className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900"
                      >
                        <option value="CASH">CASH</option>
                        <option value="UPI">UPI</option>
                        <option value="CARD">CARD</option>
                        <option value="NET_BANKING">NET_BANKING</option>
                      </select>
                    </div>
                    <div className="space-y-1">
                      <label className="font-semibold text-slate-700">UPI / Txn Reference</label>
                      <input
                        type="text"
                        placeholder="e.g. UPI/2026/1234"
                        value={admissionForm.initial_payment_ref || ''}
                        onChange={(e) => setAdmissionForm({ ...admissionForm, initial_payment_ref: e.target.value })}
                        className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900"
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={admissionMutation.isPending}
                  className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-xs transition-colors flex items-center gap-2 disabled:opacity-70"
                >
                  {admissionMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : null}
                  <span>Execute Admission & Confirm Desk</span>
                </button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Renewal Modal */}
      <Modal
        isOpen={!!selectedRenewMem}
        onClose={() => setSelectedRenewMem(null)}
        title="Subscription Renewal Desk"
        subtitle={selectedRenewMem ? `Student: ${selectedRenewMem.student_name} • Current Desk: #${selectedRenewMem.seat_number}` : ''}
        maxWidth="lg"
      >
        <form onSubmit={handleRenewSubmit} className="space-y-4 text-xs">
          {renewError && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 font-medium">
              {renewError}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="font-semibold text-slate-700">Renewal Start Date *</label>
              <input
                type="date"
                required
                value={renewForm.start_date}
                onChange={(e) => setRenewForm({ ...renewForm, start_date: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900"
              />
            </div>
            <div className="space-y-1">
              <label className="font-semibold text-slate-700">Renewal End Date *</label>
              <input
                type="date"
                required
                value={renewForm.end_date}
                onChange={(e) => setRenewForm({ ...renewForm, end_date: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900"
              />
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="retainSeat"
                checked={retainSeat}
                onChange={(e) => setRetainSeat(e.target.checked)}
              />
              <label htmlFor="retainSeat" className="font-semibold text-slate-800">
                Retain Same Desk (#{selectedRenewMem?.seat_number})
              </label>
            </div>
            {!retainSeat && (
              <div className="space-y-1 pl-5">
                <label className="font-semibold text-slate-700">Migrate to New Seat #</label>
                <select
                  value={renewForm.target_seat_id || 1}
                  onChange={(e) => setRenewForm({ ...renewForm, target_seat_id: Number(e.target.value) })}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-900 font-bold"
                >
                  {allSeats.map((s) => (
                    <option key={s.id} value={s.id} disabled={!s.is_active}>
                      Desk #{s.seat_number} {!s.is_active ? '⚠️ (Under Maintenance)' : ''}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="pt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setSelectedRenewMem(null)}
              className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={renewMutation.isPending}
              className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold flex items-center gap-2"
            >
              {renewMutation.isPending ? <Loader2 size={13} className="animate-spin" /> : null}
              <span>Confirm Renewal</span>
            </button>
          </div>
        </form>
      </Modal>

      {/* Cancellation Modal */}
      <Modal
        isOpen={!!selectedCancelMem}
        onClose={() => setSelectedCancelMem(null)}
        title="Confirm Early Subscription Cancellation"
        subtitle={selectedCancelMem ? `Seat #${selectedCancelMem.seat_number} • ${selectedCancelMem.student_name}` : ''}
        maxWidth="md"
      >
        <form onSubmit={handleCancelSubmit} className="space-y-4 text-xs">
          {cancelError && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 font-medium">
              {cancelError}
            </div>
          )}

          <div className="p-3.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 leading-relaxed">
            <AlertCircle size={16} className="inline mr-1 text-amber-600" />
            <span>Cancelling this subscription will immediately free the physical desk back into the inventory pool for other bookings.</span>
          </div>

          <div className="space-y-1">
            <label className="font-semibold text-slate-700">Mandatory Cancellation Reason *</label>
            <input
              type="text"
              required
              placeholder="e.g. Relocating, Exam completed, Medical leave"
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900"
            />
          </div>

          <div className="pt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setSelectedCancelMem(null)}
              className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold"
            >
              Dismiss
            </button>
            <button
              type="submit"
              disabled={cancelMutation.isPending}
              className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-semibold flex items-center gap-2"
            >
              {cancelMutation.isPending ? <Loader2 size={13} className="animate-spin" /> : null}
              <span>Confirm & Terminate Subscription</span>
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
