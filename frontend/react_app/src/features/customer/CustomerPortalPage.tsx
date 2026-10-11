import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { customerApi, CustomerProfileUpdatePayload } from '../../api/customer'
import { useAuth } from '../../context/AuthContext'
import {
  Armchair,
  Calendar,
  Clock,
  CreditCard,
  CheckCircle2,
  AlertCircle,
  User,
  Shield,
  Loader2,
  LogOut,
  Sparkles,
  Save,
} from 'lucide-react'
import { toast } from 'sonner'

export const CustomerPortalPage: React.FC = () => {
  const { user, logout } = useAuth()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'overview' | 'memberships' | 'payments' | 'attendance' | 'profile'>('overview')

  // Fetch Dashboard summary
  const { data: dashboard, isLoading: dashLoading } = useQuery({
    queryKey: ['customerDashboard'],
    queryFn: customerApi.getDashboard,
  })

  // Fetch Profile
  const { data: profile, isLoading: profLoading } = useQuery({
    queryKey: ['customerProfile'],
    queryFn: customerApi.getProfile,
  })

  // Fetch Memberships
  const { data: memberships = [] } = useQuery({
    queryKey: ['customerMemberships'],
    queryFn: customerApi.getMemberships,
    enabled: activeTab === 'memberships',
  })

  // Fetch Payments
  const { data: payments = [] } = useQuery({
    queryKey: ['customerPayments'],
    queryFn: customerApi.getPayments,
    enabled: activeTab === 'payments',
  })

  // Fetch Attendance
  const { data: attendance = [] } = useQuery({
    queryKey: ['customerAttendance'],
    queryFn: customerApi.getAttendance,
    enabled: activeTab === 'attendance',
  })

  // Profile Form state
  const [editProfile, setEditProfile] = useState<CustomerProfileUpdatePayload>({
    full_name: '',
    email: '',
    mobile: '',
    address: '',
    emergency_contact: '',
  })
  const [formInitialized, setFormInitialized] = useState(false)

  if (profile && !formInitialized) {
    setEditProfile({
      full_name: profile.full_name || '',
      email: profile.email || '',
      mobile: profile.mobile || '',
      address: profile.address || '',
      emergency_contact: profile.emergency_contact || '',
    })
    setFormInitialized(true)
  }

  const updateProfileMutation = useMutation({
    mutationFn: customerApi.updateProfile,
    onSuccess: (updated) => {
      toast.success('Profile updated successfully!')
      queryClient.setQueryData(['customerProfile'], updated)
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to update profile.')
    },
  })

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateProfileMutation.mutate(editProfile)
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 px-4 sm:px-8 py-3.5 flex items-center justify-between shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-base shadow-xs">
            SL
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-900 leading-tight">Smart Study Center</h1>
            <p className="text-xs text-slate-500">Student Self-Service Portal</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex flex-col text-right">
            <span className="text-xs font-semibold text-slate-900">{user?.full_name}</span>
            <span className="text-[11px] text-slate-500">Code: {profile?.student_code || 'Enrolled'}</span>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-700 text-xs font-semibold transition-all cursor-pointer"
          >
            <LogOut size={14} />
            <span>Sign Out</span>
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Navigation Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-1 border-b border-slate-200 text-sm">
          {[
            { id: 'overview', label: 'My Desk & Dues' },
            { id: 'memberships', label: 'My Subscriptions' },
            { id: 'payments', label: 'Payment Receipts' },
            { id: 'attendance', label: 'Attendance History' },
            { id: 'profile', label: 'My Profile' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 font-semibold text-xs rounded-lg transition-all cursor-pointer ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab 1: Overview */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {dashLoading ? (
              <div className="py-20 flex justify-center">
                <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
              </div>
            ) : dashboard?.has_active_membership ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {/* Desk Card */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Allocated Desk</span>
                    <div className="p-2 rounded-xl bg-blue-50 text-blue-600">
                      <Armchair size={20} />
                    </div>
                  </div>
                  <div>
                    <div className="text-3xl font-extrabold text-slate-900">Desk #{dashboard.seat_number}</div>
                    <p className="text-xs text-slate-500 mt-1 font-medium">Shift: {dashboard.shift_name}</p>
                  </div>
                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className="text-slate-600">Validity:</span>
                    <span className="font-semibold text-emerald-600">{dashboard.days_remaining} Days Left</span>
                  </div>
                </div>

                {/* Financial Summary */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Fees & Balance</span>
                    <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
                      <CreditCard size={20} />
                    </div>
                  </div>
                  <div>
                    <div className="text-3xl font-extrabold text-slate-900">
                      ₹{dashboard.due_amount !== undefined ? Number(dashboard.due_amount).toFixed(2) : '0.00'}
                    </div>
                    <p className="text-xs text-slate-500 mt-1 font-medium">
                      Total Fee: ₹{dashboard.total_fee} | Paid: ₹{dashboard.total_paid}
                    </p>
                  </div>
                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className="text-slate-600">Payment Status:</span>
                    <span
                      className={`font-semibold px-2 py-0.5 rounded-full text-[10px] ${
                        Number(dashboard.due_amount) === 0
                          ? 'bg-emerald-50 text-emerald-700'
                          : 'bg-amber-50 text-amber-700'
                      }`}
                    >
                      {Number(dashboard.due_amount) === 0 ? 'CLEARED' : 'BALANCE DUE'}
                    </span>
                  </div>
                </div>

                {/* Today's Attendance */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Today's Check-In</span>
                    <div className="p-2 rounded-xl bg-purple-50 text-purple-600">
                      <Clock size={20} />
                    </div>
                  </div>
                  <div>
                    <div className="text-3xl font-extrabold text-slate-900">
                      {dashboard.is_checked_in ? 'Present' : 'Not In Desk'}
                    </div>
                    <p className="text-xs text-slate-500 mt-1 font-medium">
                      {dashboard.current_check_in_time
                        ? `Checked in at ${new Date(dashboard.current_check_in_time).toLocaleTimeString()}`
                        : 'Web / Kiosk biometric ready'}
                    </p>
                  </div>
                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className="text-slate-600">Kiosk Sync:</span>
                    <span className="font-semibold text-slate-900">Automatic</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center space-y-3">
                <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
                  <Sparkles size={24} />
                </div>
                <h3 className="text-base font-bold text-slate-900">No Active Subscription Found</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  You are registered in the study center directory. Please visit the front-desk counter to choose your preferred physical seat (1-100) and shift to activate your desk.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Subscriptions */}
        {activeTab === 'memberships' && (
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="p-5 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900">Membership Subscriptions</h2>
              <p className="text-xs text-slate-500 mt-0.5">Historical and active seat allocations</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 border-b border-slate-100 uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="p-3.5">Seat #</th>
                    <th className="p-3.5">Shift</th>
                    <th className="p-3.5">Period</th>
                    <th className="p-3.5">Fee</th>
                    <th className="p-3.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {memberships.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="p-8 text-center text-slate-400">
                        No subscription records found.
                      </td>
                    </tr>
                  ) : (
                    memberships.map((m: any) => (
                      <tr key={m.id} className="hover:bg-slate-50">
                        <td className="p-3.5 font-bold text-slate-900">Desk #{m.seat_number}</td>
                        <td className="p-3.5">{m.shift_name}</td>
                        <td className="p-3.5">
                          {m.start_date} to {m.end_date}
                        </td>
                        <td className="p-3.5 font-semibold text-slate-900">₹{m.final_fee}</td>
                        <td className="p-3.5">
                          <span
                            className={`px-2 py-0.5 rounded-full font-semibold text-[10px] ${
                              m.status === 'ACTIVE'
                                ? 'bg-emerald-50 text-emerald-700'
                                : 'bg-slate-100 text-slate-600'
                            }`}
                          >
                            {m.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Payments */}
        {activeTab === 'payments' && (
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="p-5 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900">Transaction Receipts</h2>
              <p className="text-xs text-slate-500 mt-0.5">Verified fee collections and cashier receipts</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 border-b border-slate-100 uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="p-3.5">Receipt #</th>
                    <th className="p-3.5">Amount</th>
                    <th className="p-3.5">Method</th>
                    <th className="p-3.5">Date</th>
                    <th className="p-3.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {payments.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="p-8 text-center text-slate-400">
                        No transactions recorded.
                      </td>
                    </tr>
                  ) : (
                    payments.map((p: any) => (
                      <tr key={p.id} className="hover:bg-slate-50">
                        <td className="p-3.5 font-mono font-bold text-blue-600">{p.receipt_number}</td>
                        <td className="p-3.5 font-bold text-slate-900">₹{p.amount}</td>
                        <td className="p-3.5">{p.payment_method}</td>
                        <td className="p-3.5">{new Date(p.created_at).toLocaleDateString()}</td>
                        <td className="p-3.5">
                          <span className="px-2 py-0.5 rounded-full font-semibold text-[10px] bg-emerald-50 text-emerald-700">
                            {p.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 4: Attendance */}
        {activeTab === 'attendance' && (
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="p-5 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900">Attendance Log</h2>
              <p className="text-xs text-slate-500 mt-0.5">Daily biometric and kiosk verification history</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 border-b border-slate-100 uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="p-3.5">Date</th>
                    <th className="p-3.5">Check In</th>
                    <th className="p-3.5">Check Out</th>
                    <th className="p-3.5">Duration</th>
                    <th className="p-3.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {attendance.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="p-8 text-center text-slate-400">
                        No attendance logs recorded.
                      </td>
                    </tr>
                  ) : (
                    attendance.map((a: any) => (
                      <tr key={a.id} className="hover:bg-slate-50">
                        <td className="p-3.5 font-semibold text-slate-900">{a.attendance_date}</td>
                        <td className="p-3.5">{new Date(a.check_in).toLocaleTimeString()}</td>
                        <td className="p-3.5">
                          {a.check_out ? new Date(a.check_out).toLocaleTimeString() : 'In Progress'}
                        </td>
                        <td className="p-3.5">{a.duration_hours ? `${a.duration_hours} hrs` : '-'}</td>
                        <td className="p-3.5">
                          <span className="px-2 py-0.5 rounded-full font-semibold text-[10px] bg-blue-50 text-blue-700">
                            {a.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 5: Profile */}
        {activeTab === 'profile' && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs max-w-2xl">
            <div className="border-b border-slate-100 pb-4 mb-5">
              <h2 className="text-sm font-bold text-slate-900">Student Contact Details</h2>
              <p className="text-xs text-slate-500 mt-0.5">Keep your registered mobile and address updated</p>
            </div>

            <form onSubmit={handleProfileSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Full Name</label>
                  <input
                    type="text"
                    value={editProfile.full_name || ''}
                    onChange={(e) => setEditProfile((prev) => ({ ...prev, full_name: e.target.value }))}
                    className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none text-slate-900"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Mobile Number</label>
                  <input
                    type="tel"
                    value={editProfile.mobile || ''}
                    onChange={(e) => setEditProfile((prev) => ({ ...prev, mobile: e.target.value }))}
                    className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none text-slate-900"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Email Address</label>
                  <input
                    type="email"
                    value={editProfile.email || ''}
                    onChange={(e) => setEditProfile((prev) => ({ ...prev, email: e.target.value }))}
                    className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none text-slate-900"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Emergency Contact</label>
                  <input
                    type="tel"
                    value={editProfile.emergency_contact || ''}
                    onChange={(e) => setEditProfile((prev) => ({ ...prev, emergency_contact: e.target.value }))}
                    placeholder="Guardian mobile"
                    className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none text-slate-900"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Residential Address</label>
                <textarea
                  rows={2}
                  value={editProfile.address || ''}
                  onChange={(e) => setEditProfile((prev) => ({ ...prev, address: e.target.value }))}
                  className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none text-slate-900"
                />
              </div>

              <button
                type="submit"
                disabled={updateProfileMutation.isPending}
                className="py-2.5 px-5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-70"
              >
                {updateProfileMutation.isPending ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Save size={14} />
                )}
                <span>Save Profile Changes</span>
              </button>
            </form>
          </div>
        )}
      </main>
    </div>
  )
}
