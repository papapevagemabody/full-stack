import React from 'react';
import { render, waitFor } from '@testing-library/react';
import { HelmetProvider } from 'react-helmet-async';
import { MemoryRouter } from 'react-router-dom';
import Seo from '../Seo';

describe('Seo (лаб. №5)', () => {
  it('выставляет title и meta description', async () => {
    render(
      <HelmetProvider>
        <MemoryRouter initialEntries={['/']}>
          <Seo title="Заголовок страницы" description="Описание для поиска и соцсетей." canonicalPath="/" />
        </MemoryRouter>
      </HelmetProvider>
    );
    await waitFor(() => {
      expect(document.title).toBe('Заголовок страницы');
    });
    const meta = document.querySelector('meta[name="description"]');
    expect(meta).toHaveAttribute('content', 'Описание для поиска и соцсетей.');
  });

  it('noindex: robots meta', async () => {
    render(
      <HelmetProvider>
        <MemoryRouter>
          <Seo title="Логин" description="x" noindex canonicalPath="/login" />
        </MemoryRouter>
      </HelmetProvider>
    );
    await waitFor(() => {
      const robots = document.querySelector('meta[name="robots"]');
      expect(robots?.getAttribute('content')).toMatch(/noindex/);
    });
  });
});
