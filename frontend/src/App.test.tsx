import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import App from './App';

describe('App (лаб. №5)', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        available: false,
        city: 'X',
        message: 'E2E mock',
      }),
    } as any);
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('рендерит главную страницу и заголовок', async () => {
    render(<App />);
    expect(
      screen.getByRole('heading', {
        level: 1,
        name: /Система цензурирования изображений/,
      })
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText(/Загрузка блока погоды/)).not.toBeInTheDocument();
    });
  });
});
