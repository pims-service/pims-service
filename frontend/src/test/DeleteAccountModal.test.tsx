import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import DeleteAccountModal from '../components/Auth/DeleteAccountModal';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: { phrase?: string }) => {
      if (key === 'profile.delete_account_password_label') {
        return 'Enter your password';
      }
      if (key === 'profile.delete_account_confirmation_label') {
        return `Type ${options?.phrase} to confirm`;
      }
      return key;
    },
  }),
}));

describe('DeleteAccountModal', () => {
  it('enables delete only when confirmation phrase and password are entered', () => {
    const onConfirm = vi.fn();
    render(
      <DeleteAccountModal
        isOpen
        username="tester"
        deleting={false}
        error={null}
        onClose={vi.fn()}
        onConfirm={onConfirm}
      />
    );

    const deleteButton = screen.getByRole('button', { name: 'profile.delete_account_confirm_button' });
    expect(deleteButton).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/Type tester Confirm Delete to confirm/i), {
      target: { value: 'tester Confirm Delete' },
    });
    fireEvent.change(screen.getByLabelText('Enter your password'), {
      target: { value: 'password123' },
    });
    expect(deleteButton).not.toBeDisabled();

    fireEvent.click(deleteButton);
    expect(onConfirm).toHaveBeenCalledWith('tester Confirm Delete', 'password123');
  });
});
