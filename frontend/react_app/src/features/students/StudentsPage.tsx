import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { studentsApi } from '../../api/students'
import { membershipsApi } from '../../api/memberships'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/Card'
import { Badge } from '../../components/ui/Badge'
import { Modal } from '../../components/shared/Modal'
import { ErrorState } from '../../components/shared/ErrorState'
import { EmptyState } from '../../components/shared/EmptyState'
import { formatDate, formatCurrencyINR } from '../../lib/utils'
import type { Student, StudentCreatePayload, StudentUpdatePayload } from '../../types'
import {
  Search,
  UserPlus,
  Eye,
  Edit2,
  FileDown,
  Phone,
  Mail,
  MapPin,
  Calendar,
  ShieldAlert,
  Loader2,
} from 'lucide-react'

export const StudentsPage: React.FC = () => {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'directory' | 'register'>('directory')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null)
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)

  // Registration Form State
  const [regForm, setRegForm] = useState<StudentCreatePayload>({
    full_name: '',
    mobile: '',
    email: '',
    id_proof_type: 'Aadhaar Card',
    id_proof_number: '',
    emergency_contact: '',
    address: '',
    notes: '',
  })
  const [regError, setRegError] = useState<string | null>(null)
  const [regSuccess, setRegSuccess] = useState<string | null>(null)

  // Edit Form State
  const [editForm, setEditForm] = useState<StudentUpdatePayload>({})
  const [editError, setEditError] = useState<string | null>(null)

  // Fetch Students with search
  const {
    data: studentsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['students-list', searchQuery],
    queryFn: () => studentsApi.listStudents(searchQuery || undefined, 0, 100),
  })

  const students = studentsData?.items || []

  // Fetch Selected Student Memberships
  const { data: studentMemberships } = useQuery({
    queryKey: ['student-memberships', selectedStudent?.id],
    queryFn: () => membershipsApi.listMemberships(undefined, selectedStudent?.id),
    enabled: !!selectedStudent?.id,
  })

  // Register Student Mutation
  const registerMutation = useMutation({
    mutationFn: (payload: StudentCreatePayload) => studentsApi.createStudent(payload),
    onSuccess: (newStudent) => {
      setRegSuccess(`Aspirant ${newStudent.full_name} enrolled successfully with Code: ${newStudent.student_code}`)
      setRegError(null)
      setRegForm({
        full_name: '',
        mobile: '',
        email: '',
        id_proof_type: 'Aadhaar Card',
        id_proof_number: '',
        emergency_contact: '',
        address: '',
        notes: '',
      })
      queryClient.invalidateQueries({ queryKey: ['students-list'] })
    },
    onError: (err: any) => {
      setRegError(err.message || 'Failed to register student.')
      setRegSuccess(null)
    },
  })

  // Update Student Mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: StudentUpdatePayload }) =>
      studentsApi.updateStudent(id, payload),
    onSuccess: (updated) => {
      setSelectedStudent(updated)
      setIsEditModalOpen(false)
      queryClient.invalidateQueries({ queryKey: ['students-list'] })
    },
    onError: (err: any) => {
      setEditError(err.message || 'Failed to update student profile.')
    },
  })

  const handleRegisterSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!regForm.full_name.trim() || !regForm.mobile.trim()) {
      setRegError('Full Name and 10-digit Mobile Number are mandatory.')
      return
    }
    registerMutation.mutate(regForm)
  }

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedStudent) return
    updateMutation.mutate({ id: selectedStudent.id, payload: editForm })
  }

  const openProfile = (student: Student) => {
    setSelectedStudent(student)
    setIsProfileModalOpen(true)
  }

  const openEdit = (student: Student) => {
    setSelectedStudent(student)
    setEditForm({
      full_name: student.full_name,
      mobile: student.mobile,
      email: student.email,
      id_proof_type: student.id_proof_type,
      id_proof_number: student.id_proof_number,
      emergency_contact: student.emergency_contact,
      address: student.address,
      notes: student.notes,
      status: student.status,
    })
    setIsEditModalOpen(true)
  }

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-200">
        <button
          onClick={() => setActiveTab('directory')}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${
            activeTab === 'directory'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          Student Directory
        </button>
        <button
          onClick={() => setActiveTab('register')}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
            activeTab === 'register'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          <UserPlus size={14} />
          <span>Enroll New Aspirant</span>
        </button>
      </div>

      {activeTab === 'directory' ? (
        <div className="space-y-4">
          {/* Search & Export Strip */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="relative flex-1 max-w-md">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search by student name or 10-digit mobile..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <a
              href={studentsApi.exportStudentsCsv()}
              target="_blank"
              rel="noreferrer"
              className="px-3.5 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors flex items-center justify-center gap-1.5 shrink-0"
            >
              <FileDown size={14} />
              <span>Export CSV</span>
            </a>
          </div>

          {/* Table */}
          <Card>
            <CardContent className="p-0 overflow-x-auto">
              {isLoading ? (
                <div className="py-20 text-center text-xs text-slate-400">Loading student directory...</div>
              ) : error ? (
                <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
              ) : students.length === 0 ? (
                <EmptyState
                  title="No students found"
                  description="No registered student records matched your search query."
                  action={{ label: 'Enroll Student', onClick: () => setActiveTab('register') }}
                />
              ) : (
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Student Code</th>
                      <th className="py-3 px-4">Full Name</th>
                      <th className="py-3 px-4">Mobile</th>
                      <th className="py-3 px-4">Email</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Enrolled On</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
                    {students.map((student) => (
                      <tr key={student.id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-3 px-4 font-mono font-semibold text-blue-600">{student.student_code}</td>
                        <td className="py-3 px-4 font-bold text-slate-900">{student.full_name}</td>
                        <td className="py-3 px-4 font-mono text-slate-600">{student.mobile_number || student.mobile}</td>
                        <td className="py-3 px-4 text-slate-500">{student.email || '—'}</td>
                        <td className="py-3 px-4">
                          <Badge variant={student.status === 'ACTIVE' ? 'success' : 'danger'}>{student.status}</Badge>
                        </td>
                        <td className="py-3 px-4">{formatDate(student.created_at)}</td>
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => openProfile(student)}
                              className="p-1.5 rounded-md hover:bg-slate-100 text-slate-600 hover:text-blue-600 transition-colors"
                              title="View KYC Profile & Subscriptions"
                            >
                              <Eye size={15} />
                            </button>
                            <button
                              onClick={() => openEdit(student)}
                              className="p-1.5 rounded-md hover:bg-slate-100 text-slate-600 hover:text-amber-600 transition-colors"
                              title="Edit Student Info"
                            >
                              <Edit2 size={15} />
                            </button>
                          </div>
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
        /* Register Aspirant Form */
        <Card className="max-w-2xl">
          <CardHeader>
            <div>
              <CardTitle>Enroll New Student Aspirant</CardTitle>
              <CardDescription>Creates official student profile and assigns sequential STU-YYYY-XXXX identifier</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleRegisterSubmit} className="space-y-4">
              {regError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium">
                  {regError}
                </div>
              )}
              {regSuccess && (
                <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-700 font-medium">
                  {regSuccess}
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Full Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Rahul Sharma"
                    value={regForm.full_name}
                    onChange={(e) => setRegForm({ ...regForm, full_name: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Mobile Number (10 Digits) *</label>
                  <input
                    type="tel"
                    required
                    maxLength={15}
                    placeholder="e.g. 9876543210"
                    value={regForm.mobile}
                    onChange={(e) => setRegForm({ ...regForm, mobile: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Email Address (Optional)</label>
                  <input
                    type="email"
                    placeholder="e.g. rahul@example.com"
                    value={regForm.email || ''}
                    onChange={(e) => setRegForm({ ...regForm, email: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Emergency Contact (Optional)</label>
                  <input
                    type="tel"
                    placeholder="Guardian phone number"
                    value={regForm.emergency_contact || ''}
                    onChange={(e) => setRegForm({ ...regForm, emergency_contact: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Govt ID Proof Type</label>
                  <select
                    value={regForm.id_proof_type || ''}
                    onChange={(e) => setRegForm({ ...regForm, id_proof_type: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Aadhaar Card">Aadhaar Card</option>
                    <option value="PAN Card">PAN Card</option>
                    <option value="Driving License">Driving License</option>
                    <option value="Passport">Passport</option>
                    <option value="College ID">College ID</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">ID Document Number</label>
                  <input
                    type="text"
                    placeholder="e.g. 1234-5678-9012"
                    value={regForm.id_proof_number || ''}
                    onChange={(e) => setRegForm({ ...regForm, id_proof_number: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Residential Address</label>
                <textarea
                  rows={2}
                  placeholder="Street, City, Pincode"
                  value={regForm.address || ''}
                  onChange={(e) => setRegForm({ ...regForm, address: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={registerMutation.isPending}
                  className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs transition-colors flex items-center gap-2 disabled:opacity-70"
                >
                  {registerMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : null}
                  <span>Complete Student Registration</span>
                </button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* KYC Profile Lookup Modal */}
      <Modal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        title={selectedStudent?.full_name || 'Student Profile'}
        subtitle={`Official Code: ${selectedStudent?.student_code}`}
        maxWidth="lg"
      >
        {selectedStudent && (
          <div className="space-y-5 text-xs">
            {/* Quick Specs */}
            <div className="grid grid-cols-2 gap-3 p-3.5 bg-slate-50 rounded-xl border border-slate-200">
              <div>
                <p className="text-slate-400 font-semibold uppercase text-[10px]">Mobile Contact</p>
                <p className="font-mono font-semibold text-slate-900 mt-0.5">
                  {selectedStudent.mobile_number || selectedStudent.mobile}
                </p>
              </div>
              <div>
                <p className="text-slate-400 font-semibold uppercase text-[10px]">Email Address</p>
                <p className="font-medium text-slate-900 mt-0.5">{selectedStudent.email || 'Not Provided'}</p>
              </div>
              <div>
                <p className="text-slate-400 font-semibold uppercase text-[10px]">ID Proof Document</p>
                <p className="font-medium text-slate-900 mt-0.5">
                  {selectedStudent.id_proof_type || 'N/A'} - {selectedStudent.id_proof_number || 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-slate-400 font-semibold uppercase text-[10px]">Residential Address</p>
                <p className="font-medium text-slate-900 mt-0.5">{selectedStudent.address || 'Not Provided'}</p>
              </div>
            </div>

            {/* Subscriptions History */}
            <div className="space-y-2">
              <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider">
                Active & Historical Memberships
              </h4>
              {studentMemberships?.items && studentMemberships.items.length > 0 ? (
                <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
                  {studentMemberships.items.map((m) => (
                    <div key={m.id} className="p-3 flex items-center justify-between hover:bg-slate-50">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900">Seat #{m.seat_number}</span>
                          <span className="text-slate-500 font-medium">({m.shift_name})</span>
                          <Badge variant={m.status === 'ACTIVE' ? 'success' : 'neutral'}>{m.status}</Badge>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          {formatDate(m.start_date)} to {formatDate(m.end_date)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-slate-900">{formatCurrencyINR(m.final_fee)}</p>
                        <p className="text-[11px] text-slate-500">Paid: {formatCurrencyINR(m.total_paid)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 italic p-3 text-center bg-slate-50 rounded-lg">
                  No membership subscriptions on record for this student.
                </p>
              )}
            </div>
          </div>
        )}
      </Modal>

      {/* Edit Student Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Update Student Profile"
        subtitle={`Modifying profile for ${selectedStudent?.full_name}`}
        maxWidth="md"
      >
        <form onSubmit={handleEditSubmit} className="space-y-4 text-xs">
          {editError && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium">
              {editError}
            </div>
          )}

          <div className="space-y-1">
            <label className="font-semibold text-slate-700">Full Name</label>
            <input
              type="text"
              value={editForm.full_name || ''}
              onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900"
            />
          </div>

          <div className="space-y-1">
            <label className="font-semibold text-slate-700">Email Address</label>
            <input
              type="email"
              value={editForm.email || ''}
              onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900"
            />
          </div>

          <div className="space-y-1">
            <label className="font-semibold text-slate-700">Status</label>
            <select
              value={editForm.status || 'ACTIVE'}
              onChange={(e) => setEditForm({ ...editForm, status: e.target.value as any })}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-900"
            >
              <option value="ACTIVE">ACTIVE</option>
              <option value="INACTIVE">INACTIVE</option>
              <option value="BLOCKED">BLOCKED</option>
            </select>
          </div>

          <div className="pt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setIsEditModalOpen(false)}
              className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updateMutation.isPending}
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold flex items-center gap-1.5"
            >
              {updateMutation.isPending ? <Loader2 size={13} className="animate-spin" /> : null}
              <span>Save Changes</span>
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
