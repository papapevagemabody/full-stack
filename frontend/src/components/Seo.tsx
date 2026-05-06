import React from 'react';
import { Helmet } from 'react-helmet-async';
import { useLocation } from 'react-router-dom';
import { getPublicSiteUrl } from '../config/site';

export interface SeoProps {
  title: string;
  description: string;
  /** Путь без домена, напр. "/about" — для canonical */
  canonicalPath?: string;
  /** Закрытые страницы (кабинет, логин и т.д.) */
  noindex?: boolean;
  ogType?: string;
  /** JSON-LD объект (WebSite, Article, …) */
  jsonLd?: Record<string, unknown>;
}

/**
 * Лаб. №4: title, description, canonical, Open Graph, robots, JSON-LD.
 */
const Seo: React.FC<SeoProps> = ({
  title,
  description,
  canonicalPath,
  noindex = false,
  ogType = 'website',
  jsonLd,
}) => {
  const { pathname } = useLocation();
  const base = getPublicSiteUrl().replace(/\/$/, '');
  const pathForCanon = canonicalPath ?? pathname;
  const canonical =
    pathForCanon === '/' || pathForCanon === '' ? `${base}/` : `${base}${pathForCanon}`;

  return (
    <Helmet prioritizeSeoTags htmlAttributes={{ lang: 'ru' }}>
      <title>{title}</title>
      <meta name="description" content={description} />
      {noindex ? (
        <meta name="robots" content="noindex, nofollow" />
      ) : (
        <meta name="robots" content="index, follow" />
      )}
      <link rel="canonical" href={canonical} />

      <meta property="og:type" content={ogType} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={canonical} />
      <meta property="og:locale" content="ru_RU" />

      <meta name="twitter:card" content="summary" />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />

      {jsonLd ? (
        <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
      ) : null}
    </Helmet>
  );
};

export default Seo;
