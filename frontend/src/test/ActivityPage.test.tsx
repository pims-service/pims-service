import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ActivityPage from '../pages/ActivityPage';
import api from '../services/api';

// Mock the API service
vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  }
}));

// Mock react-i18next with dynamic language capability
let mockLanguage = 'en';
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback?: string) => fallback || key,
    i18n: {
      changeLanguage: (lng: string) => {
        mockLanguage = lng;
      },
      language: mockLanguage,
    },
  }),
}));

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

describe('ActivityPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockLanguage = 'en'; // Reset mock language to English
  });

  const renderComponent = (id: string = '12') => {
    return render(
      <MemoryRouter initialEntries={[`/activity/${id}`]}>
        <Routes>
          <Route path="/activity/:id" element={<ActivityPage />} />
        </Routes>
      </MemoryRouter>
    );
  };

  it('renders loading state initially and loads activity details', async () => {
    const mockActivity = {
      id: 12,
      title: 'Structured Reflection',
      description: 'Daily prompt instruction | اردو والا ہدایات',
      group_name: 'Group 3',
      day_number: 1,
      submitted_today: false,
    };

    (api.get as any).mockResolvedValue({ data: mockActivity });

    renderComponent();

    // Verify API is called
    expect(api.get).toHaveBeenCalledWith('/activities/daily/current/');

    // Verify title and bilingual descriptions are rendered
    await waitFor(() => {
      expect(screen.getByText('Structured Reflection')).toBeInTheDocument();
      expect(screen.getByText('Daily prompt instruction')).toBeInTheDocument();
      expect(screen.getByText('اردو والا ہدایات')).toBeInTheDocument();
    });
  });

  it('renders Group 3 Day 2 schedule, definitions, and examples correctly in English', async () => {
    const mockActivity = {
      id: 12,
      title: 'Structured Reflection',
      description: 'Daily prompt instruction | اردو ہدایات',
      group_name: 'Group 3',
      day_number: 2, // Day 2 should show Relationships, Accomplishment, Pleasure
      submitted_today: false,
    };

    (api.get as any).mockResolvedValue({ data: mockActivity });

    renderComponent();

    await waitFor(() => {
      // Entry labels
      expect(screen.getByText('Entry 1: Positive Relationships')).toBeInTheDocument();
      expect(screen.getByText('Entry 2: Accomplishment')).toBeInTheDocument();
      expect(screen.getByText('Entry 3: Pleasure')).toBeInTheDocument();

      // Definitions & Examples - English
      expect(screen.getByText('A meaningful interaction today with another person.')).toBeInTheDocument();
      expect(screen.getByText(/neighbour saw me carrying shopping bags/)).toBeInTheDocument();

      expect(screen.getByText('Something today that gave you a sense of doing well.')).toBeInTheDocument();
      expect(screen.getByText(/Finished the proposal section I had been stuck/)).toBeInTheDocument();

      expect(screen.getByText('A moment of enjoyment, comfort, or fun today.')).toBeInTheDocument();
      expect(screen.getByText(/Sipping chai on the balcony/)).toBeInTheDocument();
    });
  });

  it('renders Group 3 labels and definitions in Urdu when language is ur', async () => {
    mockLanguage = 'ur';
    const mockActivity = {
      id: 12,
      title: 'Structured Reflection',
      description: 'Daily prompt instruction | اردو ہدایات',
      group_name: 'Group 3',
      day_number: 2, // Day 2
      submitted_today: false,
    };

    (api.get as any).mockResolvedValue({ data: mockActivity });

    renderComponent();

    await waitFor(() => {
      // Entry labels in Urdu
      expect(screen.getByText('اندراج 1: مثبت تعلقات')).toBeInTheDocument();
      expect(screen.getByText('اندراج 2: کامیابی')).toBeInTheDocument();
      expect(screen.getByText('اندراج 3: لطف')).toBeInTheDocument();

      // Definitions - Urdu
      expect(screen.getByText('آج کسی دوسرے فرد کے ساتھ کوئی بامقصد ملاقات یا رابطہ۔')).toBeInTheDocument();
      expect(screen.getByText('آج کا کوئی کام جس نے اچھا کرنے کا احساس دلایا ہو۔')).toBeInTheDocument();
      expect(screen.getByText('آج کا کوئی لمحہ جس میں لطف، سکون، یا تفریح محسوس ہوئی ہو۔')).toBeInTheDocument();
    });
  });

  it('performs word counting and enforces limits (20 - 200 words)', async () => {
    const mockActivity = {
      id: 12,
      title: 'Structured Reflection',
      description: 'Daily prompt instruction',
      group_name: 'Group 3',
      day_number: 1,
      submitted_today: false,
    };

    (api.get as any).mockResolvedValue({ data: mockActivity });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Entry 1: Pleasure')).toBeInTheDocument();
    });

    const textareas = screen.getAllByRole('textbox');
    expect(textareas).toHaveLength(3);

    // Initial state: 0 / 200 words, no submit button enabled
    const submitBtn = screen.queryByRole('button', { name: /Submit Activity/i });
    expect(submitBtn).toBeDisabled();

    // 1. Text is less than 20 words
    fireEvent.change(textareas[0], { target: { value: 'This is short' } });
    expect(screen.getByText('Minimum 20 words required.')).toBeInTheDocument();

    // 2. Text is exactly 20 words
    const validText = Array(20).fill('word').join(' ');
    fireEvent.change(textareas[0], { target: { value: validText } });
    expect(screen.queryByText('Minimum 20 words required.')).not.toBeInTheDocument();

    // 3. Text is close to 200 words (warning zone)
    const warningText = Array(185).fill('word').join(' ');
    fireEvent.change(textareas[0], { target: { value: warningText } });
    expect(screen.getByText('Warning: Approaching 200-word limit.')).toBeInTheDocument();

    // 4. Text exceeds 200 words (error zone)
    const errorText = Array(201).fill('word').join(' ');
    fireEvent.change(textareas[0], { target: { value: errorText } });
    expect(screen.getByText('Error: Maximum 200 words exceeded.')).toBeInTheDocument();
    await delay(600);
  });

  it('enables submission only when all 3 textareas have valid word counts and submits successfully', async () => {
    const mockActivity = {
      id: 12,
      title: 'Structured Reflection',
      description: 'Daily prompt instruction',
      group_name: 'Group 3',
      day_number: 1,
      submitted_today: false,
    };

    (api.get as any).mockResolvedValue({ data: mockActivity });
    (api.post as any).mockResolvedValue({ data: { success: true } });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Entry 1: Pleasure')).toBeInTheDocument();
    });

    const textareas = screen.getAllByRole('textbox');
    const validText = Array(25).fill('word').join(' ');

    // Fill in textarea 1 & 2
    fireEvent.change(textareas[0], { target: { value: validText } });
    fireEvent.change(textareas[1], { target: { value: validText } });
    
    // Submit button should still be disabled
    let submitBtn = screen.getByRole('button', { name: /Submit/i });
    expect(submitBtn).toBeDisabled();

    // Fill in textarea 3
    fireEvent.change(textareas[2], { target: { value: validText } });

    // Submit button should now be enabled
    submitBtn = screen.getByRole('button', { name: /Submit/i });
    expect(submitBtn).not.toBeDisabled();

    // Submit form
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/activities/daily/submit/', {
        activity: 12,
        entry_1: validText,
        entry_2: validText,
        entry_3: validText,
      });
    });
    await delay(600);
  });

  it('saves draft to local storage on change and restores it on reload', async () => {
    const mockActivity = {
      id: 12,
      title: 'Structured Reflection',
      description: 'Daily prompt instruction',
      group_name: 'Group 3',
      day_number: 1,
      submitted_today: false,
    };

    (api.get as any).mockResolvedValue({ data: mockActivity });

    // 1. Render and enter some text
    const { unmount } = renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Entry 1: Pleasure')).toBeInTheDocument();
    });

    const textareas = screen.getAllByRole('textbox');
    fireEvent.change(textareas[0], { target: { value: 'Draft Text for Entry 1' } });

    // Verify draft saved to localStorage
    const savedDraft = JSON.parse(localStorage.getItem('activity_draft_12') || '{}');
    expect(savedDraft.entry1).toBe('Draft Text for Entry 1');

    // 2. Unmount and re-render component to simulate refresh
    unmount();
    renderComponent();

    await waitFor(() => {
      const refreshedTextareas = screen.getAllByRole('textbox');
      expect((refreshedTextareas[0] as HTMLTextAreaElement).value).toBe('Draft Text for Entry 1');
    });
    await delay(600);
  });

  it('renders read-only view and lock message when activity has already been submitted', async () => {
    const mockActivity = {
      id: 12,
      title: 'Structured Reflection',
      description: 'Daily prompt instruction',
      group_name: 'Group 3',
      day_number: 1,
      submitted_today: true,
      entry_1: 'Old entry 1 content',
      entry_2: 'Old entry 2 content',
      entry_3: 'Old entry 3 content',
    };

    (api.get as any).mockResolvedValue({ data: mockActivity });

    renderComponent();

    await waitFor(() => {
      const textareas = screen.getAllByRole('textbox');
      expect(textareas[0]).toHaveAttribute('readonly');
      expect((textareas[0] as HTMLTextAreaElement).value).toBe('Old entry 1 content');
      expect((textareas[1] as HTMLTextAreaElement).value).toBe('Old entry 2 content');
      expect((textareas[2] as HTMLTextAreaElement).value).toBe('Old entry 3 content');

      expect(screen.getByText('Daily activity submitted and locked.')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Submit/i })).not.toBeInTheDocument();
    });
  });

  it('renders Group 4 Day 2 schedule, definitions, and examples correctly in English', async () => {
    const mockActivity = {
      id: 14,
      title: 'Combined Reflection',
      description: 'Combined daily prompt instruction | اردو ہدایات',
      group_name: 'Group 4',
      day_number: 2, // Day 2 should show Relationships, Accomplishment, Pleasure with Gratitude
      submitted_today: false,
    };

    (api.get as any).mockResolvedValue({ data: mockActivity });

    renderComponent('14');

    await waitFor(() => {
      // Entry labels - Group 4 has Gratitude combined labels
      expect(screen.getByText('Entry 1: Positive Relationships with Gratitude')).toBeInTheDocument();
      expect(screen.getByText('Entry 2: Accomplishment with Gratitude')).toBeInTheDocument();
      expect(screen.getByText('Entry 3: Pleasure with Gratitude')).toBeInTheDocument();

      // Definitions & Examples - English
      expect(screen.getByText('A meaningful interaction today that you feel grateful for. Describe what happened, why you are grateful, and what or who made it possible.')).toBeInTheDocument();
      expect(screen.getByText(/A friend called to check on me out of nowhere/)).toBeInTheDocument();

      expect(screen.getByText('Something you did well today that you feel grateful for. Describe what you accomplished, why you are grateful for it, and what or who made it possible.')).toBeInTheDocument();
      expect(screen.getByText(/Submitted the section to my supervisor before deadline/)).toBeInTheDocument();

      expect(screen.getByText('An enjoyable moment today that you feel grateful for. Describe what happened, why you are grateful for it, and what or who made it possible.')).toBeInTheDocument();
      expect(screen.getByText(/My sister made karak chai/)).toBeInTheDocument();
    });
  });

  it('renders Group 4 labels and definitions in Urdu when language is ur', async () => {
    mockLanguage = 'ur';
    const mockActivity = {
      id: 14,
      title: 'Combined Reflection',
      description: 'Combined daily prompt instruction | اردو ہدایات',
      group_name: 'Group 4',
      day_number: 2, // Day 2
      submitted_today: false,
    };

    (api.get as any).mockResolvedValue({ data: mockActivity });

    renderComponent('14');

    await waitFor(() => {
      // Entry labels in Urdu
      expect(screen.getByText('اندراج 1: مثبت تعلقات بمعہ شکر گزاری')).toBeInTheDocument();
      expect(screen.getByText('اندراج 2: کامیابی بمعہ شکر گزاری')).toBeInTheDocument();
      expect(screen.getByText('اندراج 3: لطف بمعہ شکر گزاری')).toBeInTheDocument();

      // Definitions - Urdu
      expect(screen.getByText('آج کا کوئی بامقصد رابطہ جس کے لیے آپ شکر گزار ہیں۔ بیان کریں کہ کیا ہوا، آپ کیوں شکر گزار ہیں، اور کس یا کس چیز نے اسے ممکن بنایا۔')).toBeInTheDocument();
      expect(screen.getByText('آج کوئی ایسا کام جو آپ نے اچھا کیا اور جس کے لیے آپ شکر گزار ہیں۔ بیان کریں کہ آپ نے کیا حاصل کیا، اس کے لیے کیوں شکر گزار ہیں، اور کس یا کس چیز نے اسے ممکن بنایا۔')).toBeInTheDocument();
      expect(screen.getByText('آج کا کوئی لطف بھرا لمحہ جس کے لیے آپ شکر گزار ہیں۔ بیان کریں کہ کیا ہوا، آپ اس کے لیے کیوں شکر گزار ہیں، اور کس یا کس چیز نے اسے ممکن بنایا۔')).toBeInTheDocument();
    });
  });
});
