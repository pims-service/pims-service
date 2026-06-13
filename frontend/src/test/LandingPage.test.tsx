import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import LandingPage from '../pages/LandingPage';
import { BrowserRouter } from 'react-router-dom';

const landingTranslations: Record<string, string> = {
  'landing.tagline': 'A free, science-based wellbeing program',
  'landing.title': 'Welcome to Psycheversity!',
  'landing.collaboration': 'A research project of UKM in collaboration with PIMS, Islamabad.',
  'landing.intro_1': 'Psycheversity offers a free, online wellbeing program.',
  'landing.intro_2': 'Positive Psychology is the scientific study of wellbeing.',
  'landing.intro_3': 'The program consists of short daily writing activities.',
  'landing.registration_note': 'Registration is open.',
  'landing.register_now': 'Register Now',
  'landing.existing_participant': 'Existing Participant',
  'profile.account_deleted_success': 'Account Deleted Successfully',
};

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => landingTranslations[key] || key,
    i18n: { language: 'en' },
  }),
}));

describe('LandingPage', () => {
  it('renders bilingual landing content in English', () => {
    render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );

    expect(screen.getByText('A free, science-based wellbeing program')).toBeDefined();
    expect(screen.getByRole('heading', { name: /Welcome to Psycheversity!/i })).toBeDefined();
    expect(screen.getByRole('button', { name: /Home ہوم/i })).toBeDefined();
    expect(screen.getByRole('button', { name: /Information معلومات/i })).toBeDefined();
    expect(screen.getByRole('button', { name: /FAQ سوالات/i })).toBeDefined();
    expect(screen.getByRole('button', { name: /Crisis Resources ہنگامی مدد/i })).toBeDefined();
    expect(screen.getByRole('button', { name: /Contact رابطہ/i })).toBeDefined();
    expect(screen.getByRole('button', { name: /Registration رجسٹریشن/i })).toBeDefined();
  });
});
