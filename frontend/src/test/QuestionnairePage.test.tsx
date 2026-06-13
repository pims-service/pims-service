import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import QuestionnairePage from '../pages/QuestionnairePage';
import { questionnairesApi } from '../services/api';

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (str: string) => str,
    i18n: {
      changeLanguage: () => new Promise(() => {}),
      language: 'en',
    },
  }),
}));

// Mock the API service
vi.mock('../services/api', () => ({
  questionnairesApi: {
    getDetail: vi.fn(),
    createResponseSet: vi.fn(),
    saveDraftResponseSet: vi.fn(),
    submitResponseSet: vi.fn(),
    submitOptIn: vi.fn(),
  },
  groupsApi: {
    getGroups: vi.fn().mockResolvedValue({ data: [] }),
  }
}));

const mockQuestionnaire = {
  id: 'q-1',
  title: 'Longitudinal Scales',
  assessment_type: 'PSYCHOMETRIC',
  questions: [
    {
      id: 'ques-1',
      content: '[PERMA] How happy are you? | آپ کتنے خوش ہیں؟',
      type: 'SCALE',
      order: 1,
      required: true,
      options: [
        { id: 'opt-0', label: '0 - Never | کبھی نہیں', numeric_value: 0, order: 0 },
        { id: 'opt-10', label: '10 - Always | ہمیشہ', numeric_value: 10, order: 10 }
      ]
    },
    {
      id: 'ques-2',
      content: '[PERMA] How active are you? | آپ کتنے متحرک ہیں؟',
      type: 'SCALE',
      order: 2,
      required: true,
      options: [
        { id: 'opt-0', label: '0 - Never | کبھی نہیں', numeric_value: 0, order: 0 },
        { id: 'opt-10', label: '10 - Always | ہمیشہ', numeric_value: 10, order: 10 }
      ]
    },
    {
      id: 'ques-3',
      content: '[PHQ-9] Feeling down, depressed. | اداسی اور افسردگی۔',
      type: 'SCALE',
      order: 3,
      required: true,
      options: [
        { id: 'opt-p0', label: '0 - Not at all', numeric_value: 0, order: 0 },
        { id: 'opt-p3', label: '3 - Nearly every day', numeric_value: 3, order: 3 }
      ]
    }
  ]
};

const mockResponseSet = {
  id: 'rs-123',
  responses: []
};

const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

describe('QuestionnairePage Scale-Grouped Paging and Autosave', () => {
  beforeEach(() => {
    window.scrollTo = vi.fn();
    vi.clearAllMocks();
    (questionnairesApi.getDetail as any).mockResolvedValue({ data: mockQuestionnaire });
    (questionnairesApi.createResponseSet as any).mockResolvedValue({ data: mockResponseSet });
  });

  it('groups questions by scale, displays bilingual columns, and handles step pagination', async () => {
    render(
      <MemoryRouter initialEntries={['/questionnaires/q-1']}>
        <Routes>
          <Route path="/questionnaires/:id" element={<QuestionnairePage />} />
        </Routes>
      </MemoryRouter>
    );

    // Verify loading state is shown initially
    expect(screen.getByText(/Loading questionnaire.../i)).toBeInTheDocument();

    // Verify first scale group (PERMA) questions are loaded
    await waitFor(() => {
      expect(screen.getByText('Scale 1 / 2')).toBeInTheDocument();
      expect(screen.getByText('Longitudinal Scales')).toBeInTheDocument();
      // First question (bilingual)
      expect(screen.getByText('How happy are you?')).toBeInTheDocument();
      expect(screen.getByText('آپ کتنے خوش ہیں؟')).toBeInTheDocument();
      // Second question (bilingual)
      expect(screen.getByText('How active are you?')).toBeInTheDocument();
      expect(screen.getByText('آپ کتنے متحرک ہیں؟')).toBeInTheDocument();
      // Third question (PHQ-9) should NOT be visible yet
      expect(screen.queryByText('Feeling down, depressed.')).not.toBeInTheDocument();
    });

    // Continue button should be disabled initially (since required questions are not answered)
    const continueBtn = screen.getByRole('button', { name: /Continue/i });
    expect(continueBtn).toBeDisabled();
  });

  it('triggers debounced draft auto-saving when a response is updated', async () => {
    (questionnairesApi.saveDraftResponseSet as any).mockResolvedValue({ data: { success: true } });

    render(
      <MemoryRouter initialEntries={['/questionnaires/q-1']}>
        <Routes>
          <Route path="/questionnaires/:id" element={<QuestionnairePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Longitudinal Scales')).toBeInTheDocument();
    });

    // We have options 0 and 10 for ques-1
    const buttons = screen.getAllByRole('button');
    // Let's find the '0' option for the first question
    const zeroButton = buttons.find(b => b.textContent?.includes('0') && !b.textContent.includes('10'));
    expect(zeroButton).toBeDefined();

    // Click '0' response for question 1
    fireEvent.click(zeroButton!);

    // Verify saveDraftResponseSet is NOT called immediately
    expect(questionnairesApi.saveDraftResponseSet).not.toHaveBeenCalled();

    // Wait for the 500ms debounce timeout to complete
    await delay(600);

    // Verify it is auto-saved with draft response data
    expect(questionnairesApi.saveDraftResponseSet).toHaveBeenCalledTimes(1);
    expect(questionnairesApi.saveDraftResponseSet).toHaveBeenCalledWith(
      'rs-123',
      expect.arrayContaining([
        expect.objectContaining({
          question_id: 'ques-1',
          selected_option_id: 'opt-0'
        })
      ])
    );
  });

  it('shows bilingual safety resources modal when suicide risk is triggered', async () => {
    (questionnairesApi.submitResponseSet as any).mockResolvedValue({
      data: {
        id: 'rs-123',
        suicide_risk_triggered: true,
        suicide_risk_opt_in: null
      }
    });

    render(
      <MemoryRouter initialEntries={['/questionnaires/q-1']}>
        <Routes>
          <Route path="/questionnaires/:id" element={<QuestionnairePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Longitudinal Scales')).toBeInTheDocument();
    });

    // Answer the required questions for scale 1
    const buttons = screen.getAllByRole('button');
    const zeroButtons = buttons.filter(b => b.textContent?.includes('0') && !b.textContent.includes('10'));
    
    // Select options for questions
    fireEvent.click(zeroButtons[0]);
    fireEvent.click(zeroButtons[1]);

    // Wait for the Continue button to be enabled
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Continue/i })).not.toBeDisabled();
    });

    // Go to next scale
    const continueBtn = screen.getByRole('button', { name: /Continue/i });
    fireEvent.click(continueBtn);

    // Wait for the exit animation to complete and remove old DOM elements
    await delay(400);

    // Now on scale 2 (PHQ-9)
    await waitFor(() => {
      expect(screen.getByText('Scale 2 / 2')).toBeInTheDocument();
    });

    // Answer PHQ-9 item
    const phqButtons = screen.getAllByRole('button');
    const phqZero = phqButtons.find(b => b.textContent?.includes('0') && !b.textContent.includes('3'));
    fireEvent.click(phqZero!);

    // Wait for the Complete button to be enabled
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Complete/i })).not.toBeDisabled();
    });

    // Complete questionnaire submission
    const completeBtn = screen.getByRole('button', { name: /Complete/i });
    fireEvent.click(completeBtn);

    // Wait for the safety resources modal to be rendered
    await waitFor(() => {
      expect(screen.getByText('Support Resources Available')).toBeInTheDocument();
      expect(screen.getByText('امدادی وسائل دستیاب ہیں')).toBeInTheDocument();
      expect(screen.getByText('Umang')).toBeInTheDocument();
      expect(screen.getByText('Taskeen')).toBeInTheDocument();
      expect(screen.getByText('Rozan Counselling Helpline')).toBeInTheDocument();
      expect(screen.getByText('Emergency Rescue 1122')).toBeInTheDocument();
    });

    // Check opt-in checkbox
    const optInBox = screen.getByText(/Request follow-up/i);
    fireEvent.click(optInBox);

    // Mock opt-in submission
    (questionnairesApi.submitOptIn as any).mockResolvedValue({ data: { status: 'opt-in updated', suicide_risk_opt_in: true } });

    // Click Proceed
    const proceedBtn = screen.getByRole('button', { name: /Proceed/i });
    fireEvent.click(proceedBtn);

    // Wait for the opt-in API call
    await waitFor(() => {
      expect(questionnairesApi.submitOptIn).toHaveBeenCalledWith('rs-123', true);
    });
  });

  it('triggers safety resources modal immediately on page transition if local suicide risk is triggered', async () => {
    // Modify mockQuestionnaire to have a triggerable question on page 1
    const localMockQuestionnaire = {
      id: 'q-1',
      title: 'Longitudinal Scales',
      assessment_type: 'PSYCHOMETRIC',
      questions: [
        {
          id: 'ques-1',
          content: '[PHQ-9] Thoughts that you would be better off dead | خیالات کہ مرنا بہتر ہے',
          type: 'SCALE',
          order: 32, // PHQ-9 Item 9 trigger
          required: true,
          options: [
            { id: 'opt-0', label: '0 - Never', numeric_value: 0, order: 0 },
            { id: 'opt-2', label: '2 - More than half the days', numeric_value: 2, order: 2 }
          ]
        },
        {
          id: 'ques-2',
          content: '[GAD-7] Feeling nervous',
          type: 'SCALE',
          order: 33,
          required: true,
          options: [
            { id: 'opt-g0', label: '0 - Never', numeric_value: 0, order: 0 }
          ]
        }
      ]
    };
    (questionnairesApi.getDetail as any).mockResolvedValue({ data: localMockQuestionnaire });

    render(
      <MemoryRouter initialEntries={['/questionnaires/q-1']}>
        <Routes>
          <Route path="/questionnaires/:id" element={<QuestionnairePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Scale 1 / 2')).toBeInTheDocument();
    });

    // Select the risk option for question 1 (value 2)
    const options = screen.getAllByRole('button');
    const triggerOption = options.find(o => o.textContent?.includes('2') || o.textContent?.includes('More than half'));
    expect(triggerOption).toBeDefined();
    fireEvent.click(triggerOption!);

    // Wait for the Continue button to be enabled
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Continue/i })).not.toBeDisabled();
    });

    // Click Continue
    const continueBtn = screen.getByRole('button', { name: /Continue/i });
    fireEvent.click(continueBtn);

    // Verify the safety resources modal is shown immediately, before reaching page 2
    await waitFor(() => {
      expect(screen.getByText('Support Resources Available')).toBeInTheDocument();
    });

    // Click Proceed (mock opt-in first)
    (questionnairesApi.submitOptIn as any).mockResolvedValue({ data: { success: true } });
    const proceedBtn = screen.getByRole('button', { name: /Proceed/i });
    fireEvent.click(proceedBtn);

    // After proceeding, it should transition to scale 2
    await waitFor(() => {
      expect(screen.getByText('Scale 2 / 2')).toBeInTheDocument();
    });
  });
});

