import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { membershipsApi } from '../../api/memberships'
import { paymentsApi } from '../../api/payments'
import { useAuth } from '../../context/AuthContext'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { Modal } from '../../components/shared/Modal'
import { ErrorState } from '../../components/shared/ErrorState'
import { EmptyState } from '../../components/shared/EmptyState'
import { formatDate, formatDateTime, formatCurrencyINR } from '../../lib/utils'
import type { Membership, Payment, PaymentCreatePayload } from '../../types'
import {
  CreditCard,
  Receipt,
  FileDown,
  ShieldBan,
  CheckCircle,
  AlertCircle,
  Loader2,
  Coins,
} from 'lucide-react'

export const PaymentsPage: React.FC = () => {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<'collect' | 'ledger' | 'void'>('collect')

  // Selected Dues Membership
  const [selectedDueMem, setSelectedDueMem] = useState<Membership | null>(null)
  const [payAmount, setPayAmount] = useState<number>(0)
  const [payMethod, setPayMethod] = useState<'CASH' | 'UPI' | 'CARD' | 'NET_BANKING'>('CASH')
  const [txnRef, setTxnRef] = useState('')
  const [payNotes, setPayNotes] = useState('')
  const [payError, setPayError] = useState<string | null>(null)
  const [issuedReceipt, setIssuedReceipt] = useState<Payment | null>(null)

  // Ledger Membership Lookup
  const [inspectMemId, setInspectMemId] = useState<string>('')

  // Void Payment State
  const [voidPaymentId, setVoidPaymentId] = useState('')
  const [voidReason, setVoidReason] = useState('')
  const [voidError, setVoidError] = useState<string | null>(null)
  const [voidSuccess, setVoidSuccess] = useState<string | null>(null)

  // Fetch Active Memberships
  const { data: membershipsData, isLoading: isMemLoading } = useQuery({
    queryKey: ['memberships-for-cashier'],
    queryFn: () => membershipsApi.listMemberships('ACTIVE', undefined, undefined, 0, 100),
  })
  const allMemberships = membershipsData?.items || []
  const dueMemberships = allMemberships.filter((m) => Number(m.due_amount) > 0)

  // Fetch Payments for Inspected Membership
  const {
    data: paymentsList = [],
    isLoading: isPaymentsLoading,
    refetch: refetchLedger,
  } = useQuery({
    queryKey: ['membership-payments', inspectMemId],
    queryFn: () => paymentsApi.listMembershipPayments(inspectMemId),
    enabled: !!inspectMemId,
  })

  // Payment Collection Mutation
  const paymentMutation = useMutation({
    mutationFn: (payload: PaymentCreatePayload) => paymentsApi.recordPayment(payload),
    onSuccess: (receipt) => {
      setIssuedReceipt(receipt)
      setPayError(null)
      queryClient.invalidateQueries({ queryKey: ['memberships-for-cashier'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
      queryClient.invalidateQueries({ queryKey: ['membership-payments'] })
    },
    onError: (err: any) => {
      setPayError(err.message || 'Payment processing failed.')
    },
  })

  // Void Mutation
  const voidMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      paymentsApi.voidPayment(id, { void_reason: reason }),
    onSuccess: () => {
      setVoidSuccess('Payment transaction marked as VOIDED and balance restored.')
      setVoidError(null)
      setVoidPaymentId('')
      setVoidReason('')
      queryClient.invalidateQueries({ queryKey: ['memberships-for-cashier'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
      queryClient.invalidateQueries({ queryKey: ['membership-payments'] })
    },
    onError: (err: any) => {
      setVoidError(err.message || 'Void transaction failed.')
      setVoidSuccess(null)
    },
  })

  const handleSelectDueMem = (m: Membership) => {
    setSelectedDueMem(m)
    setPayAmount(Number(m.due_amount))
    setPayError(null)
    setIssuedReceipt(null)
  }

  const handlePaymentSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedDueMem) return
    if (payAmount <= 0) {
      setPayError('Payment amount must be greater than zero.')
      return
    }

    const payload: PaymentCreatePayload = {
      membership_id: selectedDueMem.id,
      student_id: selectedDueMem.student_id,
      amount: payAmount,
      payment_method: payMethod,
      transaction_ref: txnRef.trim() || undefined,
      notes: payNotes.trim() || undefined,
    }

    paymentMutation.mutate(payload)
  }

  const handleVoidSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!voidPaymentId.trim() || !voidReason.trim()) {
      setVoidError('Payment ID and Void Reason are mandatory.')
      return
    }
    voidMutation.mutate({ id: voidPaymentId.trim(), reason: voidReason.trim() })
  }

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="flex items-center gap-1.5 p-1 bg-white/70 backdrop-blur-xl rounded-2xl border border-white/80 shadow-[0_4px_20px_rgb(0,0,0,0.03)] w-fit">
        <button
          onClick={() => setActiveTab('collect')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
            activeTab === 'collect'
              ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-indigo-500/20'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
          }`}
        >
          <Coins size={14} />
          <span>Collect Dues</span>
        </button>
        <button
          onClick={() => setActiveTab('ledger')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
            activeTab === 'ledger'
              ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-indigo-500/20'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
          }`}
        >
          <Receipt size={14} />
          <span>Payment Ledger</span>
        </button>
        {user?.role === 'ADMIN' && (
          <button
            onClick={() => setActiveTab('void')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'void'
                ? 'bg-gradient-to-r from-rose-600 to-red-600 text-white shadow-md shadow-rose-500/20'
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
            }`}
          >
            <ShieldBan size={14} />
            <span>Void Transaction</span>
          </button>
        )}
      </div>

      {activeTab === 'collect' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Due Accounts List */}
          <div className="lg:col-span-1 space-y-3">
            <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              Pending Dues Accounts ({dueMemberships.length})
            </h3>
            {isMemLoading ? (
              <div className="p-8 text-center text-xs text-slate-400">Loading dues...</div>
            ) : dueMemberships.length === 0 ? (
              <div className="p-8 text-center text-xs text-emerald-700 bg-emerald-50/80 rounded-2xl border border-emerald-200/80 font-bold backdrop-blur-md">
                Zero outstanding dues across all active subscriptions!
              </div>
            ) : (
              <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
                {dueMemberships.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => handleSelectDueMem(m)}
                    className={`w-full p-4 rounded-2xl border text-left transition-all cursor-pointer ${
                      selectedDueMem?.id === m.id
                        ? 'bg-indigo-50/90 border-indigo-300 shadow-sm'
                        : 'bg-white/75 backdrop-blur-xl border-white/80 hover:bg-white hover:border-slate-200 shadow-[0_4px_20px_rgb(0,0,0,0.02)]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900 text-xs">{m.student_name}</span>
                      <span className="font-black text-rose-600 text-xs">{formatCurrencyINR(m.due_amount)}</span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1 font-medium">
                      Seat #{m.seat_number} • {m.shift_name}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Payment Entry Form */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Cashier Terminal Entry</CardTitle>
                  <CardDescription>
                    {selectedDueMem
                      ? `Receiving payment for ${selectedDueMem.student_name} (Seat #${selectedDueMem.seat_number})`
                      : 'Select a pending account from the left panel to proceed'}
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                {selectedDueMem ? (
                  <form onSubmit={handlePaymentSubmit} className="space-y-4 text-xs">
                    {payError && (
                      <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 font-medium">
                        {payError}
                      </div>
                    )}

                    {/* Balance Overview */}
                    <div className="grid grid-cols-3 gap-3 p-4 bg-white/70 backdrop-blur-md rounded-2xl border border-white/90 shadow-2xs">
                      <div>
                        <p className="text-slate-400 font-bold uppercase text-[10px]">Total Contract Fee</p>
                        <p className="font-black text-slate-900 mt-0.5">{formatCurrencyINR(selectedDueMem.final_fee)}</p>
                      </div>
                      <div>
                        <p className="text-slate-400 font-bold uppercase text-[10px]">Already Paid</p>
                        <p className="font-black text-emerald-600 mt-0.5">
                          {formatCurrencyINR(selectedDueMem.total_paid)}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-400 font-bold uppercase text-[10px]">Pending Due</p>
                        <p className="font-black text-rose-600 mt-0.5">{formatCurrencyINR(selectedDueMem.due_amount)}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Payment Amount (₹) *</label>
                        <input
                          type="number"
                          required
                          min={1}
                          max={Number(selectedDueMem.due_amount)}
                          value={payAmount}
                          onChange={(e) => setPayAmount(Number(e.target.value))}
                          className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 font-bold focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>

                      <div className="space-y-1">
                        <label className="font-semibold text-slate-700">Payment Channel *</label>
                        <select
                          value={payMethod}
                          onChange={(e) => setPayMethod(e.target.value as any)}
                          className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="CASH">CASH</option>
                          <option value="UPI">UPI</option>
                          <option value="CARD">CARD</option>
                          <option value="NET_BANKING">NET_BANKING</option>
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <label className="font-semibold text-slate-700">Transaction Reference (Optional)</label>
                        <input
                          type="text"
                          placeholder="e.g. UPI/2026/0921"
                          value={txnRef}
                          onChange={(e) => setTxnRef(e.target.value)}
                          className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                        />
                      </div>

                      <div className="space-y-1">
                        <label className="font-semibold text-slate-700">Desk Remarks (Optional)</label>
                        <input
                          type="text"
                          placeholder="e.g. Second installment paid"
                          value={payNotes}
                          onChange={(e) => setPayNotes(e.target.value)}
                          className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>

                    <div className="pt-2 flex justify-end">
                      <button
                        type="submit"
                        disabled={paymentMutation.isPending}
                        className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-xs transition-colors flex items-center gap-2 disabled:opacity-70"
                      >
                        {paymentMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : null}
                        <span>Record Payment & Issue Receipt</span>
                      </button>
                    </div>
                  </form>
                ) : (
                  <div className="py-20 text-center text-slate-400 text-xs">
                    Please click an account on the left to record fee collection.
                  </div>
                )}

                {/* Issued Receipt Display */}
                {issuedReceipt && selectedDueMem && (
                  <div className="mt-6 p-5 rounded-xl bg-emerald-50/70 border border-emerald-200 text-xs space-y-3">
                    <div className="flex items-center justify-between border-b border-emerald-200 pb-2">
                      <span className="font-bold text-emerald-900 text-sm">Receipt #{issuedReceipt.receipt_number}</span>
                      <Badge variant="success">COMPLETED</Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-slate-700">
                      <div>Student: <span className="font-semibold">{selectedDueMem.student_name}</span></div>
                      <div>Desk: <span className="font-semibold">Seat #{selectedDueMem.seat_number}</span></div>
                      <div>Amount Collected: <span className="font-bold text-emerald-800">{formatCurrencyINR(issuedReceipt.amount)}</span></div>
                      <div>Channel: <span className="font-semibold">{issuedReceipt.payment_method}</span></div>
                      <div>Date: <span className="font-mono">{formatDateTime(issuedReceipt.created_at)}</span></div>
                      <div>Txn Ref: <span className="font-mono">{issuedReceipt.transaction_ref || '—'}</span></div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      ) : activeTab === 'ledger' ? (
        <div className="space-y-4">
          {/* Pick Membership */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 flex-1 max-w-lg">
              <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider shrink-0">
                Inspect Subscription:
              </span>
              <select
                value={inspectMemId}
                onChange={(e) => setInspectMemId(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Choose Membership --</option>
                {allMemberships.map((m) => (
                  <option key={m.id} value={m.id}>
                    Seat #{m.seat_number} • {m.student_name} ({m.shift_name})
                  </option>
                ))}
              </select>
            </div>
            <a
              href={paymentsApi.exportRevenueCsv()}
              target="_blank"
              rel="noreferrer"
              className="px-3.5 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors flex items-center gap-1.5 shrink-0"
            >
              <FileDown size={14} />
              <span>Export Ledger CSV</span>
            </a>
          </div>

          {/* Ledger Table */}
          <Card>
            <CardContent className="p-0 overflow-x-auto">
              {!inspectMemId ? (
                <div className="py-20 text-center text-xs text-slate-400">
                  Select a membership subscription from the dropdown above to view historical receipts.
                </div>
              ) : isPaymentsLoading ? (
                <div className="py-20 text-center text-xs text-slate-400">Loading ledger records...</div>
              ) : paymentsList.length === 0 ? (
                <EmptyState title="No transactions recorded" description="No payment entries have been logged for this membership contract." />
              ) : (
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Receipt Number</th>
                      <th className="py-3 px-4">Timestamp</th>
                      <th className="py-3 px-4">Channel</th>
                      <th className="py-3 px-4">Amount</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Txn Reference</th>
                      <th className="py-3 px-4">Void Notes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
                    {paymentsList.map((p) => (
                      <tr key={p.id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-3 px-4 font-mono font-bold text-blue-600">{p.receipt_number}</td>
                        <td className="py-3 px-4 text-slate-500">{formatDateTime(p.created_at)}</td>
                        <td className="py-3 px-4">{p.payment_method}</td>
                        <td className="py-3 px-4 font-bold text-slate-900">{formatCurrencyINR(p.amount)}</td>
                        <td className="py-3 px-4">
                          <Badge variant={p.status === 'COMPLETED' ? 'success' : 'danger'}>{p.status}</Badge>
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-500">{p.transaction_ref || '—'}</td>
                        <td className="py-3 px-4 text-rose-600 italic">{p.void_reason || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </CardContent>
          </Card>
        </div>
      ) : (
        /* Void Payment Tab (Admin Only) */
        <Card className="max-w-xl">
          <CardHeader>
            <div>
              <CardTitle>Void Erroneous Payment Transaction</CardTitle>
              <CardDescription>
                Restores the membership balance and marks the payment entry permanently VOIDED for audit compliance.
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleVoidSubmit} className="space-y-4 text-xs">
              {voidError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 font-medium">
                  {voidError}
                </div>
              )}
              {voidSuccess && (
                <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 font-medium">
                  {voidSuccess}
                </div>
              )}

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Payment UUID *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 3fa85f64-5717-4562-b3fc-2c963f66afa6"
                  value={voidPaymentId}
                  onChange={(e) => setVoidPaymentId(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 font-mono"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Mandatory Void Reason *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Incorrect amount recorded, duplicate entry"
                  value={voidReason}
                  onChange={(e) => setVoidReason(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900"
                />
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={voidMutation.isPending}
                  className="px-5 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-semibold flex items-center gap-2 disabled:opacity-70"
                >
                  {voidMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : null}
                  <span>Execute Transaction Void</span>
                </button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
