import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import DeleteUserModal from '../components/Admin/DeleteUserModal';

describe('DeleteUserModal', () => {
  it('enables delete only when the exact confirmation phrase is entered', () => {
    const onConfirm = vi.fn();
    render(
      <DeleteUserModal
        isOpen
        username="tester"
        fullName="Test User"
        deleting={false}
        error={null}
        onClose={vi.fn()}
        onConfirm={onConfirm}
      />
    );

    const deleteButton = screen.getByRole('button', { name: /Delete User/i });
    expect(deleteButton).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/Type/i), { target: { value: 'Confirm Delete' } });
    expect(deleteButton).not.toBeDisabled();

    fireEvent.click(deleteButton);
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });
});
