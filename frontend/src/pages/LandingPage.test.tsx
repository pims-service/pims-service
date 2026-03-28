import { render, screen } from '@testing-library/react';
import LandingPage from './LandingPage';
import { BrowserRouter } from 'react-router-dom';

test('renders landing page headline', () => {
  render(
    <BrowserRouter>
      <LandingPage />
    </BrowserRouter>
  );
  const linkElement = screen.getByText(/Discover the Psychology of Achievement/i);
  expect(linkElement).toBeInTheDocument();
});
