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
    expect(screen.getByText(/Phase 1 Enrollment Open/i)).toBeDefined();
  });

  it('renders main headline', () => {
    render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );
    expect(screen.getByText(/Psychology of Achievement/i)).toBeDefined();
  });
});
