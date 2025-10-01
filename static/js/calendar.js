let currentDate = new Date();

function renderCalendar(date) {
    const calendarDays = document.getElementById('calendarDays');
    const calendarMonth = document.getElementById('calendar-month');
    calendarDays.innerHTML = '';
    
    const year = date.getFullYear();
    const month = date.getMonth();
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    
    const daysInMonth = lastDay.getDate();
    const startingDay = firstDay.getDay();
    
    // Update month header
    calendarMonth.textContent = date.toLocaleString('default', { month: 'long', year: 'numeric' });
    
    // Previous month days
    const prevMonthLastDay = new Date(year, month, 0).getDate();
    for (let i = 0; i < startingDay; i++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day other-month';
        dayElement.textContent = prevMonthLastDay - startingDay + i + 1;
        calendarDays.appendChild(dayElement);
    }
    
    // Current month days
    const today = new Date();
    for (let i = 1; i <= daysInMonth; i++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        dayElement.textContent = i;
        
        // Highlight today
        if (year === today.getFullYear() && month === today.getMonth() && i === today.getDate()) {
            dayElement.classList.add('today');
        }
        
        // Add click event to navigate to daily tasks
        dayElement.addEventListener('click', function() {
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
            window.location.href = `/tasks/${dateStr}`;
        });
        
        calendarDays.appendChild(dayElement);
    }
    
    // Next month days
    const totalCells = startingDay + daysInMonth;
    const remainingCells = totalCells > 35 ? 42 - totalCells : 35 - totalCells;
    
    for (let i = 1; i <= remainingCells; i++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day other-month';
        dayElement.textContent = i;
        calendarDays.appendChild(dayElement);
    }
    
    currentDate = date;
}

function prevMonth() {
    const newDate = new Date(currentDate);
    newDate.setMonth(newDate.getMonth() - 1);
    renderCalendar(newDate);
}

function nextMonth() {
    const newDate = new Date(currentDate);
    newDate.setMonth(newDate.getMonth() + 1);
    renderCalendar(newDate);
}
