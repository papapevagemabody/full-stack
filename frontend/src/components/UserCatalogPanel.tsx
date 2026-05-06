import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiService } from '../services/api';
import { usePermissions } from '../hooks/usePermissions';
import { useAuth } from '../contexts/AuthContext';
import '../pages/UserCatalog.css';

export interface UserAssetRow {
  id: number;
  user_id: number;
  owner_username?: string | null;
  title: string;
  description?: string | null;
  category: string;
  original_filename: string;
  content_type?: string | null;
  size_bytes: number;
  created_at?: string | null;
  updated_at?: string | null;
}

interface ListResponse {
  items: UserAssetRow[];
  total: number;
  page: number;
  page_size: number;
}

const CATALOG_KEYS = [
  'q',
  'category',
  'date_from',
  'date_to',
  'page',
  'page_size',
  'sort_by',
  'sort_order',
  'all_users',
] as const;

export interface UserCatalogPanelProps {
  /** Увеличьте, чтобы принудительно обновить список (после загрузки/цензуры и т.д.) */
  refreshTrigger?: number;
  onMeta?: (meta: { total: number; page: number }) => void;
  /** Скрыть верхний заголовок блока (когда заголовок уже на странице профиля) */
  hideTitle?: boolean;
}

const UserCatalogPanel: React.FC<UserCatalogPanelProps> = ({
  refreshTrigger = 0,
  onMeta,
  hideTitle = false,
}) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { isLoading: authLoading } = useAuth();
  const { hasPermission, isAdmin } = usePermissions();
  const [data, setData] = useState<ListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [draft, setDraft] = useState({
    q: '',
    category: '',
    dateFrom: '',
    dateTo: '',
    sortBy: 'created_at',
    sortOrder: 'desc' as 'asc' | 'desc',
    pageSize: 10,
    allUsers: false,
  });

  const syncDraftFromUrl = useCallback(() => {
    setDraft({
      q: searchParams.get('q') || '',
      category: searchParams.get('category') || '',
      dateFrom: searchParams.get('date_from') || '',
      dateTo: searchParams.get('date_to') || '',
      sortBy: searchParams.get('sort_by') || 'created_at',
      sortOrder: (searchParams.get('sort_order') === 'asc' ? 'asc' : 'desc') as 'asc' | 'desc',
      pageSize: Math.min(100, Math.max(1, parseInt(searchParams.get('page_size') || '10', 10) || 10)),
      allUsers: searchParams.get('all_users') === '1',
    });
  }, [searchParams]);

  useEffect(() => {
    syncDraftFromUrl();
  }, [syncDraftFromUrl]);

  const fetchList = useCallback(async () => {
    if (authLoading) {
      return;
    }
    if (!hasPermission('catalog.view')) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = (await apiService.getUserAssetsList({
        q: searchParams.get('q') || undefined,
        category: searchParams.get('category') || undefined,
        date_from: searchParams.get('date_from') || undefined,
        date_to: searchParams.get('date_to') || undefined,
        page: parseInt(searchParams.get('page') || '1', 10) || 1,
        page_size: parseInt(searchParams.get('page_size') || '10', 10) || 10,
        sort_by: searchParams.get('sort_by') || 'created_at',
        sort_order: searchParams.get('sort_order') || 'desc',
        all_users: searchParams.get('all_users') === '1' ? true : undefined,
      })) as ListResponse;
      setData(res);
    } catch (e: any) {
      let msg = e?.message || 'Ошибка загрузки каталога';
      if (/Not Found/i.test(msg)) {
        msg =
          'Каталог недоступен (404). Перезапустите backend с текущим кодом (роутер /user-assets) или задайте REACT_APP_API_URL на реальный адрес API.';
      }
      setError(msg);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [searchParams, hasPermission, authLoading]);

  useEffect(() => {
    void fetchList();
  }, [fetchList]);

  useEffect(() => {
    if (refreshTrigger > 0) {
      void fetchList();
    }
  }, [refreshTrigger, fetchList]);

  const onMetaRef = useRef(onMeta);
  onMetaRef.current = onMeta;
  useEffect(() => {
    if (data) {
      onMetaRef.current?.({ total: data.total, page: data.page });
    }
  }, [data]);

  const applyFilters = () => {
    const p = new URLSearchParams(searchParams);
    CATALOG_KEYS.forEach((k) => p.delete(k));
    p.set('tab', 'files');
    p.set('page', '1');
    if (draft.q.trim()) p.set('q', draft.q.trim());
    if (draft.category.trim()) p.set('category', draft.category.trim());
    if (draft.dateFrom) p.set('date_from', draft.dateFrom);
    if (draft.dateTo) p.set('date_to', draft.dateTo);
    p.set('sort_by', draft.sortBy);
    p.set('sort_order', draft.sortOrder);
    p.set('page_size', String(draft.pageSize));
    if (draft.allUsers && isAdmin) p.set('all_users', '1');
    setSearchParams(p);
  };

  const goPage = (n: number) => {
    const p = new URLSearchParams(searchParams);
    p.set('tab', 'files');
    p.set('page', String(Math.max(1, n)));
    setSearchParams(p);
  };

  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDesc, setUploadDesc] = useState('');
  const [uploadCategory, setUploadCategory] = useState('general');
  const [uploading, setUploading] = useState(false);
  const [uploadErr, setUploadErr] = useState<string | null>(null);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasPermission('catalog.manage') || !uploadFile) return;
    setUploading(true);
    setUploadErr(null);
    try {
      await apiService.uploadUserAsset(uploadFile, {
        title: uploadTitle || uploadFile.name,
        description: uploadDesc || undefined,
        category: uploadCategory,
      });
      setUploadFile(null);
      setUploadTitle('');
      setUploadDesc('');
      setUploadCategory('general');
      await fetchList();
    } catch (err: any) {
      setUploadErr(err?.message || 'Ошибка загрузки');
    } finally {
      setUploading(false);
    }
  };

  const [editRow, setEditRow] = useState<UserAssetRow | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editCategory, setEditCategory] = useState('');
  const [saving, setSaving] = useState(false);

  const openEdit = (row: UserAssetRow) => {
    setEditRow(row);
    setEditTitle(row.title);
    setEditDesc(row.description || '');
    setEditCategory(row.category);
  };

  const saveEdit = async () => {
    if (!editRow) return;
    setSaving(true);
    try {
      await apiService.updateUserAsset(editRow.id, {
        title: editTitle,
        description: editDesc || undefined,
        category: editCategory,
      });
      setEditRow(null);
      await fetchList();
    } catch (e: any) {
      setError(e?.message || 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const removeRow = async (id: number) => {
    if (!window.confirm('Удалить запись и файл в хранилище?')) return;
    try {
      await apiService.deleteUserAsset(id);
      await fetchList();
    } catch (e: any) {
      setError(e?.message || 'Ошибка удаления');
    }
  };

  const downloadRow = async (id: number) => {
    try {
      const { url } = await apiService.getUserAssetDownloadUrl(id);
      window.open(url, '_blank', 'noopener,noreferrer');
    } catch (e: any) {
      setError(e?.message || 'Не удалось получить ссылку');
    }
  };

  if (authLoading) {
    return (
      <div className="user-catalog user-catalog--embedded">
        <p className="user-catalog__hint">Проверка сессии…</p>
      </div>
    );
  }

  if (!hasPermission('catalog.view')) {
    return (
      <div className="user-catalog user-catalog--embedded">
        <p className="user-catalog__denied">Нет доступа к каталогу (нужно право catalog.view).</p>
      </div>
    );
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  const currentPage = data?.page || parseInt(searchParams.get('page') || '1', 10) || 1;
  const showOwnerColumn = isAdmin && searchParams.get('all_users') === '1';

  return (
    <div className="user-catalog user-catalog--embedded">
      {!hideTitle && (
        <>
          <h2 className="user-catalog__title">Каталог материалов</h2>
          <p className="user-catalog__hint">
            
          </p>
        </>
      )}
      {hideTitle && (
        <p className="user-catalog__hint user-catalog__hint--tight">
          
        </p>
      )}

      <section className="user-catalog__card">
        <h2>Фильтры и поиск</h2>
        <div className="user-catalog__filters">
          <label>
            Поиск
            <input
              value={draft.q}
              onChange={(e) => setDraft((d) => ({ ...d, q: e.target.value }))}
              placeholder="Название, описание, имя файла"
            />
          </label>
          <label>
            Категория
            <input
              value={draft.category}
              onChange={(e) => setDraft((d) => ({ ...d, category: e.target.value }))}
              placeholder="например general, docs"
            />
          </label>
          <label>
            Дата с
            <input
              type="date"
              value={draft.dateFrom}
              onChange={(e) => setDraft((d) => ({ ...d, dateFrom: e.target.value }))}
            />
          </label>
          <label>
            Дата по
            <input
              type="date"
              value={draft.dateTo}
              onChange={(e) => setDraft((d) => ({ ...d, dateTo: e.target.value }))}
            />
          </label>
          <label>
            Сортировка
            <select
              value={draft.sortBy}
              onChange={(e) => setDraft((d) => ({ ...d, sortBy: e.target.value }))}
            >
              <option value="created_at">По дате</option>
              <option value="title">По названию</option>
              <option value="size_bytes">По размеру</option>
              <option value="original_filename">По имени файла</option>
            </select>
          </label>
          <label>
            Порядок
            <select
              value={draft.sortOrder}
              onChange={(e) =>
                setDraft((d) => ({ ...d, sortOrder: e.target.value as 'asc' | 'desc' }))
              }
            >
              <option value="desc">По убыванию</option>
              <option value="asc">По возрастанию</option>
            </select>
          </label>
          <label>
            На странице
            <select
              value={draft.pageSize}
              onChange={(e) => setDraft((d) => ({ ...d, pageSize: parseInt(e.target.value, 10) }))}
            >
              {[5, 10, 20, 50].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
          {isAdmin && (
            <label className="user-catalog__check">
              <input
                type="checkbox"
                checked={draft.allUsers}
                onChange={(e) => setDraft((d) => ({ ...d, allUsers: e.target.checked }))}
              />
              Все пользователи
            </label>
          )}
        </div>
        <button type="button" className="user-catalog__btn user-catalog__btn--primary" onClick={applyFilters}>
          Применить
        </button>
      </section>

      {hasPermission('catalog.manage') && (
        <section className="user-catalog__card">
          <h2>Загрузка файла</h2>
          <form onSubmit={handleUpload} className="user-catalog__upload">
            <input type="file" onChange={(e) => setUploadFile(e.target.files?.[0] || null)} required />
            <input
              placeholder="Название"
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
            />
            <input
              placeholder="Описание (необязательно)"
              value={uploadDesc}
              onChange={(e) => setUploadDesc(e.target.value)}
            />
            <input
              placeholder="Категория"
              value={uploadCategory}
              onChange={(e) => setUploadCategory(e.target.value)}
            />
            <button type="submit" disabled={uploading || !uploadFile}>
              {uploading ? 'Загрузка…' : 'Отправить'}
            </button>
          </form>
          {uploadErr && <p className="user-catalog__err">{uploadErr}</p>}
          <p className="user-catalog__small">
            Допустимые расширения и размер — как в настройках сервера (обычно до 10 МБ).
          </p>
        </section>
      )}

      <section className="user-catalog__card">
        <h2>Список</h2>
        {loading ? (
          <p>Загрузка…</p>
        ) : error ? (
          <p className="user-catalog__err">{error}</p>
        ) : !data?.items.length ? (
          <p>Нет записей.</p>
        ) : (
          <>
            <table className="user-catalog__table">
              <thead>
                <tr>
                  <th>ID</th>
                  {showOwnerColumn && <th>Владелец</th>}
                  <th>Название</th>
                  <th>Категория</th>
                  <th>Файл</th>
                  <th>Размер</th>
                  <th>Создано</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {data.items.map((row) => (
                  <tr key={row.id}>
                    <td>{row.id}</td>
                    {showOwnerColumn && <td>{row.owner_username || row.user_id}</td>}
                    <td>{row.title}</td>
                    <td>{row.category}</td>
                    <td>{row.original_filename}</td>
                    <td>{(row.size_bytes / 1024).toFixed(1)} КБ</td>
                    <td>{row.created_at ? new Date(row.created_at).toLocaleString() : '—'}</td>
                    <td className="user-catalog__actions">
                      <button type="button" onClick={() => downloadRow(row.id)}>
                        Скачать
                      </button>
                      {hasPermission('catalog.manage') && (
                        <>
                          <button type="button" onClick={() => openEdit(row)}>
                            Изменить
                          </button>
                          <button type="button" onClick={() => removeRow(row.id)}>
                            Удалить
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="user-catalog__pager">
              <button type="button" disabled={currentPage <= 1} onClick={() => goPage(currentPage - 1)}>
                Назад
              </button>
              <span>
                Стр. {currentPage} / {totalPages} (всего {data.total})
              </span>
              <button
                type="button"
                disabled={currentPage >= totalPages}
                onClick={() => goPage(currentPage + 1)}
              >
                Вперёд
              </button>
            </div>
          </>
        )}
      </section>

      {editRow && (
        <div className="user-catalog__modal">
          <div className="user-catalog__modal-inner">
            <h3>Редактирование #{editRow.id}</h3>
            <label>
              Название
              <input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} />
            </label>
            <label>
              Описание
              <textarea value={editDesc} onChange={(e) => setEditDesc(e.target.value)} rows={3} />
            </label>
            <label>
              Категория
              <input value={editCategory} onChange={(e) => setEditCategory(e.target.value)} />
            </label>
            <div className="user-catalog__modal-actions">
              <button type="button" onClick={() => setEditRow(null)}>
                Отмена
              </button>
              <button type="button" disabled={saving} onClick={() => void saveEdit()}>
                Сохранить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserCatalogPanel;
