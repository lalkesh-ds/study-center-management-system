import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Badge } from '../components/ui/Badge'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { StatCard } from '../components/shared/StatCard'
import { EmptyState } from '../components/shared/EmptyState'
import { Modal } from '../components/shared/Modal'
import { Users } from 'lucide-react'

describe('UI Primitives', () => {
  it('renders Badge with custom variants and children', () => {
    const { rerender } = render(<Badge variant="success">Active</Badge>)
    expect(screen.getByText('Active')).toBeInTheDocument()
    expect(screen.getByText('Active')).toHaveClass('bg-emerald-500/10')

    rerender(<Badge variant="danger">Expired</Badge>)
    expect(screen.getByText('Expired')).toHaveClass('bg-rose-500/10')
  })

  it('renders Card with header and content sections', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Seat Allocation</CardTitle>
        </CardHeader>
        <CardContent>
          <p>100 Available Desks</p>
        </CardContent>
      </Card>
    )

    expect(screen.getByText('Seat Allocation')).toBeInTheDocument()
    expect(screen.getByText('100 Available Desks')).toBeInTheDocument()
  })

  it('renders StatCard with title, value, helper text, and icon', () => {
    render(
      <StatCard
        title="Total Members"
        value={154}
        subtitle="Active subscribers"
        icon={Users}
        trend="+8% this month"
      />
    )

    expect(screen.getByText('Total Members')).toBeInTheDocument()
    expect(screen.getByText('154')).toBeInTheDocument()
    expect(screen.getByText('Active subscribers')).toBeInTheDocument()
    expect(screen.getByText('+8% this month')).toBeInTheDocument()
  })

  it('renders EmptyState with action button and triggers callback', async () => {
    const user = userEvent.setup()
    const handleAction = vi.fn()

    render(
      <EmptyState
        title="No memberships found"
        description="Create your first subscription"
        action={{
          label: 'Add Membership',
          onClick: handleAction,
        }}
      />
    )

    expect(screen.getByText('No memberships found')).toBeInTheDocument()
    expect(screen.getByText('Create your first subscription')).toBeInTheDocument()

    const button = screen.getByRole('button', { name: /Add Membership/i })
    await user.click(button)
    expect(handleAction).toHaveBeenCalledTimes(1)
  })

  it('renders Modal when isOpen is true and closes on close button', async () => {
    const user = userEvent.setup()
    const handleClose = vi.fn()

    const { rerender } = render(
      <Modal isOpen={false} onClose={handleClose} title="Edit Student">
        <div>Form Content</div>
      </Modal>
    )

    expect(screen.queryByText('Edit Student')).not.toBeInTheDocument()

    rerender(
      <Modal isOpen={true} onClose={handleClose} title="Edit Student">
        <div>Form Content</div>
      </Modal>
    )

    expect(screen.getByText('Edit Student')).toBeInTheDocument()
    expect(screen.getByText('Form Content')).toBeInTheDocument()

    const closeBtn = screen.getByRole('button', { name: /close modal/i })
    await user.click(closeBtn)
    expect(handleClose).toHaveBeenCalledTimes(1)
  })
})
