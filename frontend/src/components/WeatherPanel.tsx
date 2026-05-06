import React, { useCallback, useEffect, useState } from 'react';
import { apiService, PublicWeatherPayload } from '../services/api';
import './WeatherPanel.css';

/**
 * Лаб. №4: UI для стороннего API (погода Open-Meteo через backend).
 * Состояния: загрузка, данные, пусто/ошибка, graceful degradation.
 */
const WeatherPanel: React.FC = () => {
  const [city, setCity] = useState('Москва');
  const [draft, setDraft] = useState('Москва');
  const [data, setData] = useState<PublicWeatherPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async (c: string) => {
    setLoading(true);
    setErr(null);
    try {
      const res = await apiService.fetchPublicWeather(c);
      setData(res);
    } catch (e: any) {
      setErr(e?.message || 'Не удалось связаться с сервером');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(city);
  }, [city, load]);

  return (
    <section className="weather-panel" aria-labelledby="weather-heading">
      <h2 id="weather-heading">Погода (сторонний API)</h2>
      <p className="weather-panel__hint">
        Данные: Open-Meteo через защищённый backend (таймауты, повторы, лимит запросов).
      </p>
      <form
        className="weather-panel__form"
        onSubmit={(e) => {
          e.preventDefault();
          const v = draft.trim() || 'Москва';
          setCity(v);
        }}
      >
        <label>
          Город
          <input
            type="text"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            maxLength={80}
            placeholder="Например, Санкт-Петербург"
            aria-label="Название города"
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? 'Запрос…' : 'Обновить'}
        </button>
      </form>

      {loading && !data && <p className="weather-panel__state">Загрузка…</p>}
      {err && <p className="weather-panel__err">{err}</p>}

      {data && !data.available && (
        <div className="weather-panel__fallback" role="status">
          <p>
            <strong>Сервис погоды недоступен.</strong> {data.message || 'Попробуйте позже.'}
          </p>
          <p className="weather-panel__muted">Основной функционал приложения не затронут.</p>
        </div>
      )}

      {data && data.available && (
        <dl className="weather-panel__data">
          <dt>Город</dt>
          <dd>
            {data.city}
            {data.country ? ` (${data.country})` : ''}
          </dd>
          <dt>Температура</dt>
          <dd>{data.temperature_c != null ? `${data.temperature_c} °C` : '—'}</dd>
          <dt>Ветер</dt>
          <dd>{data.wind_speed_kmh != null ? `${data.wind_speed_kmh} км/ч` : '—'}</dd>
          <dt>Код погоды (WMO)</dt>
          <dd>{data.weather_code ?? '—'}</dd>
        </dl>
      )}
    </section>
  );
};

export default WeatherPanel;
