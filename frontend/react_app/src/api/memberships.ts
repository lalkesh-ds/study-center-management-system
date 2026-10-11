import { apiClient } from './client'
import type {
  Membership,
  MembershipCreatePayload,
  MembershipRenewPayload,
  MembershipCancelPayload,
  PaginatedResponse,
} from '../types'

export const membershipsApi = {
  listMemberships: async (
    status?: string,
    studentId?: string,
    seatId?: number,
    skip = 0,
    limit = 50
  ): Promise<PaginatedResponse<Membership>> => {
    const params: Record<string, any> = { skip, limit }
    if (status && status !== 'ALL') params.status = status
    if (studentId) params.student_id = studentId
    if (seatId) params.seat_id = seatId

    const { data } = await apiClient.get<PaginatedResponse<Membership>>('/memberships', { params })
    return data
  },

  getMembership: async (id: string): Promise<Membership> => {
    const { data } = await apiClient.get<Membership>(`/memberships/${id}`)
    return data
  },

  createAdmission: async (payload: MembershipCreatePayload): Promise<Membership> => {
    const { data } = await apiClient.post<Membership>('/memberships', payload)
    return data
  },

  renewMembership: async (id: string, payload: MembershipRenewPayload): Promise<Membership> => {
    const { data } = await apiClient.post<Membership>(`/memberships/${id}/renew`, payload)
    return data
  },

  cancelMembership: async (id: string, payload: MembershipCancelPayload): Promise<Membership> => {
    const { data } = await apiClient.post<Membership>(`/memberships/${id}/cancel`, payload)
    return data
  },
}
