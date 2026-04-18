import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AdminBaselineResultsPage from '../pages/AdminBaselineResultsPage';
import { questionnairesApi } from '../services/api';

vi.mock('../services/api', () => ({
  questionnairesApi: {
    getAdminBaselineResponses: vi.fn(),
    exportAdminBaselinesCSV: vi.fn(),
  }
}));

// Mock browser global for file downloading
global.URL.createObjectURL = vi.fn();
// Mock anchor click to avoid JSDOM navigation error
window.HTMLAnchorElement.prototype.click = vi.fn();

describe('AdminBaselineResultsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders unique groups dynamically in the UI filter dropdown', async () => {
    const mockResponse = {
      data: {
        results: [
          { id: '1', full_name: 'Alpha John', username: 'ajohn', group_name: 'Control Group', completed_at: '2026-04-18' },
          { id: '2', full_name: 'Bravo Jane', username: 'bjane', group_name: 'Variable Group', completed_at: '2026-04-18' },
        ],
        count: 2,
        next: null,
        previous: null
      }
    };
    (questionnairesApi.getAdminBaselineResponses as any).mockResolvedValue(mockResponse);

    render(
      <MemoryRouter>
        <AdminBaselineResultsPage />
      </MemoryRouter>
    );

    // Wait for the loading block to vanish
    await waitFor(() => {
      expect(screen.queryByText('Retrieving raw response sets...')).not.toBeInTheDocument();
    });

    // Check dropdown aggregation logic isolates explicit options
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
    expect(screen.getByText('All Groups')).toBeInTheDocument();
    
    // Use getAllByText because 'Control Group' text appears in the table AND the dropdown
    expect(screen.getAllByText('Control Group').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Variable Group').length).toBeGreaterThan(0);
  });

  it('accurately injects the active group string to the export API payload', async () => {
    const mockResponse = {
      data: {
        results: [
          { id: '1', full_name: 'Delta Jack', username: 'djack', group_name: 'Analysis Group', completed_at: '2026-04-18' },
        ],
        count: 1,
        next: null,
        previous: null
      }
    };
    (questionnairesApi.getAdminBaselineResponses as any).mockResolvedValue(mockResponse);
    (questionnairesApi.exportAdminBaselinesCSV as any).mockResolvedValue({ data: new Blob() });

    render(
      <MemoryRouter>
        <AdminBaselineResultsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Delta Jack')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    
    // Simulate User choosing a mapped Group Filter
    fireEvent.change(select, { target: { value: 'Analysis Group' } });

    // Simulate User starting the export action
    const exportBtn = screen.getByText(/Export SPSS CSV/i);
    fireEvent.click(exportBtn);

    // Ensure the wrapper accurately sends the queried string argument
    await waitFor(() => {
      expect(questionnairesApi.exportAdminBaselinesCSV).toHaveBeenCalledWith('Analysis Group');
    });
  });
});
