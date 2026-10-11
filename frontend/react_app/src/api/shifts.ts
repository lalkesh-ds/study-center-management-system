import { apiClient } from './client'
import type { Shift } from '../types'

export const shiftsApi = {
  listShifts: async (): Promise<Shift[]> => {
    const { data } = await apiClient.get<Shift[]>('/shifts')
    return data
  },
  getShift: async (id: number): Promise<Shift> => {
    const { data } = await apiClient.get<Shift>(`/shifts/${id}`)
    return data
  },
}
