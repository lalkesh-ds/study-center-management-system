import { apiClient } from './client'
import type { Student, StudentCreatePayload, StudentUpdatePayload, PaginatedResponse } from '../types'

export const studentsApi = {
  listStudents: async (search?: string, skip = 0, limit = 50): Promise<PaginatedResponse<Student>> => {
    const params: Record<string, any> = { skip, limit }
    if (search) params.search = search
    const { data } = await apiClient.get<PaginatedResponse<Student>>('/students', { params })
    return data
  },

  getStudent: async (id: string): Promise<Student> => {
    const { data } = await apiClient.get<Student>(`/students/${id}`)
    return data
  },

  createStudent: async (payload: StudentCreatePayload): Promise<Student> => {
    const { data } = await apiClient.post<Student>('/students', payload)
    return data
  },

  updateStudent: async (id: string, payload: StudentUpdatePayload): Promise<Student> => {
    const { data } = await apiClient.put<Student>(`/students/${id}`, payload)
    return data
  },

  exportStudentsCsv: (): string => {
    return `${apiClient.defaults.baseURL}/students/export`
  },
}
