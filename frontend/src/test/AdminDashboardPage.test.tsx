import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AdminDashboardPage from '../pages/AdminDashboardPage';
import { questionnairesApi } from '../services/api';

// Mock the API service
vi.mock('../services/api', () => ({
  questionnairesApi: {
    getDashboardAnalytics: vi.fn(),
  },
  groupsApi: {
    getGroups: vi.fn().mockResolvedValue({ data: [] }),
  }
}));

describe('AdminDashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches and renders dashboard analytics correctly', async () => {
    const mockData = {
      total_participants: 423,
      active_rate_percentage: 82.5,
      total_submissions: 1042,
      current_phase_name: 'Phase 2: Experiment',
      engagement_trend: [],
      recent_participants: []
    };
    
    // Assign mock resolution
    (questionnairesApi.getDashboardAnalytics as any).mockResolvedValue({ data: mockData });

    render(
      <MemoryRouter>
        <AdminDashboardPage />
      </MemoryRouter>
    );

    // Should indicate loading initially
    expect(screen.getByText('Loading analytics...')).toBeInTheDocument();

    // Verify UI injected text from mock API response
    await waitFor(() => {
      expect(screen.getByText('423')).toBeInTheDocument();
      expect(screen.getByText('82.5%')).toBeInTheDocument();
      expect(screen.getByText('1,042')).toBeInTheDocument();
      expect(screen.getByText('Phase 2: Experiment')).toBeInTheDocument();
    });
  });

  it('safely handles API errors', async () => {
    // Assert rejection behavior
    (questionnairesApi.getDashboardAnalytics as any).mockRejectedValue(new Error('API Down'));

    render(
      <MemoryRouter>
        <AdminDashboardPage />
      </MemoryRouter>
    );

        await waitFor(() => {
      expect(screen.getByText(/Failed to load dashboard analytics./i)).toBeInTheDocument();
    });
  });
});
