import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AdminSuicideRiskPage from '../pages/AdminSuicideRiskPage';
import api from '../services/api';

vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('AdminSuicideRiskPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders opted-in flagged participants from cached API', async () => {
    (api.get as any).mockResolvedValueOnce({
      data: {
        last_refreshed_at: '2026-06-05T12:00:00Z',
        total_flagged: 2,
        opt_in_count: 1,
        cases: [
          {
            response_set_id: 'rs-1',
            user_id: 1,
            username: 'tester_export',
            email: 'tester@example.com',
            full_name: 'Export Test User',
            whatsapp_number: '+923001234567',
            group_name: 'Group 1',
            milestone_label: 'T0 (Signup)',
            completed_at: '2026-06-05T11:00:00Z',
            suicide_risk_opt_in: true,
            phq9_total: 17,
            sidas_total: 29,
          },
        ],
      },
    });

    render(
      <MemoryRouter>
        <AdminSuicideRiskPage />
      </MemoryRouter>
    );

    expect(await screen.findByText('Safety Risk Follow-Ups')).toBeInTheDocument();
    expect(await screen.findByText('Export Test User')).toBeInTheDocument();
    expect(await screen.findByText('tester@example.com')).toBeInTheDocument();
    expect(await screen.findByText('Opted in')).toBeInTheDocument();
    expect(await screen.findByText('T0 (Signup)')).toBeInTheDocument();
  });

  it('shows empty state when no opted-in cases', async () => {
    (api.get as any).mockResolvedValueOnce({
      data: {
        last_refreshed_at: '2026-06-05T12:00:00Z',
        total_flagged: 0,
        opt_in_count: 0,
        cases: [],
      },
    });

    render(
      <MemoryRouter>
        <AdminSuicideRiskPage />
      </MemoryRouter>
    );

    expect(
      await screen.findByText('No participants have opted in for researcher follow-up.')
    ).toBeInTheDocument();
  });
});
