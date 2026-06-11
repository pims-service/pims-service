import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ForgotPasswordPage from '../pages/ForgotPasswordPage';
import api from '../services/api';

vi.mock('../services/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: any) => {
      const keys: Record<string, string> = {
        'forgot_password.request_title': 'Reset password',
        'forgot_password.request_subtitle': 'Enter your email address to receive a reset code',
        'forgot_password.email_label': 'Email Address',
        'forgot_password.send_code_btn': 'Send Reset Code',
        'forgot_password.back_to_login': 'Back to Sign In',
        'forgot_password.reset_title': 'Enter reset code',
        'forgot_password.reset_subtitle': `We sent a 6-digit code to ${options?.email}`,
        'forgot_password.otp_label': 'Verification Code',
        'forgot_password.verify_code_btn': 'Verify Code',
        'forgot_password.set_password_title': 'Set new password',
        'forgot_password.set_password_subtitle': 'Choose a strong password to secure your account',
        'forgot_password.new_password_label': 'New Password',
        'forgot_password.confirm_password_label': 'Confirm New Password',
        'forgot_password.reset_password_btn': 'Reset Password',
        'forgot_password.password_mismatch': 'Passwords do not match.',
      };
      return keys[key] || key;
    },
  }),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual as any,
    useNavigate: () => mockNavigate,
  };
});

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders request password reset phase initially', () => {
    render(
      <MemoryRouter>
        <ForgotPasswordPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Reset password')).toBeInTheDocument();
    expect(screen.getByText('Enter your email address to receive a reset code')).toBeInTheDocument();
    expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Send Reset Code/i })).toBeInTheDocument();
  });

  it('navigates through email request, OTP verification, and password reset successfully', async () => {
    // Mock the 3 POST requests
    (api.post as any)
      .mockResolvedValueOnce({ data: { message: 'Code sent' } }) // Request
      .mockResolvedValueOnce({ data: { message: 'OTP verified' } }) // Verify
      .mockResolvedValueOnce({ data: { message: 'Password reset successful' } }); // Reset

    render(
      <MemoryRouter>
        <ForgotPasswordPage />
      </MemoryRouter>
    );

    // 1. Submit email (Phase 'request')
    const emailInput = screen.getByLabelText('Email Address');
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /Send Reset Code/i }));

    expect(api.post).toHaveBeenCalledWith('/auth/forgot-password/', { email: 'test@example.com' });

    // Transition to Phase 'verify'
    await waitFor(() => {
      expect(screen.getByText('Enter reset code')).toBeInTheDocument();
    }, { timeout: 2000 });

    expect(screen.getByText('We sent a 6-digit code to test@example.com')).toBeInTheDocument();
    expect(screen.getByLabelText('Verification Code')).toBeInTheDocument();
    
    // Check that password fields are NOT visible yet
    expect(screen.queryByLabelText('New Password')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Confirm New Password')).not.toBeInTheDocument();

    // 2. Submit OTP (Phase 'verify')
    const otpInput = screen.getByLabelText('Verification Code');
    fireEvent.change(otpInput, { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: /Verify Code/i }));

    expect(api.post).toHaveBeenCalledWith('/auth/verify-reset-otp/', { email: 'test@example.com', otp: '123456' });

    // Transition to Phase 'reset'
    await waitFor(() => {
      expect(screen.getByText('Set new password')).toBeInTheDocument();
    }, { timeout: 2000 });

    expect(screen.getByLabelText('New Password')).toBeInTheDocument();
    expect(screen.getByLabelText('Confirm New Password')).toBeInTheDocument();
    expect(screen.queryByLabelText('Verification Code')).not.toBeInTheDocument();

    // 3. Submit Passwords (Phase 'reset')
    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'Password123!' } });
    fireEvent.change(screen.getByLabelText('Confirm New Password'), { target: { value: 'Password123!' } });
    fireEvent.click(screen.getByRole('button', { name: /Reset Password/i }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/auth/reset-password/', {
        email: 'test@example.com',
        otp: '123456',
        password: 'Password123!',
        confirm_password: 'Password123!',
      });
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login', {
        state: { message: 'forgot_password.reset_success_banner' }
      });
    });
  });

  it('shows error if passwords do not match during reset phase', async () => {
    (api.post as any)
      .mockResolvedValueOnce({ data: { message: 'Code sent' } })
      .mockResolvedValueOnce({ data: { message: 'OTP verified' } });

    render(
      <MemoryRouter>
        <ForgotPasswordPage />
      </MemoryRouter>
    );

    // Transition to Phase 'verify'
    fireEvent.change(screen.getByLabelText('Email Address'), { target: { value: 'test@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /Send Reset Code/i }));

    await waitFor(() => {
      expect(screen.getByLabelText('Verification Code')).toBeInTheDocument();
    }, { timeout: 2000 });

    // Transition to Phase 'reset'
    fireEvent.change(screen.getByLabelText('Verification Code'), { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: /Verify Code/i }));

    await waitFor(() => {
      expect(screen.getByLabelText('New Password')).toBeInTheDocument();
    }, { timeout: 2000 });

    // Fill details with mismatching passwords
    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'Password123!' } });
    fireEvent.change(screen.getByLabelText('Confirm New Password'), { target: { value: 'DifferentPass123!' } });
    fireEvent.click(screen.getByRole('button', { name: /Reset Password/i }));

    expect(screen.getByText('Passwords do not match.')).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledTimes(2); // Request + Verify only
  });
});
