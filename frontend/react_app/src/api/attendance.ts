import { apiClient } from './client'
import type { Attendance, AttendanceCheckInPayload, AttendanceCheckOutPayload } from '../types'

export const attendanceApi = {
  checkIn: async (payload: AttendanceCheckInPayload): Promise<Attendance> => {
    const { data } = await apiClient.post<Attendance>('/attendance/check-in', payload)
    return data
  },

  checkOut: async (id: string, payload?: AttendanceCheckOutPayload): Promise<Attendance> => {
    const { data } = await apiClient.post<Attendance>(`/attendance/${id}/check-out`, payload || {})
    return data
  },

  listDailyAttendance: async (attendanceDate?: string): Promise<Attendance[]> => {
    const params: Record<string, any> = {}
    if (attendanceDate) params.attendance_date = attendanceDate
    const { data } = await apiClient.get<Attendance[]>('/attendance/daily', { params })
    return data
  },
}
