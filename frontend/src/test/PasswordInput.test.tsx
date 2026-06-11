import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PasswordInput from '../components/Auth/PasswordInput';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe('PasswordInput', () => {
  it('toggles password visibility when the eye button is clicked', () => {
    render(
      <PasswordInput
        id="password"
        name="password"
        value="secret123"
        onChange={() => {}}
      />
    );

    const input = screen.getByDisplayValue('secret123');
    expect(input).toHaveAttribute('type', 'password');

    fireEvent.click(screen.getByRole('button', { name: 'auth.show_password' }));
    expect(input).toHaveAttribute('type', 'text');

    fireEvent.click(screen.getByRole('button', { name: 'auth.hide_password' }));
    expect(input).toHaveAttribute('type', 'password');
  });
});
