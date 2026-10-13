import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { attendanceApi } from '../../api/attendance'
import { studentsApi } from '../../api/students'
import { membershipsApi } from '../../api/memberships'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { ErrorState } from '../../components/shared/ErrorState'
import { EmptyState } from '../../components/shared/EmptyState'
import { formatTime, formatDate } from '../../lib/utils'
import type { Attendance, Student, Membership } from '../../types'
import {
  Clock,
  Search,
  LogIn,
  LogOut,
  Calendar,
  UserCheck,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Users,
} from 'lucide-react'

export const AttendancePage: React.FC = () => {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'terminal' | 'roster'>('terminal')
  const [searchMobileOrName, setSearchMobileOrName] = useState('')
  const [rosterDate, setRosterDate] = useState(() => new Date().toISOString().split('T')[0])

  // Front-Desk Verification State
  const [matchedStudent, setMatchedStudent] = useState<Student | null>(null)
  const [activeMembership, setActiveMembership] = useState<Membership | null>(null)
  const [searchMessage, setSearchMessage] = useState<string | null>(null)

  // Daily Attendance Query
  const {
    data: dailyRoster = [],
    isLoading: isRosterLoading,
    error: rosterError,
    refetch: refetchRoster,
  } = useQuery({
    queryKey: ['attendance-roster', rosterDate],
    queryFn: () => attendanceApi.listDailyAttendance(rosterDate),
  })

  // Check-In Mutation
  const checkInMutation = useMutation({
    mutationFn: (payload: { student_id: string; membership_id: string }) =>
      attendanceApi.checkIn({
        student_id: payload.student_id,
        membership_id: payload.membership_id,
        source: 'MANUAL_STAFF',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance-roster'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
      setSearchMessage('Student checked in successfully!')
    },
    onError: (err: any) => {
      setSearchMessage(`Check-in rejected: ${err.message}`)
    },
  })

  // Check-Out Mutation
  const checkOutMutation = useMutation({
    mutationFn: (attendanceId: string) => attendanceApi.checkOut(attendanceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance-roster'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
      setSearchMessage('Student checked out successfully!')
    },
    onError: (err: any) => {
      setSearchMessage(`Check-out failed: ${err.message}`)
    },
  })

  const handleStudentSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchMobileOrName.trim()) return

    setMatchedStudent(null)
    setActiveMembership(null)
    setSearchMessage(null)

    try {
      const res = await studentsApi.listStudents(searchMobileOrName.trim(), 0, 5)
      const found = res.items?.[0]
      if (!found) {
        setSearchMessage('No registered student matched your query.')
        return
      }

      setMatchedStudent(found)

      // Look up student's active memberships
      const memRes = await membershipsApi.listMemberships('ACTIVE', found.id)
      const todayStr = new Date().toISOString().split('T')[0]
      const validMem = memRes.items.find((m) => m.start_date <= todayStr && m.end_date >= todayStr)

      if (validMem) {
        setActiveMembership(validMem)
      } else {
        setSearchMessage('Student found, but has no active membership subscription for today.')
      }
    } catch (err: any) {
      setSearchMessage(`Search error: ${err.message}`)
    }
  }

  // Check if matched student already has an open log today
  const currentStudentRecord = matchedStudent
    ? dailyRoster.find((r) => r.student_id === matchedStudent.id)
    : null

  // Roster stats
  const totalPresent = dailyRoster.filter((r) => r.status === 'PRESENT').length
  const totalDeparted = dailyRoster.filter((r) => r.status === 'CHECKED_OUT').length

  return (
    <div className="space-y-6">
      {/* Tab Navigation Pill Bar */}
      <div className="flex items-center gap-1.5 p-1 bg-white/70 backdrop-blur-xl rounded-2xl border border-white/80 shadow-[0_4px_20px_rgb(0,0,0,0.03)] w-fit">
        <button
          onClick={() => setActiveTab('terminal')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
            activeTab === 'terminal'
              ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-indigo-500/20'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
          }`}
        >
          <LogIn size={14} />
          <span>Rapid Check-In / Check-Out Terminal</span>
        </button>
        <button
          onClick={() => setActiveTab('roster')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
            activeTab === 'roster'
              ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-indigo-500/20'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'
          }`}
        >
          <Calendar size={14} />
          <span>Daily Attendance Roster ({dailyRoster.length})</span>
        </button>
      </div>

      {activeTab === 'terminal' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
          {/* Search Box */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Student Identification</CardTitle>
                <CardDescription>Enter mobile number or name to verify today's shift allocation</CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleStudentSearch} className="space-y-4 text-xs">
                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Mobile or Aspirant Name *</label>
                  <div className="relative">
                    <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      required
                      placeholder="e.g. 9876543210 or Rahul"
                      value={searchMobileOrName}
                      onChange={(e) => setSearchMobileOrName(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200/90 bg-white/90 text-xs font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-2xs"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs shadow-md shadow-indigo-500/20 transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-[0.99]"
                >
                  <Search size={14} />
                  <span>Lookup Student Account</span>
                </button>
              </form>
            </CardContent>
          </Card>

          {/* Action Box */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Attendance Action Terminal</CardTitle>
                <CardDescription>Front-desk entry/exit authorization</CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              {matchedStudent ? (
                <div className="space-y-4 text-xs">
                  {/* Student Profile Card */}
                  <div className="p-4 bg-white/70 backdrop-blur-md rounded-2xl border border-white/90 shadow-2xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-black text-slate-900 text-sm">{matchedStudent.full_name}</span>
                      <span className="font-mono font-bold text-indigo-600">{matchedStudent.student_code}</span>
                    </div>
                    <p className="text-slate-600 font-medium">Mobile: {matchedStudent.mobile_number || matchedStudent.mobile}</p>

                    {activeMembership ? (
                      <div className="p-2.5 rounded-xl bg-emerald-50/80 border border-emerald-200/80 text-emerald-800 font-bold flex items-center justify-between">
                        <span>
                          Assigned: <strong>Seat #{activeMembership.seat_number}</strong> ({activeMembership.shift_name})
                        </span>
                        <Badge variant="success">ACTIVE</Badge>
                      </div>
                    ) : (
                      <div className="p-2.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 font-medium">
                        No active subscription booked for today.
                      </div>
                    )}
                  </div>

                  {searchMessage && (
                    <div className="p-3.5 rounded-xl bg-blue-50 border border-blue-200 text-blue-700 font-medium">
                      {searchMessage}
                    </div>
                  )}

                  {/* Actions */}
                  {activeMembership && (
                    <div>
                      {!currentStudentRecord ? (
                        <button
                          disabled={checkInMutation.isPending}
                          onClick={() =>
                            checkInMutation.mutate({
                              student_id: matchedStudent.id,
                              membership_id: activeMembership.id,
                            })
                          }
                          className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-[0.99]"
                        >
                          {checkInMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : <LogIn size={16} />}
                          <span>Record Check-In (Student Arrival)</span>
                        </button>
                      ) : currentStudentRecord.status === 'PRESENT' ? (
                        <button
                          disabled={checkOutMutation.isPending}
                          onClick={() => checkOutMutation.mutate(currentStudentRecord.id)}
                          className="w-full py-3.5 px-4 rounded-2xl bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white font-bold text-xs shadow-lg shadow-rose-500/20 transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-[0.99]"
                        >
                          {checkOutMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : <LogOut size={16} />}
                          <span>Record Check-Out (Student Departure)</span>
                        </button>
                      ) : (
                        <div className="p-4 rounded-xl bg-slate-100 text-center font-semibold text-slate-700">
                          Student has already checked out today ({currentStudentRecord.duration_hours || 0} hrs studied).
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="py-16 text-center text-xs text-slate-400">
                  {searchMessage ? (
                    <p className="text-rose-600 font-medium">{searchMessage}</p>
                  ) : (
                    'Search for a student using the left panel to execute entry/exit logging.'
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      ) : (
        /* Daily Roster View */
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 bg-white/75 backdrop-blur-xl p-4 sm:p-5 rounded-2xl border border-white/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
            <div className="flex items-center gap-2">
              <Calendar size={18} className="text-indigo-600" />
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Roster Date:</span>
              <input
                type="date"
                value={rosterDate}
                onChange={(e) => setRosterDate(e.target.value)}
                className="px-3 py-1.5 rounded-xl border border-slate-200/90 bg-white/90 text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-2xs"
              />
            </div>

            <div className="flex items-center gap-4 text-xs bg-white/60 backdrop-blur-md px-3.5 py-1.5 rounded-xl border border-white">
              <span className="text-slate-600 font-semibold">Total Logs: <strong className="text-slate-900 font-black">{dailyRoster.length}</strong></span>
              <span className="text-emerald-700 font-bold">Currently in Center: <strong className="text-emerald-800 font-black">{totalPresent}</strong></span>
              <span className="text-slate-500 font-semibold">Departed: <strong className="text-slate-700 font-black">{totalDeparted}</strong></span>
            </div>
          </div>

          <Card>
            <CardContent className="p-0 overflow-x-auto">
              {isRosterLoading ? (
                <div className="py-20 text-center text-xs text-slate-400">Loading daily attendance roster...</div>
              ) : rosterError ? (
                <ErrorState message={(rosterError as Error).message} onRetry={() => refetchRoster()} />
              ) : dailyRoster.length === 0 ? (
                <EmptyState title="No attendance logs" description={`Zero attendance check-ins logged for ${rosterDate}.`} />
              ) : (
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50/80 border-b border-slate-100 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
                    <tr>
                      <th className="py-3 px-4">Student</th>
                      <th className="py-3 px-4">Desk</th>
                      <th className="py-3 px-4">Shift</th>
                      <th className="py-3 px-4">Check-In Time</th>
                      <th className="py-3 px-4">Check-Out Time</th>
                      <th className="py-3 px-4">Duration</th>
                      <th className="py-3 px-4">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
                    {dailyRoster.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="py-3.5 px-4 font-bold text-slate-900">{r.student_name || 'Aspirant'}</td>
                        <td className="py-3.5 px-4 font-bold text-indigo-600">Seat #{r.seat_number || r.seat_id || '—'}</td>
                        <td className="py-3.5 px-4 text-slate-600">{r.shift_name || '—'}</td>
                        <td className="py-3.5 px-4 font-mono font-medium text-slate-700">{r.check_in ? r.check_in.substring(11, 19) : '—'}</td>
                        <td className="py-3.5 px-4 font-mono font-medium text-slate-700">{r.check_out ? r.check_out.substring(11, 19) : '—'}</td>
                        <td className="py-3.5 px-4 text-slate-600">{r.duration_hours !== null && r.duration_hours !== undefined ? `${r.duration_hours} hrs` : 'In Progress'}</td>
                        <td className="py-3.5 px-4">
                          <Badge variant={r.status === 'PRESENT' ? 'success' : 'neutral'}>
                            {r.status === 'PRESENT' ? 'In Facility' : 'Departed'}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
