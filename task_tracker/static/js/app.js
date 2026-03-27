/* === O365 Task Tracker — Frontend JS === */

// --- Task Status Update ---
function updateTaskStatus(taskId, newStatus) {
    fetch(`/api/task/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
    })
    .then(r => {
        if (!r.ok) throw new Error('Update failed');
        return r.json();
    })
    .then(() => {
        // Refresh stats without full reload
        refreshStats();
        showToast(`Task updated to "${newStatus.replace('_', ' ')}"`);
    })
    .catch(err => showToast('Failed to update task', 'error'));
}

// --- Generic Field Update (used on detail page) ---
function updateField(taskId, field, value) {
    fetch(`/api/task/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [field]: value }),
    })
    .then(r => {
        if (!r.ok) throw new Error('Update failed');
        return r.json();
    })
    .then(() => showToast('Saved'))
    .catch(err => showToast('Failed to save', 'error'));
}

// --- Delete Task ---
function deleteTask(taskId) {
    if (!confirm('Delete this task? This cannot be undone.')) return;
    fetch(`/api/task/${taskId}`, { method: 'DELETE' })
    .then(r => {
        if (!r.ok) throw new Error('Delete failed');
        window.location.href = '/';
    })
    .catch(err => showToast('Failed to delete task', 'error'));
}

// --- Refresh Stats ---
function refreshStats() {
    fetch('/api/stats')
    .then(r => r.json())
    .then(stats => {
        const mapping = {
            'total': '.stat-card:nth-child(1) .stat-number',
            'new': '.stat-new .stat-number',
            'in_progress': '.stat-progress .stat-number',
            'waiting': '.stat-waiting .stat-number',
            'completed': '.stat-done .stat-number',
            'urgent_active': '.stat-urgent .stat-number',
            'overdue': '.stat-overdue .stat-number',
        };
        for (const [key, selector] of Object.entries(mapping)) {
            const el = document.querySelector(selector);
            if (el && stats[key] !== undefined) {
                el.textContent = stats[key];
            }
        }
    })
    .catch(() => {});
}

// --- Create Task Modal ---
function openCreateModal() {
    document.getElementById('createModal').style.display = 'flex';
}

function closeCreateModal() {
    document.getElementById('createModal').style.display = 'none';
}

// Close modal on backdrop click
document.addEventListener('click', function(e) {
    const modal = document.getElementById('createModal');
    if (modal && e.target === modal) {
        closeCreateModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeCreateModal();
    }
});

// --- Toast Notifications ---
function showToast(message, type = 'success') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 1.5rem;
        right: 1.5rem;
        padding: 0.75rem 1.25rem;
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 500;
        color: #fff;
        background: ${type === 'error' ? '#d63031' : '#00b894'};
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 300;
        opacity: 0;
        transform: translateY(10px);
        transition: all 0.2s ease;
    `;
    document.body.appendChild(toast);

    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    });

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 200);
    }, 2500);
}

// --- Auto-dismiss flash messages ---
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.flash').forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transition = 'opacity 0.3s';
            setTimeout(() => flash.remove(), 300);
        }, 5000);
    });
});

// --- Auto-Sync ---
(function() {
    const SYNC_INTERVAL = 5 * 60 * 1000; // 5 minutes
    let syncTimer = null;

    function updateSyncStatus(text, syncing) {
        const el = document.getElementById('syncStatus');
        if (!el) return;
        const label = el.querySelector('.sync-label');
        const spinner = el.querySelector('.sync-spinner');
        if (label) label.textContent = text;
        if (spinner) spinner.style.display = syncing ? 'inline-block' : 'none';
    }

    function formatTimeAgo(isoStr) {
        if (!isoStr) return 'never';
        const diff = Math.floor((Date.now() - new Date(isoStr + 'Z').getTime()) / 1000);
        if (diff < 60) return 'just now';
        if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
        if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
        return Math.floor(diff / 86400) + 'd ago';
    }

    function runAutoSync() {
        updateSyncStatus('Syncing...', true);
        fetch('/sync/api', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                updateSyncStatus('Sync failed', false);
                return;
            }
            const timeStr = formatTimeAgo(data.last_sync);
            updateSyncStatus('Synced ' + timeStr, false);
            if (data.new_tasks > 0) {
                showToast(data.new_tasks + ' new task' + (data.new_tasks > 1 ? 's' : '') + ' from email');
                // Reload to show new tasks
                setTimeout(() => window.location.reload(), 1500);
            } else {
                refreshStats();
            }
        })
        .catch(() => updateSyncStatus('Sync error', false));
    }

    function startAutoSync() {
        // Only auto-sync if authenticated (check for sync status bar)
        if (!document.getElementById('syncStatus')) return;
        // Initial sync status check
        fetch('/sync/status')
        .then(r => r.json())
        .then(data => {
            if (!data.authenticated) return;
            updateSyncStatus('Synced ' + formatTimeAgo(data.last_sync), false);
            // Start polling
            syncTimer = setInterval(runAutoSync, SYNC_INTERVAL);
        })
        .catch(() => {});
    }

    document.addEventListener('DOMContentLoaded', startAutoSync);
})();
