import { apiClient } from './client'
import type { DashboardSummary, ExpiringMembershipItem, RevenueReport } from '../types'

export const analyticsApi = {
  getDashboardSummary: async (targetDate?: string): Promise<DashboardSummary> => {
    const params: Record<string, any> = {}
    if (targetDate) params.target_date = targetDate
    const { data } = await apiClient.get<DashboardSummary>('/dashboard/summary', { params })
    return data
  },

  getExpiringMemberships: async (daysThreshold = 3): Promise<ExpiringMembershipItem[]> => {
    const { data } = await apiClient.get<ExpiringMembershipItem[]>('/reports/expiring', {
      params: { days_threshold: daysThreshold },
    })
    return data
  },

  getRevenueReport: async (startDate?: string, endDate?: string): Promise<RevenueReport> => {
    const params: Record<string, any> = {}
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    const { data } = await apiClient.get<RevenueReport>('/reports/revenue', { params })
    return data
  },
}
