import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AdminFollowUpsPage from '../pages/AdminFollowUpsPage';
import api from '../services/api';

// Mock the API service
vi.mock('../services/api', () => {
  return {
    default: {
      get: vi.fn(),
      patch: vi.fn(),
    },
  };
});

describe('AdminFollowUpsPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders loading state initially and then shows follow-up tickets', async () => {
    const mockTickets = [
      {
        id: 1,
        ticket_number: 'TKT-A1B2C3',
        user_full_name: 'Alice Cooper',
        user_email: 'alice@cooper.com',
        user_whatsapp_number: '+123456789',
        subject: 'Call Protocol: High Daily Activity Miss Rate (Tier 3)',
        message: 'Alice has missed most activities.',
        status: 'Open',
        created_at: '2026-06-01T12:00:00Z',
      },
    ];

    (api.get as any).mockResolvedValueOnce({ data: mockTickets });

    render(
      <MemoryRouter>
        <AdminFollowUpsPage />
      </MemoryRouter>
    );

    // Verify loading state
    expect(screen.getByText('Syncing outreach list...')).toBeInTheDocument();

    // Verify loaded ticket details
    expect(await screen.findByText('Call Protocol Follow-Ups')).toBeInTheDocument();
    expect(await screen.findByText('Alice Cooper')).toBeInTheDocument();
    expect(await screen.findByText('alice@cooper.com')).toBeInTheDocument();
    expect(await screen.findByText('+123456789')).toBeInTheDocument();
    expect(await screen.findByText('Call Protocol: High Daily Activity Miss Rate (Tier 3)')).toBeInTheDocument();
  });

  it('handles status review and updates correctly inside the modal', async () => {
    const mockTickets = [
      {
        id: 1,
        ticket_number: 'TKT-A1B2C3',
        user_full_name: 'Alice Cooper',
        user_email: 'alice@cooper.com',
        user_whatsapp_number: '+123456789',
        subject: 'Call Protocol: High Daily Activity Miss Rate (Tier 3)',
        message: 'Alice has missed most activities.',
        status: 'Open',
        admin_notes: 'Initial clinical notes',
        created_at: '2026-06-01T12:00:00Z',
      },
    ];

    (api.get as any).mockResolvedValueOnce({ data: mockTickets });
    (api.patch as any).mockResolvedValueOnce({ data: { status: 'Resolved' } });

    render(
      <MemoryRouter>
        <AdminFollowUpsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Alice Cooper')).toBeInTheDocument();
    });

    const reviewBtn = screen.getByRole('button', { name: /Review Call Status/i });
    fireEvent.click(reviewBtn);

    // Modal should open
    expect(screen.getByText('Outreach Task TKT-A1B2C3')).toBeInTheDocument();
    expect(screen.getByText('Initial clinical notes')).toBeInTheDocument();

    // Change status in select dropdown
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Resolved' } });

    // Click save changes button
    const saveBtn = screen.getByRole('button', { name: /Save Outreach Updates/i });
    fireEvent.click(saveBtn);

    expect(api.patch).toHaveBeenCalledWith('/support/tickets/1/', {
      status: 'Resolved',
      admin_notes: 'Initial clinical notes',
    });
  });
});
