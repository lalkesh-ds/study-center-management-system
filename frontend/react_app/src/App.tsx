import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/layout/ProtectedRoute'
import { AppLayout } from './components/layout/AppLayout'
import { ErrorBoundary } from './components/shared/ErrorBoundary'

// Pages
import { LoginPage } from './features/auth/LoginPage'
import { RegisterPage } from './features/auth/RegisterPage'
import { ForgotPasswordPage } from './features/auth/ForgotPasswordPage'
import { CustomerPortalPage } from './features/customer/CustomerPortalPage'
import { DashboardPage } from './features/dashboard/DashboardPage'
import { SeatsPage } from './features/seats/SeatsPage'
import { StudentsPage } from './features/students/StudentsPage'
import { MembershipsPage } from './features/memberships/MembershipsPage'
import { PaymentsPage } from './features/payments/PaymentsPage'
import { AttendancePage } from './features/attendance/AttendancePage'
import { AnalyticsPage } from './features/analytics/AnalyticsPage'
import { NotFoundPage } from './components/shared/NotFoundPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 30, // 30s
      retry: 1,
    },
  },
})

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ErrorBoundary>
          <BrowserRouter>
            <Routes>
              {/* Public Auth Routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />

              {/* Protected Routes (Library Owners & Staff) */}
              <Route element={<ProtectedRoute />}>
                <Route element={<AppLayout />}>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/seats" element={<SeatsPage />} />
                  <Route path="/students" element={<StudentsPage />} />
                  <Route path="/memberships" element={<MembershipsPage />} />
                  <Route path="/payments" element={<PaymentsPage />} />
                  <Route path="/attendance" element={<AttendancePage />} />
                  <Route path="/analytics" element={<AnalyticsPage />} />
                </Route>
              </Route>

              {/* 404 & Fallback */}
              <Route path="/404" element={<NotFoundPage />} />
              <Route path="*" element={<Navigate to="/404" replace />} />
            </Routes>
          </BrowserRouter>
        </ErrorBoundary>
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
