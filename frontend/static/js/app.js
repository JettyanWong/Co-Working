const API_BASE = '/api';
let currentUser = null;
let currentSection = 'projects';

function init() {
    const user = localStorage.getItem('user');
    if (!user) {
        window.location.href = '/login.html';
        return;
    }
    currentUser = JSON.parse(user);
    document.getElementById('currentUser').textContent = currentUser.username;
    const changePasswordBtn = document.getElementById('changePasswordBtn');
    if (changePasswordBtn) {
        changePasswordBtn.addEventListener('click', showChangePasswordModal);
    }
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', submitChangePassword);
    }
    if (currentUser.role === 'admin') {
        document.getElementById('adminNavItem').style.display = '';
    }
    loadProjects();
}

async function api(endpoint, options = {}) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    });
    return res;
}

function showSection(section, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    currentSection = section;

    ['projects', 'tasks', 'documents', 'files'].forEach(s => {
        document.getElementById(`${s}Section`).classList.toggle('hidden', s !== section);
        document.getElementById(`nav${s.charAt(0).toUpperCase() + s.slice(1)}`).classList.toggle('active', s === section);
    });

    // Load data for the active section
    if (section === 'projects') {
        closeModal();  // Close any open modals when switching to projects
        loadProjects();
    } else if (section === 'tasks') {
        loadMyTasks();
    } else if (section === 'documents') {
        loadDocuments();
    } else if (section === 'files') {
        populateFileProjectSelect();
        loadFiles();
    }
}

async function loadProjects() {
    const res = await api('/projects');
    const data = await res.json();
    const tbody = document.getElementById('projectsTable');
    if (!tbody) return;
    tbody.innerHTML = data.projects.map(p => {
        const memberNames = (p.members || []).map(m => m.username).join(', ');
        const displayMembers = memberNames || p.owner;
        const createdAt = p.created_at ? new Date(p.created_at).toLocaleString('zh-CN') : '-';
        return `
        <tr>
            <td>${p.name}</td>
            <td>${p.description || '-'}</td>
            <td>${p.owner || '-'}</td>
            <td>${createdAt}</td>
            <td title="${displayMembers}">${displayMembers}</td>
            <td>
                <button class="btn" onclick="viewProject(${p.id})">查看</button>
                ${p.owner_id === currentUser.id ? `<button class="btn btn-danger" onclick="deleteProject(${p.id})" style="margin-left:5px;">删除</button>` : ''}
            </td>
        </tr>
    `}).join('');
}

async function loadMyTasks() {
    // Load all tasks from all projects the user is a member of
    const res = await api('/projects');
    const data = await res.json();

    let allTasks = [];
    for (const project of data.projects) {
        const tasksRes = await api(`/projects/${project.id}/tasks`);
        if (tasksRes.ok) {
            const tasksData = await tasksRes.json();
            for (const task of tasksData.tasks) {
                allTasks.push({ ...task, projectName: project.name });
            }
        }
    }

    const tbody = document.getElementById('tasksTable');
    if (!tbody) return;
    tbody.innerHTML = allTasks.map(t => `
        <tr>
            <td>${t.projectName}</td>
            <td>${t.title}</td>
            <td><span class="status ${t.status}">${t.status === 'in_progress' ? '进行中' : t.status === 'completed' ? '已完成' : '待处理'}</span></td>
            <td>${t.assignee || '-'}</td>
            <td>
                <button class="btn" onclick="viewProject(${t.project_id})" style="margin-right:5px;">查看</button>
                ${t.created_by === currentUser.id ? `<button class="btn btn-danger" onclick="deleteTask(${t.id})" style="margin-left:5px;">删除</button>` : ''}
            </td>
        </tr>
    `).join('');
}

async function loadDocuments() {
    const res = await api('/documents');
    const data = await res.json();

    const tbody = document.getElementById('documentTable');
    if (!tbody) return;
    tbody.innerHTML = data.documents && data.documents.length ? data.documents.map(d => `
        <tr>
            <td>${d.title}</td>
            <td>${d.owner || '-'}</td>
            <td>${d.project_name || '-'}</td>
            <td>${d.created_at ? new Date(d.created_at).toLocaleString('zh-CN') : '-'}</td>
            <td>
                <button class="btn" onclick="editDoc(${d.id})">查看</button>
                ${d.owner_id === currentUser.id ? `<button class="btn btn-danger" onclick="deleteDocument(${d.id})" style="margin-left:5px;">删除</button>` : ''}
            </td>
        </tr>
    `).join('') : '<tr><td colspan="5" style="color:#666;">暂无文档</td></tr>';
}

async function loadFiles() {
    const res = await api('/projects');
    const data = await res.json();

    let allFiles = [];
    for (const project of data.projects) {
        const filesRes = await api(`/projects/${project.id}/files`);
        if (filesRes.ok) {
            const filesData = await filesRes.json();
            for (const file of filesData.files) {
                allFiles.push({ ...file, projectName: project.name });
            }
        }
    }

    const tbody = document.getElementById('filesTable');
    if (!tbody) return;
    tbody.innerHTML = allFiles.map(f => `
        <tr>
            <td>${f.filename}</td>
            <td>${(f.size / 1024).toFixed(1)} KB</td>
            <td>${f.uploader || '-'}</td>
            <td>${f.project_name || '-'}</td>
            <td>${f.created_at ? new Date(f.created_at).toLocaleString('zh-CN') : '-'}</td>
            <td>${f.updated_at ? new Date(f.updated_at).toLocaleString('zh-CN') : '-'}</td>
            <td>
                <button class="btn" onclick="viewFile(${f.id})">查看</button>
                <button class="btn" onclick="downloadFile(${f.id})">下载</button>
                ${f.uploader_id === currentUser.id ? `<button class="btn btn-danger" onclick="deleteFile(${f.id})" style="margin-left:5px;">删除</button>` : ''}
            </td>
        </tr>
    `).join('') || '<tr><td colspan="7" style="color:#666;">暂无文件</td></tr>';
}

function showCreateProject() {
    document.getElementById('createProjectModal').classList.add('show');
    // Populate user checkboxes
    const container = document.getElementById('userCheckboxList');
    container.innerHTML = '<span style="color:#999;">加载中...</span>';
    fetch('/api/users').then(r => r.json()).then(data => {
        container.innerHTML = (data.users || [])
            .filter(u => u.id !== currentUser.id)
            .map(u => `<label style="display:block;padding:4px 0;cursor:pointer;">
                <input type="checkbox" value="${u.id}" class="member-checkbox"> ${u.username}
            </label>`).join('') || '<span style="color:#999;">暂无其他用户</span>';
    }).catch(() => {
        container.innerHTML = '<span style="color:#999;">加载失败</span>';
    });
}

function closeProjectModal() {
    document.getElementById('createProjectModal').classList.remove('show');
}

function showCreateDocument() {
    // Populate project selector
    const select = document.getElementById('docProjectSelect');
    select.innerHTML = '<option value="">不关联项目</option>';
    fetch('/api/projects').then(r => r.json()).then(data => {
        (data.projects || []).forEach(p => {
            select.innerHTML += `<option value="${p.id}">${p.name}</option>`;
        });
    });
    document.getElementById('createDocumentModal').classList.add('show');
}

function closeDocModal() {
    document.getElementById('createDocumentModal').classList.remove('show');
}

function showChangePasswordModal() {
    const modal = document.getElementById('changePasswordModal');
    const errorEl = document.getElementById('changePasswordError');
    if (errorEl) errorEl.textContent = '';
    if (modal) modal.classList.add('show');
}

function closeChangePasswordModal() {
    const modal = document.getElementById('changePasswordModal');
    if (modal) modal.classList.remove('show');
    const form = document.getElementById('changePasswordForm');
    if (form) form.reset();
    const errorEl = document.getElementById('changePasswordError');
    if (errorEl) errorEl.textContent = '';
}

function closeModal() {
    closeProjectModal();
    closeDocModal();
    closeChangePasswordModal();
}

async function submitChangePassword(e) {
    e.preventDefault();
    const errorEl = document.getElementById('changePasswordError');
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (!currentPassword || !newPassword || !confirmPassword) {
        if (errorEl) errorEl.textContent = '请填写全部密码字段';
        return;
    }
    if (newPassword.length < 8) {
        if (errorEl) errorEl.textContent = '新密码至少 8 个字符';
        return;
    }
    if (newPassword !== confirmPassword) {
        if (errorEl) errorEl.textContent = '两次输入的新密码不一致';
        return;
    }

    const res = await api('/change-password', {
        method: 'POST',
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
    });

    if (res.ok) {
        closeChangePasswordModal();
        alert('密码修改成功，请使用新密码继续登录。');
    } else {
        const data = await res.json();
        if (errorEl) errorEl.textContent = data.error || '修改失败';
    }
}

document.getElementById('createProjectForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('projectName').value;
    const description = document.getElementById('projectDesc').value;
    const memberIds = Array.from(document.querySelectorAll('.member-checkbox:checked'))
        .map(cb => parseInt(cb.value));
    const res = await api('/projects', {
        method: 'POST',
        body: JSON.stringify({ name, description, member_ids: memberIds })
    });
    if (res.ok) {
        closeProjectModal();
        document.getElementById('projectName').value = '';
        document.getElementById('projectDesc').value = '';
        loadProjects();
    } else {
        const data = await res.json();
        alert(data.error || '创建失败');
    }
});

document.getElementById('createDocumentForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('docTitleInput').value;
    const projectId = document.getElementById('docProjectSelect').value;
    const body = { title: title };
    if (projectId) body.project_id = parseInt(projectId);

    const res = await api('/documents', {
        method: 'POST',
        body: JSON.stringify(body)
    });
    if (res.ok) {
        const data = await res.json();
        closeDocModal();
        document.getElementById('docTitleInput').value = '';
        window.location.href = '/static/editor.html?id=' + data.document.id;
    } else {
        const data = await res.json();
        alert(data.error || '创建失败');
    }
});

async function viewProject(id) {
    window.location.href = `/static/project.html?id=${id}`;
}

async function claimTask(taskId) {
    const res = await api(`/tasks/${taskId}/claim`, { method: 'POST' });
    if (res.ok) {
        loadMyTasks();
    } else {
        const data = await res.json();
        alert(data.error || '操作失败');
    }
}

async function completeTask(taskId) {
    const res = await api(`/tasks/${taskId}/complete`, { method: 'POST' });
    if (res.ok) {
        loadMyTasks();
    } else {
        const data = await res.json();
        alert(data.error || '操作失败');
    }
}

function editDoc(docId) {
    window.location.href = `/static/editor.html?id=${docId}`;
}

function viewFile(fileId) {
    window.open(`/static/file-view.html?id=${fileId}`);
}

function downloadFile(fileId) {
    window.open(`${API_BASE}/files/${fileId}/download`);
}

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    if (!file) {
        alert('请选择文件');
        return;
    }
    const formData = new FormData();
    formData.append('file', file);
    const projectSelect = document.getElementById('fileProjectSelect');
    if (projectSelect && projectSelect.value) {
        formData.append('project_id', projectSelect.value);
    }
    const res = await fetch(`${API_BASE}/files`, { method: 'POST', body: formData });
    if (res.ok) {
        fileInput.value = '';
        if (projectSelect) projectSelect.value = '';
        loadFiles();
    } else {
        const data = await res.json();
        alert(data.error || '上传失败');
    }
}

function populateFileProjectSelect() {
    const select = document.getElementById('fileProjectSelect');
    if (!select) return;
    select.innerHTML = '<option value="">选择项目（可选）</option>';
    fetch('/api/projects').then(r => r.json()).then(data => {
        (data.projects || []).forEach(p => {
            select.innerHTML += `<option value="${p.id}">${p.name}</option>`;
        });
    });
}

async function deleteProject(id) {
    if (!confirm('确定要删除该项目吗？此操作不可撤销。')) return;
    const res = await api(`/projects/${id}`, { method: 'DELETE' });
    if (res.ok) {
        loadProjects();
    } else {
        const data = await res.json();
        alert(data.error || '删除失败');
    }
}

async function deleteTask(id) {
    if (!confirm('确定要删除该任务吗？')) return;
    const res = await api(`/tasks/${id}`, { method: 'DELETE' });
    if (res.ok) {
        loadMyTasks();
    } else {
        const data = await res.json();
        alert(data.error || '删除失败');
    }
}

async function deleteDocument(id) {
    if (!confirm('确定要删除该文档吗？此操作不可撤销。')) return;
    const res = await api(`/documents/${id}`, { method: 'DELETE' });
    if (res.ok) {
        loadDocuments();
    } else {
        const data = await res.json();
        alert(data.error || '删除失败');
    }
}

async function deleteFile(id) {
    if (!confirm('确定要删除该文件吗？')) return;
    const res = await api(`/files/${id}`, { method: 'DELETE' });
    if (res.ok) {
        loadFiles();
    } else {
        const data = await res.json();
        alert(data.error || '删除失败');
    }
}

async function logout() {
    await fetch('/auth/logout', { method: 'POST' });
    localStorage.removeItem('user');
    window.location.href = '/login.html';
}

// Initialize
init();
