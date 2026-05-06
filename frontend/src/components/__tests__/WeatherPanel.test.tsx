import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import WeatherPanel from '../WeatherPanel';

describe('WeatherPanel (лаб. №5)', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('показывает данные при available=true', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        available: true,
        city: 'TestTown',
        country: 'RU',
        temperature_c: -5,
        wind_speed_kmh: 12,
        weather_code: 1,
        provider: 'open-meteo',
      }),
    } as any);

    render(<WeatherPanel />);

    await waitFor(() => {
      expect(screen.getByText(/TestTown/)).toBeInTheDocument();
    });
    expect(screen.getByText(/-5/)).toBeInTheDocument();
  });

  it('graceful degradation при available=false', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        available: false,
        city: 'X',
        message: 'Внешний API недоступен',
      }),
    } as any);

    render(<WeatherPanel />);

    await waitFor(() => {
      expect(screen.getByRole('status')).toBeInTheDocument();
    });
    expect(screen.getByText(/Внешний API недоступен/)).toBeInTheDocument();
  });

  it('ошибка сети', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('network'));

    render(<WeatherPanel />);

    await waitFor(() => {
      expect(screen.getByText(/network/i)).toBeInTheDocument();
    });
  });
});
