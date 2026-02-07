import React, { useState, useEffect } from 'react';

const API_BASE = '/api/admin';

function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    loadTasks();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadTasks, 30000);
    return () => clearInterval(interval);
  }, []);

  async function loadTasks() {
    try {
      const res = await fetch(`${API_BASE}/tasks`);
      const data = await res.json();
      setTasks(data.tasks || []);
    } catch (e) {
      console.error('Failed to load tasks:', e);
    } finally {
      setLoading(false);
    }
  }

  async function cancelTask(taskId) {
    if (!window.confirm(`Cancel task ${taskId}?`)) return;
    
    try {
      const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        setToast({ type: 'success', message: 'Task cancelled' });
        loadTasks();
      } else {
        throw new Error('Failed to cancel');
      }
    } catch (e) {
      setToast({ type: 'error', message: e.message });
    }
    setTimeout(() => setToast(null), 3000);
  }

  function formatTimeLeft(minutes) {
    if (minutes < 0) return 'overdue';
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  }

  if (loading) {
    return <div className="loading"><div className="spinner"></div>Loading...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">⏰ Scheduled Tasks</h1>
        <p className="page-subtitle">Agent's scheduled and recurring tasks</p>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Active Tasks ({tasks.length})</h2>
          <button onClick={loadTasks} className="btn btn-secondary btn-sm">Refresh</button>
        </div>

        {tasks.length === 0 ? (
          <p style={{ color: 'var(--text-dim)', textAlign: 'center', padding: '40px' }}>
            No scheduled tasks. Agent can create tasks using the <code>schedule_task</code> tool.
          </p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>User</th>
                <th>Type</th>
                <th>Content</th>
                <th>Next Run</th>
                <th>Time Left</th>
                <th>Recurring</th>
                <th>Source</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <tr key={task.id}>
                  <td>
                    <code style={{ fontSize: '11px' }}>{task.id.substring(0, 15)}...</code>
                  </td>
                  <td>{task.user_id}</td>
                  <td>
                    <span className={`badge ${task.type === 'agent' ? 'badge-primary' : 'badge-secondary'}`}>
                      {task.type}
                    </span>
                  </td>
                  <td style={{ maxWidth: '300px' }}>
                    <div style={{ 
                      overflow: 'hidden', 
                      textOverflow: 'ellipsis', 
                      whiteSpace: 'nowrap',
                      fontSize: '13px'
                    }}>
                      {task.content}
                    </div>
                  </td>
                  <td style={{ fontSize: '12px', whiteSpace: 'nowrap' }}>
                    {task.next_run}
                  </td>
                  <td>
                    <span style={{ 
                      color: task.time_left_minutes < 5 ? 'var(--accent)' : 'inherit',
                      fontWeight: task.time_left_minutes < 5 ? 'bold' : 'normal'
                    }}>
                      {formatTimeLeft(task.time_left_minutes)}
                    </span>
                  </td>
                  <td>
                    {task.recurring ? (
                      <span style={{ color: 'var(--success)' }}>
                        🔄 every {task.interval_minutes}m
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-dim)' }}>once</span>
                    )}
                  </td>
                  <td>
                    <span className={`badge ${task.source === 'userbot' ? 'badge-warning' : 'badge-info'}`}>
                      {task.source === 'userbot' ? '👤' : '🤖'} {task.source}
                    </span>
                  </td>
                  <td>
                    <button 
                      onClick={() => cancelTask(task.id)} 
                      className="btn btn-danger btn-sm"
                    >
                      Cancel
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card" style={{ marginTop: '20px' }}>
        <div className="card-header">
          <h2 className="card-title">📖 Task Types</h2>
        </div>
        <div style={{ padding: '15px' }}>
          <table className="table" style={{ marginBottom: 0 }}>
            <tbody>
              <tr>
                <td><code>message</code></td>
                <td>Send a reminder message to the user</td>
              </tr>
              <tr>
                <td><code>agent</code></td>
                <td>Run the agent with a prompt (can use tools, search, etc.)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {toast && (
        <div className={`toast ${toast.type}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}

export default Tasks;
