import { apiClient } from './client'
import type { Payment, PaymentCreatePayload, PaymentVoidPayload } from '../types'

export const paymentsApi = {
  recordPayment: async (payload: PaymentCreatePayload): Promise<Payment> => {
    const { data } = await apiClient.post<Payment>('/payments', payload)
    return data
  },

  voidPayment: async (paymentId: string, payload: PaymentVoidPayload): Promise<Payment> => {
    const { data } = await apiClient.post<Payment>(`/payments/${paymentId}/void`, payload)
    return data
  },

  listMembershipPayments: async (membershipId: string): Promise<Payment[]> => {
    const { data } = await apiClient.get<Payment[]>(`/memberships/${membershipId}/payments`)
    return data
  },

  exportRevenueCsv: (startDate?: string, endDate?: string): string => {
    const params = new URLSearchParams()
    if (startDate) params.set('start_date', startDate)
    if (endDate) params.set('end_date', endDate)
    const queryString = params.toString() ? `?${params.toString()}` : ''
    return `${apiClient.defaults.baseURL}/reports/revenue/export${queryString}`
  },
}
