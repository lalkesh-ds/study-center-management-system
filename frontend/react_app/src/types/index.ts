// Common Pagination
export interface PaginationMeta {
  total: number
  skip: number
  limit: number
  has_more: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  pagination: PaginationMeta
}

// User & Auth
export interface User {
  id: string
  username: string
  email: string
  full_name: string
  role: 'ADMIN' | 'STAFF' | 'CUSTOMER'
  mobile?: string | null
  student_id?: string | null
  is_active: boolean
  created_at: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  refresh_token?: string
  expires_in?: number
  user: User
}

export interface RegisterPayload {
  username: string
  email: string
  mobile: string
  full_name: string
  password: string
}

// Seats
export interface Seat {
  id: number
  seat_number: number
  is_active: boolean
  has_power_outlet: boolean
  has_locker: boolean
  description?: string | null
}

export interface SeatStatusUpdate {
  is_active: boolean
  reason?: string
}

export interface DailySeatMatrixItem {
  seat_id: number
  seat_number: number
  is_active: boolean
  has_power_outlet: boolean
  has_locker: boolean
  morning_available: boolean
  morning_occupied_by?: string | null
  afternoon_available: boolean
  afternoon_occupied_by?: string | null
  evening_available: boolean
  evening_occupied_by?: string | null
  full_day_available: boolean
}

export interface SingleShiftSeatMatrixItem {
  seat_id: number
  seat_number: number
  status: 'AVAILABLE' | 'OCCUPIED' | 'MAINTENANCE'
  has_power_outlet: boolean
  has_locker: boolean
  occupant?: {
    student_id: string
    membership_id: string
    shift_name?: string | null
  } | null
}

export interface SingleShiftAvailabilityResponse {
  shift_id: number
  shift_name: string
  start_date: string
  end_date: string
  total_seats: number
  available_count: number
  occupied_count: number
  maintenance_count: number
  seats: SingleShiftSeatMatrixItem[]
}

// Shifts
export interface Shift {
  id: number
  name: string
  start_minute: number
  end_minute: number
  base_fee: number | string
  is_active: boolean
}

// Students
export interface Student {
  id: string
  student_code: string
  full_name: string
  mobile: string
  mobile_number?: string
  email?: string | null
  id_proof_type?: string | null
  id_proof_number?: string | null
  emergency_contact?: string | null
  address?: string | null
  notes?: string | null
  status: 'ACTIVE' | 'INACTIVE' | 'BLOCKED'
  is_active?: boolean
  created_at: string
  updated_at: string
}

export interface StudentCreatePayload {
  full_name: string
  mobile: string
  email?: string | null
  id_proof_type?: string | null
  id_proof_number?: string | null
  emergency_contact?: string | null
  address?: string | null
  notes?: string | null
}

export interface StudentUpdatePayload {
  full_name?: string
  mobile?: string
  email?: string | null
  id_proof_type?: string | null
  id_proof_number?: string | null
  emergency_contact?: string | null
  address?: string | null
  notes?: string | null
  status?: 'ACTIVE' | 'INACTIVE' | 'BLOCKED'
}

// Memberships
export interface Membership {
  id: string
  student_id: string
  student_name?: string | null
  seat_id: number
  seat_number: number
  shift_id: number
  shift_name?: string | null
  start_date: string
  end_date: string
  start_minute: number
  end_minute: number
  base_fee: number | string
  discount_amount: number | string
  final_fee: number | string
  status: 'ACTIVE' | 'CANCELLED'
  derived_status: 'ACTIVE' | 'EXPIRING_SOON' | 'EXPIRED' | 'CANCELLED'
  renewed_from_id?: string | null
  total_paid: number | string
  due_amount: number | string
  payment_status: 'PAID' | 'PARTIAL' | 'PENDING'
  created_at: string
}

export interface MembershipCreatePayload {
  student_id: string
  seat_id: number
  shift_id: number
  start_date: string
  end_date: string
  discount_amount?: number
  initial_payment_amount?: number | null
  initial_payment_method?: 'CASH' | 'UPI' | 'CARD' | 'NET_BANKING' | null
  initial_payment_ref?: string | null
}

export interface MembershipRenewPayload {
  start_date: string
  end_date: string
  target_seat_id?: number | null
  target_shift_id?: number | null
  discount_amount?: number
  initial_payment_amount?: number | null
  initial_payment_method?: 'CASH' | 'UPI' | 'CARD' | 'NET_BANKING' | null
}

export interface MembershipCancelPayload {
  cancel_reason: string
}

// Payments
export interface Payment {
  id: string
  membership_id: string
  student_id: string
  receipt_number: string
  amount: number | string
  payment_method: 'CASH' | 'UPI' | 'CARD' | 'NET_BANKING'
  status: 'COMPLETED' | 'VOIDED'
  transaction_ref?: string | null
  notes?: string | null
  void_reason?: string | null
  voided_at?: string | null
  created_at: string
}

export interface PaymentCreatePayload {
  membership_id: string
  student_id: string
  amount: number
  payment_method: 'CASH' | 'UPI' | 'CARD' | 'NET_BANKING'
  transaction_ref?: string | null
  notes?: string | null
}

export interface PaymentVoidPayload {
  void_reason: string
}

// Attendance
export interface Attendance {
  id: string
  student_id: string
  student_name?: string | null
  membership_id: string
  seat_id?: number | null
  seat_number?: number | null
  shift_name?: string | null
  attendance_date: string
  check_in: string
  check_out?: string | null
  status: 'PRESENT' | 'CHECKED_OUT'
  source: 'MANUAL_STAFF' | 'KIOSK' | 'BIOMETRIC_SYNC'
  duration_hours?: number | null
  notes?: string | null
  created_at: string
}

export interface AttendanceCheckInPayload {
  student_id?: string
  membership_id?: string
  source?: 'MANUAL_STAFF' | 'KIOSK' | 'BIOMETRIC_SYNC'
  notes?: string
}

export interface AttendanceCheckOutPayload {
  check_out_time?: string
}

// Analytics & Dashboard
export interface DashboardSummary {
  target_date: string
  total_physical_seats: number
  occupied_physical_seats: number
  physical_utilization_rate: number
  total_slot_capacity: number
  booked_shift_slots: number
  slot_occupancy_rate: number
  total_seat_hours_capacity: number
  booked_seat_hours: number
  seat_hour_occupancy_rate: number
  active_students_count: number
  expiring_soon_count: number
  expired_unrenewed_count: number
  daily_revenue: number | string
  total_outstanding_dues: number | string

  // Compatibility / optional
  physical_utilization_percentage?: number
  occupied_seats_count?: number
  empty_seats_count?: number
  slot_occupancy_percentage?: number
  consumed_slots?: number
  total_slots?: number
  seat_hour_occupancy_percentage?: number
  consumed_seat_hours?: number
  total_seat_hours?: number
  active_memberships_today?: number
  total_pending_dues?: number | string
  shift_breakdown?: Record<string, number>
}

export interface ExpiringMembershipItem {
  membership_id: string
  student_id: string
  student_name: string
  student_mobile: string
  seat_number: number
  shift_name: string
  start_date: string
  end_date: string
  final_fee?: number | string
  due_amount: number | string
  days_remaining: number
}

export interface RevenueReport {
  start_date: string
  end_date: string
  total_revenue: number | string
  transaction_count: number
  cash_total: number | string
  upi_total: number | string
  card_total: number | string
  net_banking_total: number | string
  // Compatibility
  total_collections?: number | string
  voided_count?: number
  by_payment_method?: Record<string, number>
}
