import { apiClient } from './client'
import type { Seat, DailySeatMatrixItem, SingleShiftAvailabilityResponse } from '../types'

export const seatsApi = {
  listSeats: async (isActive?: boolean): Promise<Seat[]> => {
    const params: Record<string, any> = {}
    if (isActive !== undefined) params.is_active = isActive
    const { data } = await apiClient.get<Seat[]>('/seats', { params })
    return data
  },

  getSeatAvailability: async (targetDate?: string): Promise<DailySeatMatrixItem[]> => {
    const params: Record<string, any> = {}
    if (targetDate) params.target_date = targetDate
    const { data } = await apiClient.get<DailySeatMatrixItem[]>('/seats/availability', { params })
    return data
  },

  getShiftAvailability: async (startDate: string, endDate: string, shiftId: number): Promise<SingleShiftAvailabilityResponse> => {
    const { data } = await apiClient.get<SingleShiftAvailabilityResponse>('/seats/availability', {
      params: { start_date: startDate, end_date: endDate, shift_id: shiftId },
    })
    return data
  },

  getSeat: async (id: number): Promise<Seat> => {
    const { data } = await apiClient.get<Seat>(`/seats/${id}`)
    return data
  },

  toggleMaintenance: async (id: number): Promise<Seat> => {
    const { data } = await apiClient.put<Seat>(`/seats/${id}/toggle-maintenance`)
    return data
  },

  updateSeatStatus: async (id: number, isActive: boolean, reason?: string): Promise<Seat> => {
    const { data } = await apiClient.patch<Seat>(`/seats/${id}/status`, {
      is_active: isActive,
      reason,
    })
    return data
  },
}
