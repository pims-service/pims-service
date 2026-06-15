import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AdminT2ResultsPage from '../pages/AdminT2ResultsPage';
import { questionnairesApi } from '../services/api';

// Mock the API service
vi.mock('../services/api', () => ({
  questionnairesApi: {
    getAdminT2Responses: vi.fn(),
    getAdminT2Detail: vi.fn(),
    triggerAdminT2Export: vi.fn(),
    getAdminExportStatus: vi.fn(),
  },
}));

describe.sequential('AdminT2ResultsPage', () => {
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
          id: 't2-sub-1',
          user: 5,
          full_name: 'John Doe',
          username: 'johndoe',
          questionnaire: 'q-t2-id',
          questionnaire_title: 'T2 Questionnaire',
          group_name: 'Group A',
          status: 'COMPLETED',
          started_at: '2026-06-01T12:00:00Z',
          completed_at: '2026-06-01T12:30:00Z',
        },
      ],
    };

    (questionnairesApi.getAdminT2Responses as any).mockResolvedValueOnce({ data: mockResponses });

    render(
      <MemoryRouter>
        <AdminT2ResultsPage />
      </MemoryRouter>
    );

    // Verify loading indicator is shown
    expect(screen.getByText('Loading 3-month assessment data...')).toBeInTheDocument();

    // Wait for the data to load and verify columns and row details
    expect(await screen.findByText('3-Month Assessment Results')).toBeInTheDocument();
    expect(await screen.findByText('John Doe')).toBeInTheDocument();
    expect(await screen.findByText(/johndoe/i)).toBeInTheDocument();
    expect((await screen.findAllByText('Group A')).length).toBeGreaterThan(0);
  });

  it('handles CSV export trigger correctly', async () => {
    (questionnairesApi.getAdminT2Responses as any).mockResolvedValueOnce({ data: { results: [], count: 0 } });
    (questionnairesApi.triggerAdminT2Export as any).mockResolvedValueOnce({ data: { task_id: 'export-task-123' } });

    render(
      <MemoryRouter>
        <AdminT2ResultsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('3-Month Assessment Results')).toBeInTheDocument();
    });

    const exportBtn = screen.getByRole('button', { name: /Export Assessments CSV/i });
    fireEvent.click(exportBtn);

    expect(questionnairesApi.triggerAdminT2Export).toHaveBeenCalledWith('All');
    await waitFor(() => {
      expect(screen.getByText(/Processing large dataset export/i)).toBeInTheDocument();
    });
  });

  it('retrieves and displays T2 response detail inside the modal', async () => {
    const mockResponses = {
      count: 1,
      results: [
        {
          id: 't2-sub-1',
          full_name: 'Jane Smith',
          username: 'janesmith',
          group_name: 'Group B',
          completed_at: '2026-06-01T12:30:00Z',
        },
      ],
    };

    const mockDetail = {
      id: 't2-sub-1',
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

    (questionnairesApi.getAdminT2Responses as any).mockResolvedValueOnce({ data: mockResponses });
    (questionnairesApi.getAdminT2Detail as any).mockResolvedValueOnce({ data: mockDetail });

    render(
      <MemoryRouter>
        <AdminT2ResultsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });

    const viewBtn = screen.getByRole('button', { name: /View Details/i });
    fireEvent.click(viewBtn);

    expect(questionnairesApi.getAdminT2Detail).toHaveBeenCalledWith('t2-sub-1');

    await waitFor(() => {
      expect(screen.getByText('3-Month Assessment Response Detail')).toBeInTheDocument();
      expect(screen.getByText('How satisfied are you?')).toBeInTheDocument();
      expect(screen.getByText('Very satisfied')).toBeInTheDocument();
    });
  });
});
