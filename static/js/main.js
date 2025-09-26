// Task Modal functionality
function openTaskModal() {
    document.getElementById('taskModal').style.display = 'block';
}

function closeTaskModal() {
    document.getElementById('taskModal').style.display = 'none';
    // Reset priority selection when closing modal
    selectedPriority = null;
    document.querySelectorAll('.priority-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    document.getElementById('priority').value = '';
}

// Recurring task checkbox
document.getElementById('is_recurring').addEventListener('change', function() {
    document.getElementById('recurrence').disabled = !this.checked;
});

// Priority selection in modal - toggle behavior
let selectedPriority = null;

function togglePriority(priority) {
    const option = document.querySelector(`[data-priority="${priority}"]`);
    
    if (selectedPriority === priority) {
        // Deselect if clicking the same priority
        option.classList.remove('selected');
        selectedPriority = null;
        document.getElementById('priority').value = '';
    } else {
        // Deselect previous and select new
        document.querySelectorAll('.priority-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        option.classList.add('selected');
        selectedPriority = priority;
        document.getElementById('priority').value = priority;
    }
}

// Task action menu functions
function showTaskMenu(taskId, event) {
    event.stopPropagation();
    hideAllTaskMenus();
    const menu = document.getElementById(`task-menu-${taskId}`);
    menu.style.display = 'block';
}

function hideAllTaskMenus() {
    document.querySelectorAll('.task-menu-popup').forEach(menu => {
        menu.style.display = 'none';
    });
}

function updateTaskPriority(taskId, priority) {
    fetch(`/update_task_priority/${taskId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ priority: priority })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            hideAllTaskMenus();
            window.location.reload();
        }
    });
}

function moveTaskTomorrow(taskId) {
    fetch(`/move_task_tomorrow/${taskId}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            hideAllTaskMenus();
            window.location.reload();
        }
    });
}

function deleteTaskCompletely(taskId) {
    if (confirm('Are you sure you want to delete this task completely? This cannot be undone.')) {
        fetch(`/delete_task_completely/${taskId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                hideAllTaskMenus();
                window.location.reload();
            }
        });
    }
}

// Task completion toggle
function toggleTask(taskId) {
    fetch(`/toggle_task/${taskId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
                if (taskElement) {
                    taskElement.classList.toggle('completed', data.completed);
                }
            }
        });
}

// Close modals when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('taskModal');
    if (event.target === modal) {
        closeTaskModal();
    }
    
    if (!event.target.closest('.task-menu-popup') && !event.target.closest('.task-menu-btn')) {
        hideAllTaskMenus();
    }
}

// Close modals with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeTaskModal();
        hideAllTaskMenus();
    }
});
