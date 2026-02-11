import { useState, useEffect, useMemo } from 'react'
import { getTools, toggleTool } from '../api'
import { useT } from '../i18n'

function Tools() {
  const { t } = useT()
  const [tools, setTools] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState(null)
  const [search, setSearch] = useState('')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')

  useEffect(() => {
    loadTools()
  }, [])

  async function loadTools() {
    try {
      const data = await getTools()
      setTools(data.tools || [])
    } catch (e) {
      console.error('Failed to load tools:', e)
    } finally {
      setLoading(false)
    }
  }

  async function handleToggle(name, enabled) {
    try {
      await toggleTool(name, enabled)
      setTools(tools.map(t => 
        t.name === name ? { ...t, enabled } : t
      ))
      setToast({ type: 'success', message: t('toast.tool_toggled', { state: enabled ? t('toast.enabled') : t('toast.disabled') }) })
    } catch (e) {
      setToast({ type: 'error', message: e.message })
    }
    setTimeout(() => setToast(null), 3000)
  }

  // Get unique sources for filter
  const sources = useMemo(() => {
    const srcSet = new Set(tools.map(t => t.source || 'builtin'))
    return ['all', ...Array.from(srcSet).sort()]
  }, [tools])

  // Filter tools
  const filteredTools = useMemo(() => {
    return tools.filter(tool => {
      // Search filter
      if (search) {
        const searchLower = search.toLowerCase()
        const nameMatch = tool.name.toLowerCase().includes(searchLower)
        const descMatch = (tool.description || '').toLowerCase().includes(searchLower)
        if (!nameMatch && !descMatch) return false
      }
      
      // Source filter
      if (sourceFilter !== 'all') {
        const toolSource = tool.source || 'builtin'
        if (toolSource !== sourceFilter) return false
      }
      
      // Status filter
      if (statusFilter === 'enabled' && !tool.enabled) return false
      if (statusFilter === 'disabled' && tool.enabled !== false) return false
      
      return true
    })
  }, [tools, search, sourceFilter, statusFilter])

  // Stats
  const stats = useMemo(() => ({
    total: tools.length,
    enabled: tools.filter(t => t.enabled !== false).length,
    disabled: tools.filter(t => t.enabled === false).length,
    mcp: tools.filter(t => (t.source || '').startsWith('mcp:')).length,
    builtin: tools.filter(t => !t.source || t.source === 'builtin').length
  }), [tools])

  function getSourceBadge(source) {
    if (!source || source === 'builtin') {
      return <span className="badge badge-blue">builtin</span>
    }
    if (source.startsWith('mcp:')) {
      const server = source.replace('mcp:', '')
      return <span className="badge badge-purple">MCP: {server}</span>
    }
    if (source.startsWith('skill:')) {
      return <span className="badge badge-green">skill</span>
    }
    return <span className="badge">{source}</span>
  }

  if (loading) {
    return <div className="loading"><div className="spinner"></div>{t('common.loading')}</div>
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">{t('tools.title')}</h1>
        <p className="page-subtitle">{t('tools.subtitle')}</p>
      </div>

      {/* Stats */}
      <div className="stats-row" style={{ marginBottom: '20px' }}>
        <div className="stat-card">
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">Всего</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: 'var(--success)' }}>{stats.enabled}</div>
          <div className="stat-label">Включено</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: 'var(--text-dim)' }}>{stats.disabled}</div>
          <div className="stat-label">Выключено</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: 'var(--primary)' }}>{stats.mcp}</div>
          <div className="stat-label">MCP</div>
        </div>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '20px', padding: '16px' }}>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ flex: '1', minWidth: '200px' }}>
            <input
              type="text"
              placeholder="🔍 Поиск по названию или описанию..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
          <div>
            <select value={sourceFilter} onChange={e => setSourceFilter(e.target.value)}>
              <option value="all">Все источники</option>
              {sources.filter(s => s !== 'all').map(src => (
                <option key={src} value={src}>{src}</option>
              ))}
            </select>
          </div>
          <div>
            <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
              <option value="all">Все статусы</option>
              <option value="enabled">Включённые</option>
              <option value="disabled">Выключенные</option>
            </select>
          </div>
          <div style={{ color: 'var(--text-dim)', fontSize: '13px' }}>
            Показано: {filteredTools.length} из {tools.length}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: '50px' }}>Вкл</th>
              <th style={{ width: '250px' }}>Инструмент</th>
              <th>Описание</th>
              <th style={{ width: '120px' }}>Источник</th>
            </tr>
          </thead>
          <tbody>
            {filteredTools.map(tool => (
              <tr key={tool.name} className={tool.enabled === false ? 'row-disabled' : ''}>
                <td>
                  <label className="toggle-switch toggle-sm">
                    <input 
                      type="checkbox"
                      checked={tool.enabled ?? true}
                      onChange={e => handleToggle(tool.name, e.target.checked)}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </td>
                <td>
                  <div style={{ fontWeight: 500 }}>
                    {tool.name}
                  </div>
                </td>
                <td>
                  <div style={{ 
                    color: 'var(--text-dim)', 
                    fontSize: '13px',
                    maxWidth: '500px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {tool.description || '—'}
                  </div>
                </td>
                <td>
                  {getSourceBadge(tool.source)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredTools.length === 0 && (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-dim)' }}>
            {search || sourceFilter !== 'all' || statusFilter !== 'all' 
              ? 'Ничего не найдено' 
              : t('tools.no_tools')}
          </div>
        )}
      </div>

      {toast && (
        <div className={`toast ${toast.type}`}>
          {toast.message}
        </div>
      )}
    </div>
  )
}

export default Tools
