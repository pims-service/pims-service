import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import LandingPage from '../pages/LandingPage';
import { BrowserRouter } from 'react-router-dom';

describe('LandingPage', () => {
  it('renders progress banner', () => {
    render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );
    expect(screen.getByText(/Phase 1 Enrollment Now Open/i)).toBeDefined();
  });

  it('renders main headline', () => {
    render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );
    expect(screen.getByRole('heading', { name: /The Science of Human Achievement/i })).toBeDefined();
  });
});
