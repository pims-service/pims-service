import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AdminT4ResultsPage from '../pages/AdminT4ResultsPage';
import { questionnairesApi } from '../services/api';

vi.mock('../services/api', () => ({
  questionnairesApi: {
    getAdminT4Responses: vi.fn(),
    getAdminT4Detail: vi.fn(),
    triggerAdminT4Export: vi.fn(),
    getAdminExportStatus: vi.fn(),
  },
}));

describe.sequential('AdminT4ResultsPage', () => {
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
          id: 't4-sub-1',
          user: 5,
          full_name: 'John Doe',
          username: 'johndoe',
          questionnaire: 'q-t4-id',
          questionnaire_title: 'T4 Questionnaire',
          group_name: 'Group A',
          status: 'COMPLETED',
          started_at: '2026-06-01T12:00:00Z',
          completed_at: '2026-06-01T12:30:00Z',
        },
      ],
    };

    (questionnairesApi.getAdminT4Responses as any).mockResolvedValueOnce({ data: mockResponses });

    render(
      <MemoryRouter>
        <AdminT4ResultsPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Loading 1-year assessment data...')).toBeInTheDocument();
    expect(await screen.findByText('1-Year Assessment Results')).toBeInTheDocument();
    expect(await screen.findByText('John Doe')).toBeInTheDocument();
    expect(await screen.findByText(/johndoe/i)).toBeInTheDocument();
    expect((await screen.findAllByText('Group A')).length).toBeGreaterThan(0);
  });

  it('handles CSV export trigger correctly', async () => {
    (questionnairesApi.getAdminT4Responses as any).mockResolvedValueOnce({ data: { results: [], count: 0 } });
    (questionnairesApi.triggerAdminT4Export as any).mockResolvedValueOnce({ data: { task_id: 'export-task-123' } });

    render(
      <MemoryRouter>
        <AdminT4ResultsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('1-Year Assessment Results')).toBeInTheDocument();
    });

    const exportBtn = screen.getByRole('button', { name: /Export CSV/i });
    fireEvent.click(exportBtn);

    expect(questionnairesApi.triggerAdminT4Export).toHaveBeenCalledWith('All');
    await waitFor(() => {
      expect(screen.getByText(/Processing large dataset export/i)).toBeInTheDocument();
    });
  });

  it('retrieves and displays T4 response detail inside the modal', async () => {
    const mockResponses = {
      count: 1,
      results: [
        {
          id: 't4-sub-1',
          full_name: 'Jane Smith',
          username: 'janesmith',
          group_name: 'Group B',
          completed_at: '2026-06-01T12:30:00Z',
        },
      ],
    };

    const mockDetail = {
      id: 't4-sub-1',
      full_name: 'Jane Smith',
      status: 'COMPLETED',
      completed_at: '2026-06-01T12:30:00Z',
      responses: [
        {
          id: 'resp-1',
          question_text: 'How satisfied are you?',
          selected_option_label: 'Very satisfied',
          text_value: null,
        },
      ],
    };

    (questionnairesApi.getAdminT4Responses as any).mockResolvedValueOnce({ data: mockResponses });
    (questionnairesApi.getAdminT4Detail as any).mockResolvedValueOnce({ data: mockDetail });

    render(
      <MemoryRouter>
        <AdminT4ResultsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });

    const viewBtn = screen.getByRole('button', { name: /View Details/i });
    fireEvent.click(viewBtn);

    expect(questionnairesApi.getAdminT4Detail).toHaveBeenCalledWith('t4-sub-1');

    await waitFor(() => {
      expect(screen.getByText('1-Year Assessment Response Detail')).toBeInTheDocument();
      expect(screen.getByText('How satisfied are you?')).toBeInTheDocument();
      expect(screen.getByText('Very satisfied')).toBeInTheDocument();
    });
  });
});
