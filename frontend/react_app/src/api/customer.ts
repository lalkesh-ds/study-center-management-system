import { apiClient } from './client'

export interface CustomerDashboardData {
  has_active_membership: boolean
  active_membership_id?: string | null
  seat_number?: number | null
  shift_name?: string | null
  membership_status?: string | null
  days_remaining?: number | null
  total_fee?: number | null
  total_paid?: number | null
  due_amount?: number | null
  is_checked_in: boolean
  current_check_in_time?: string | null
}

export interface CustomerProfileData {
  id: string
  student_id?: string | null
  username: string
  email: string
  mobile?: string | null
  full_name: string
  role: string
  student_code?: string | null
  id_proof_type?: string | null
  id_proof_number?: string | null
  emergency_contact?: string | null
  address?: string | null
  created_at: string
}

export interface CustomerProfileUpdatePayload {
  full_name?: string
  email?: string
  mobile?: string
  address?: string
  emergency_contact?: string
}

export const customerApi = {
  getDashboard: async (): Promise<CustomerDashboardData> => {
    const { data } = await apiClient.get<CustomerDashboardData>('/customer/dashboard')
    return data
  },
  getProfile: async (): Promise<CustomerProfileData> => {
    const { data } = await apiClient.get<CustomerProfileData>('/customer/profile')
    return data
  },
  updateProfile: async (payload: CustomerProfileUpdatePayload): Promise<CustomerProfileData> => {
    const { data } = await apiClient.patch<CustomerProfileData>('/customer/profile', payload)
    return data
  },
  getMemberships: async (): Promise<any[]> => {
    const { data } = await apiClient.get<any[]>('/customer/membership')
    return data
  },
  getPayments: async (): Promise<any[]> => {
    const { data } = await apiClient.get<any[]>('/customer/payments')
    return data
  },
  getAttendance: async (): Promise<any[]> => {
    const { data } = await apiClient.get<any[]>('/customer/attendance')
    return data
  },
}
