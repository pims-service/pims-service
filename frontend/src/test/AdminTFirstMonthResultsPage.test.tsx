import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AdminTFirstMonthResultsPage from '../pages/AdminTFirstMonthResultsPage';
import { questionnairesApi } from '../services/api';

// Mock the API service
vi.mock('../services/api', () => ({
  questionnairesApi: {
    getAdminTFirstMonthResponses: vi.fn(),
    getAdminTFirstMonthDetail: vi.fn(),
    triggerAdminTFirstMonthExport: vi.fn(),
    getAdminExportStatus: vi.fn(),
  },
}));

describe.sequential('AdminTFirstMonthResultsPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders loading state initially and then shows submission list', async () => {
    const mockResponses = {
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: 'tfm-sub-1',
          user: 6,
          full_name: 'Noman R.',
          username: 'noman',
          questionnaire: 'q-tfm-id',
          questionnaire_title: 'T-First-Month Questionnaire',
          group_name: 'Group B',
          status: 'COMPLETED',
          started_at: '2026-06-01T12:00:00Z',
          completed_at: '2026-06-01T12:30:00Z',
        },
      ],
    };

    (questionnairesApi.getAdminTFirstMonthResponses as any).mockResolvedValueOnce({ data: mockResponses });

    render(
      <MemoryRouter>
        <AdminTFirstMonthResultsPage />
      </MemoryRouter>
    );

    // Verify loading indicator is shown
    expect(screen.getByText('Loading T-First-Month follow-up data...')).toBeInTheDocument();

    // Wait for the data to load and verify columns and row details
    expect(await screen.findByText('T-First-Month Post-Test Results')).toBeInTheDocument();
    expect(await screen.findByText('Noman R.')).toBeInTheDocument();
    expect(await screen.findByText('@noman')).toBeInTheDocument();
    expect((await screen.findAllByText('Group B')).length).toBeGreaterThan(0);
  });

  it('handles CSV export trigger correctly', async () => {
    (questionnairesApi.getAdminTFirstMonthResponses as any).mockResolvedValueOnce({ data: { results: [], count: 0 } });
    (questionnairesApi.triggerAdminTFirstMonthExport as any).mockResolvedValueOnce({ data: { task_id: 'export-task-tfm' } });

    render(
      <MemoryRouter>
        <AdminTFirstMonthResultsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('T-First-Month Post-Test Results')).toBeInTheDocument();
    });

    const exportBtn = screen.getByRole('button', { name: /Export CSV/i });
    fireEvent.click(exportBtn);

    expect(questionnairesApi.triggerAdminTFirstMonthExport).toHaveBeenCalledWith('All');
    await waitFor(() => {
      expect(screen.getByText(/Processing large dataset export/i)).toBeInTheDocument();
    });
  });

  it('retrieves and displays T-First-Month response detail inside the modal', async () => {
    const mockResponses = {
      count: 1,
      results: [
        {
          id: 'tfm-sub-1',
          full_name: 'Khuzaim K.',
          username: 'khuzaim',
          group_name: 'Group A',
          completed_at: '2026-06-01T12:30:00Z',
        },
      ],
    };

    const mockDetail = {
      id: 'tfm-sub-1',
      full_name: 'Khuzaim K.',
      status: 'COMPLETED',
      completed_at: '2026-06-01T12:30:00Z',
      responses: [
        {
          id: 'resp-tfm-1',
          question_text: 'Did you feel energetic?',
          selected_option_label: 'Moderately',
          text_value: null,
        },
      ],
    };

    (questionnairesApi.getAdminTFirstMonthResponses as any).mockResolvedValueOnce({ data: mockResponses });
    (questionnairesApi.getAdminTFirstMonthDetail as any).mockResolvedValueOnce({ data: mockDetail });

    render(
      <MemoryRouter>
        <AdminTFirstMonthResultsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Khuzaim K.')).toBeInTheDocument();
    });

    const viewBtn = screen.getByRole('button', { name: /View Details/i });
    fireEvent.click(viewBtn);

    expect(questionnairesApi.getAdminTFirstMonthDetail).toHaveBeenCalledWith('tfm-sub-1');

    await waitFor(() => {
      expect(screen.getByText('T-First-Month Response Detail')).toBeInTheDocument();
      expect(screen.getByText('Did you feel energetic?')).toBeInTheDocument();
      expect(screen.getByText('Moderately')).toBeInTheDocument();
    });
  });
});
