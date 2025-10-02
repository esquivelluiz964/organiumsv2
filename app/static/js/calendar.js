class CalendarManager {
    constructor(initialEvents = []) {
        // normalize events: ensure dates are ISO strings or null
        this.events = initialEvents.map(e => ({
            ...e,
            start: e.start || null,
            end: e.end || null
        }));
        this.currentDate = new Date();
        this.currentView = 'month'; // 'month' | 'week' | 'day'
        this.container = document.getElementById('calendar');
        this.currentMonthLabel = document.getElementById('currentMonth');
        this.prevBtn = document.getElementById('prevBtn');
        this.nextBtn = document.getElementById('nextBtn');
        this.viewButtons = document.querySelectorAll('.btn-view');

        // modal elements
        this.modal = document.getElementById('eventModal');
        this.modalTitle = document.getElementById('modalTitle');
        this.form = document.getElementById('eventForm');
        this.inputId = document.getElementById('eventId');
        this.inputTitle = document.getElementById('eventTitle');
        this.inputDescription = document.getElementById('eventDescription');
        this.inputStart = document.getElementById('eventStart');
        this.inputEnd = document.getElementById('eventEnd');
        this.inputResponsavel = document.getElementById('eventResponsavel');
        this.inputSetor = document.getElementById('eventSetor');
        this.inputColor = document.getElementById('eventColor');
        this.colorValue = document.getElementById('colorValue');
        this.deleteBtn = document.getElementById('deleteBtn');

        this.draggedEventId = null;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.render();
    }

    setupEventListeners() {
        this.prevBtn.addEventListener('click', () => { this.navigate(-1); });
        this.nextBtn.addEventListener('click', () => { this.navigate(1); });

        document.querySelectorAll('.btn-view').forEach(btn => {
            btn.addEventListener('click', (ev) => {
                this.viewButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentView = btn.dataset.view;
                this.render();
            });
        });

        // modal open button (from template)
        window.openEventModal = (eventObj) => this.openEventModal(eventObj);
        window.closeEventModal = () => this.closeEventModal();

        // form submit
        this.form.addEventListener('submit', (ev) => {
            ev.preventDefault();
            this.saveEventFromForm();
        });

        // color picker
        this.inputColor.addEventListener('input', (ev) => {
            this.colorValue.textContent = ev.target.value;
        });

        // delete
        this.deleteBtn.addEventListener('click', () => {
            const id = this.inputId.value;
            if (!id) return;
            if (!confirm('Deseja realmente excluir este evento?')) return;
            this.deleteEvent(id);
        });

        // close modal by clicking outside
        window.addEventListener('click', (e) => {
            if (e.target === this.modal) this.closeEventModal();
        });
    }

    // -----------------------
    // Rendering entry points
    // -----------------------
    render() {
        this.container.innerHTML = '';
        if (this.currentView === 'month') {
            this.renderMonth();
        } else if (this.currentView === 'week') {
            this.renderWeek();
        } else if (this.currentView === 'day') {
            this.renderDay();
        }
    }

    renderMonth() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();

        // update header label
        const monthName = this.currentDate.toLocaleString('pt-BR', { month: 'long' });
        this.currentMonthLabel.textContent = `${this.capitalize(monthName)} ${year}`;

        // grid container
        const grid = document.createElement('div');
        grid.className = 'month-grid';

        // weekdays header
        const weekDays = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];
        const headerRow = document.createElement('div');
        headerRow.className = 'calendar-header';
        weekDays.forEach(d => {
            const cell = document.createElement('div');
            cell.className = 'weekday';
            cell.textContent = d;
            headerRow.appendChild(cell);
        });
        grid.appendChild(headerRow);

        // first day of month
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        // JS: Sunday=0 ... we want Mon-first, so compute index accordingly
        const startIndex = (firstDay.getDay() + 6) % 7; // 0..6, where 0 => Monday

        // number of cells = startIndex + lastDay.getDate(), then pad to full weeks
        const totalDays = startIndex + lastDay.getDate();
        const totalCells = Math.ceil(totalDays / 7) * 7;

        const today = new Date();
        for (let i = 0; i < totalCells; i++) {
            const cell = document.createElement('div');
            cell.className = 'month-cell';

            const dayNumber = i - startIndex + 1;
            if (i >= startIndex && dayNumber <= lastDay.getDate()) {
                const dateObj = new Date(year, month, dayNumber);
                cell.dataset.date = dateObj.toISOString();

                // date header
                const dateHeader = document.createElement('div');
                dateHeader.className = 'date-header';
                dateHeader.textContent = dayNumber;
                if (dateObj.toDateString() === today.toDateString()) {
                    dateHeader.classList.add('today');
                }
                cell.appendChild(dateHeader);

                // events container
                const evContainer = document.createElement('div');
                evContainer.className = 'events-container';
                cell.appendChild(evContainer);

                // allow double click to create new event on that date (set start to morning)
                cell.addEventListener('dblclick', () => {
                    const startISO = new Date(year, month, dayNumber, 9, 0, 0).toISOString();
                    this.openEventModal({ start: startISO, end: null });
                });

                // allow drop
                this.setupCellDragDrop(cell, dateObj);
            } else {
                cell.classList.add('empty-cell');
            }

            grid.appendChild(cell);
        }

        this.container.appendChild(grid);
        this.placeEventsInMonthGrid();
    }

    renderWeek() {
        const startOfWeek = this.getStartOfWeek(this.currentDate); // Monday
        const weekLabelStart = startOfWeek.toLocaleDateString('pt-BR', { day: '2-digit', month: 'long' });
        const weekEnd = new Date(startOfWeek);
        weekEnd.setDate(startOfWeek.getDate() + 6);
        const weekLabelEnd = weekEnd.toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' });
        this.currentMonthLabel.textContent = `Semana: ${weekLabelStart} — ${weekLabelEnd}`;

        const wrapper = document.createElement('div');
        wrapper.className = 'week-wrapper';

        const header = document.createElement('div');
        header.className = 'week-header';
        for (let d = 0; d < 7; d++) {
            const day = new Date(startOfWeek);
            day.setDate(startOfWeek.getDate() + d);
            const col = document.createElement('div');
            col.className = 'week-col';
            col.dataset.date = day.toISOString();
            const dayTitle = document.createElement('div');
            dayTitle.className = 'week-day-title';
            dayTitle.textContent = `${this.capitalize(day.toLocaleString('pt-BR', { weekday: 'short' }))} ${day.getDate()}`;
            col.appendChild(dayTitle);
            wrapper.appendChild(col);

            // drop
            this.setupCellDragDrop(col, day);
        }

        // events area
        this.container.appendChild(wrapper);
        this.placeEventsInWeekOrDay('week', startOfWeek);
    }

    renderDay() {
        const day = this.currentDate;
        const dayLabel = day.toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' });
        this.currentMonthLabel.textContent = this.capitalize(dayLabel);

        const wrapper = document.createElement('div');
        wrapper.className = 'day-wrapper';

        const col = document.createElement('div');
        col.className = 'day-col';
        col.dataset.date = day.toISOString();
        wrapper.appendChild(col);

        // allow drop
        this.setupCellDragDrop(col, day);

        // hours grid
        const hoursGrid = document.createElement('div');
        hoursGrid.className = 'hours-grid';
        for (let h = 0; h < 24; h++) {
            const hourRow = document.createElement('div');
            hourRow.className = 'hour-row';
            hourRow.dataset.hour = h;
            hourRow.textContent = `${h.toString().padStart(2, '0')}:00`;
            col.appendChild(hourRow);

            // double click to create at that hour
            hourRow.addEventListener('dblclick', (ev) => {
                const date = new Date(day.getFullYear(), day.getMonth(), day.getDate(), h, 0, 0);
                this.openEventModal({ start: date.toISOString(), end: null });
            });
        }

        this.container.appendChild(wrapper);
        this.placeEventsInWeekOrDay('day', day);
    }

    // -----------------------
    // Helpers: place events
    // -----------------------
    placeEventsInMonthGrid() {
        const cells = this.container.querySelectorAll('.month-cell');
        cells.forEach(cell => {
            const dateIso = cell.dataset.date;
            if (!dateIso) return;
            const dayStart = new Date(dateIso);
            const dayEnd = new Date(dayStart);
            dayEnd.setDate(dayStart.getDate() + 1);

            const evContainer = cell.querySelector('.events-container');
            evContainer.innerHTML = '';

            const eventsForDay = this.events.filter(ev => {
                if (!ev.start) return false;
                const s = new Date(ev.start);
                // event considered on day if its start is within the day's range OR it spans this day
                const e = ev.end ? new Date(ev.end) : null;
                return (s >= dayStart && s < dayEnd) || (e && s < dayEnd && e > dayStart);
            });

            eventsForDay.forEach(ev => {
                const evEl = this.createEventElement(ev, 'month');
                evContainer.appendChild(evEl);
            });
        });
    }

    placeEventsInWeekOrDay(view, anchorDate) {
        // view = 'week' or 'day'
        // anchorDate: for week -> startOfWeek, for day -> the specific day
        if (view === 'week') {
            // for each column (7 cols)
            const cols = this.container.querySelectorAll('.week-col');
            cols.forEach((col, idx) => {
                const date = new Date(anchorDate);
                date.setDate(anchorDate.getDate() + idx);
                const dayStart = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 0, 0, 0);
                const dayEnd = new Date(dayStart);
                dayEnd.setDate(dayStart.getDate() + 1);

                col.innerHTML = col.querySelector('.week-day-title').outerHTML; // keep title
                const eventsForDay = this.events.filter(ev => {
                    if (!ev.start) return false;
                    const s = new Date(ev.start);
                    const e = ev.end ? new Date(ev.end) : null;
                    return (s >= dayStart && s < dayEnd) || (e && s < dayEnd && e > dayStart);
                });

                const list = document.createElement('div');
                list.className = 'events-list';
                eventsForDay.forEach(ev => list.appendChild(this.createEventElement(ev, 'week')));
                col.appendChild(list);
            });
        } else { // day
            const col = this.container.querySelector('.day-col');
            if (!col) return;
            // remove everything (hours are present)
            const hoursGrid = col.querySelector('.hours-grid') || col;
            // create overlay container
            const overlay = document.createElement('div');
            overlay.className = 'day-events-overlay';
            hoursGrid.appendChild(overlay);

            const dayStart = new Date(anchorDate.getFullYear(), anchorDate.getMonth(), anchorDate.getDate(), 0, 0, 0);
            const dayEnd = new Date(dayStart);
            dayEnd.setDate(dayStart.getDate() + 1);
            const eventsForDay = this.events.filter(ev => {
                if (!ev.start) return false;
                const s = new Date(ev.start);
                const e = ev.end ? new Date(ev.end) : null;
                return (s >= dayStart && s < dayEnd) || (e && s < dayEnd && e > dayStart);
            });

            eventsForDay.forEach(ev => {
                const evEl = this.createEventElement(ev, 'day');
                overlay.appendChild(evEl);
                // position by time (basic)
                if (ev.start) {
                    const s = new Date(ev.start);
                    const startMinutes = s.getHours() * 60 + s.getMinutes();
                    const topPct = (startMinutes / (24 * 60)) * 100;
                    evEl.style.position = 'absolute';
                    evEl.style.top = `${topPct}%`;
                    // height by duration if end present
                    if (ev.end) {
                        const e = new Date(ev.end);
                        let durMinutes = (e - s) / (1000 * 60);
                        if (durMinutes < 30) durMinutes = 30;
                        const heightPct = (durMinutes / (24 * 60)) * 100;
                        evEl.style.height = `${heightPct}%`;
                        evEl.style.overflow = 'hidden';
                    } else {
                        evEl.style.height = '2.5%'; // small block
                    }
                }
            });
        }
    }

    createEventElement(ev, context = 'month') {
        const el = document.createElement('div');
        el.className = 'calendar-event';
        el.draggable = true;
        el.dataset.eventId = ev.id;
        el.textContent = ev.title;
        el.title = (ev.description || '') + (ev.responsavel ? `\nResponsável: ${ev.responsavel}` : '');

        // style color
        el.style.backgroundColor = ev.color || '#3b82f6';
        el.style.borderLeft = `4px solid ${this.darkenColor(ev.color || '#3b82f6')}`;

        // click to open modal (edit)
        el.addEventListener('click', (e) => {
            e.stopPropagation();
            this.openEventModal(ev);
        });

        // drag handlers
        el.addEventListener('dragstart', (e) => {
            this.draggedEventId = ev.id;
            e.dataTransfer.setData('text/plain', ev.id);
            e.dataTransfer.effectAllowed = 'move';
            el.classList.add('dragging');
        });
        el.addEventListener('dragend', (e) => {
            this.draggedEventId = null;
            el.classList.remove('dragging');
        });

        return el;
    }

    setupCellDragDrop(cellEl, dateObj) {
        cellEl.addEventListener('dragover', (ev) => {
            ev.preventDefault();
            ev.dataTransfer.dropEffect = 'move';
            cellEl.classList.add('drag-over');
        });
        cellEl.addEventListener('dragleave', (ev) => {
            cellEl.classList.remove('drag-over');
        });
        cellEl.addEventListener('drop', (ev) => {
            ev.preventDefault();
            cellEl.classList.remove('drag-over');
            const id = ev.dataTransfer.getData('text/plain') || this.draggedEventId;
            if (!id) return;
            // move event start to this cell's date at same hour as original start (if possible)
            const event = this.events.find(x => String(x.id) === String(id));
            if (!event) return;
            const oldStart = event.start ? new Date(event.start) : new Date();
            const newStart = new Date(dateObj);
            // keep hour/minutes from old start
            newStart.setHours(oldStart.getHours(), oldStart.getMinutes(), 0, 0);
            const durationMs = event.end ? (new Date(event.end) - new Date(event.start)) : null;
            const newEnd = durationMs ? new Date(newStart.getTime() + durationMs) : null;

            // optimistic update
            const prevStart = event.start;
            const prevEnd = event.end;
            event.start = newStart.toISOString();
            event.end = newEnd ? newEnd.toISOString() : null;
            this.render();

            // send update
            this.apiUpdateEvent(event.id, {
                title: event.title,
                description: event.description,
                start_at: event.start,
                end_at: event.end,
                responsavel_id: event.responsavel || null,
                setor_id: event.setor || null,
                cor: event.color || '#3b82f6'
            }).catch(err => {
                alert('Erro ao mover evento: ' + err.message);
                // rollback
                event.start = prevStart;
                event.end = prevEnd;
                this.render();
            });
        });
    }

    // -----------------------
    // Interaction: modal
    // -----------------------
    openEventModal(eventObj = null) {
        // eventObj can be full event or partial (start/end) or null -> new
        this.deleteBtn.style.display = 'none';
        this.modalTitle.textContent = eventObj && eventObj.id ? 'Editar Evento' : 'Novo Evento';
        if (eventObj && eventObj.id) {
            // find event in memory
            const ev = this.events.find(x => String(x.id) === String(eventObj.id));
            if (ev) {
                this.fillFormWithEvent(ev);
                this.deleteBtn.style.display = '';
            } else {
                // eventObj may be some data
                this.fillFormWithEvent(eventObj);
            }
        } else if (eventObj && eventObj.start) {
            // partial
            this.fillFormWithEvent({
                id: '',
                title: '',
                description: '',
                start: eventObj.start,
                end: eventObj.end || '',
                responsavel: null,
                setor: null,
                color: '#3b82f6'
            });
        } else {
            this.fillFormWithEvent({
                id: '',
                title: '',
                description: '',
                start: null,
                end: null,
                responsavel: null,
                setor: null,
                color: '#3b82f6'
            });
        }

        this.modal.style.display = 'block';
    }

    closeEventModal() {
        this.modal.style.display = 'none';
        this.form.reset();
        // reset defaults
        this.inputColor.value = '#3b82f6';
        this.colorValue.textContent = '#3b82f6';
    }

    fillFormWithEvent(ev) {
        this.inputId.value = ev.id || '';
        this.inputTitle.value = ev.title || '';
        this.inputDescription.value = ev.description || '';
        this.inputStart.value = ev.start ? this.isoToLocalInput(ev.start) : '';
        this.inputEnd.value = ev.end ? this.isoToLocalInput(ev.end) : '';
        this.inputResponsavel.value = (ev.responsavel || ev.responsavel_id) || '';
        this.inputSetor.value = (ev.setor || ev.setor_id) || '';
        this.inputColor.value = ev.color || ev.cor || '#3b82f6';
        this.colorValue.textContent = this.inputColor.value;
    }

    saveEventFromForm() {
        const id = this.inputId.value;
        const payload = {
            title: this.inputTitle.value.trim(),
            description: this.inputDescription.value.trim(),
            start_at: this.localInputToIso(this.inputStart.value),
            end_at: this.inputEnd.value ? this.localInputToIso(this.inputEnd.value) : null,
            responsavel_id: this.inputResponsavel.value || null,
            setor_id: this.inputSetor.value || null,
            cor: this.inputColor.value || '#3b82f6',
            tipo: 'evento'
        };

        if (!payload.title || !payload.start_at) {
            alert('Preencha pelo menos o título e a data de início.');
            return;
        }

        if (id) {
            // update
            // optimistic update in memory
            const ev = this.events.find(x => String(x.id) === String(id));
            const prev = ev ? { ...ev } : null;
            if (ev) {
                ev.title = payload.title;
                ev.description = payload.description;
                ev.start = payload.start_at;
                ev.end = payload.end_at;
                ev.responsavel = payload.responsavel_id;
                ev.setor = payload.setor_id;
                ev.color = payload.cor;
            }
            this.render();
            this.apiUpdateEvent(id, payload).then(() => {
                this.closeEventModal();
            }).catch(err => {
                alert('Erro ao atualizar evento: ' + err.message);
                if (prev && ev) {
                    Object.assign(ev, prev);
                    this.render();
                }
            });
        } else {
            // create
            // send to server
            this.apiCreateEvent(payload).then(result => {
                const created = result.event;
                // push to memory with expected shape
                this.events.push({
                    id: created.id,
                    title: created.title,
                    description: payload.description,
                    start: created.start,
                    end: created.end,
                    responsavel: payload.responsavel_id,
                    setor: payload.setor_id,
                    color: created.color || payload.cor
                });
                this.render();
                this.closeEventModal();
            }).catch(err => {
                alert('Erro ao criar evento: ' + err.message);
            });
        }
    }

    deleteEvent(id) {
        // optimistic remove
        const idx = this.events.findIndex(x => String(x.id) === String(id));
        if (idx === -1) return;
        const removed = this.events.splice(idx, 1)[0];
        this.render();

        this.apiDeleteEvent(id).then(() => {
            this.closeEventModal();
        }).catch(err => {
            alert('Erro ao excluir evento: ' + err.message);
            // rollback
            this.events.push(removed);
            this.render();
        });
    }

    // -----------------------
    // API wrappers
    // -----------------------
    apiCreateEvent(payload) {
        return fetch('/api/events', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload),
            credentials: 'same-origin'
        }).then(resp => {
            if (!resp.ok) return resp.json().then(j => { throw new Error(j.error || 'Erro ao criar'); });
            return resp.json();
        });
    }

    apiUpdateEvent(id, payload) {
        return fetch(`/api/events/${id}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload),
            credentials: 'same-origin'
        }).then(resp => {
            if (!resp.ok) return resp.json().then(j => { throw new Error(j.error || 'Erro ao atualizar'); });
            return resp.json();
        });
    }

    apiDeleteEvent(id) {
        return fetch(`/api/events/${id}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        }).then(resp => {
            if (!resp.ok) return resp.json().then(j => { throw new Error(j.error || 'Erro ao excluir'); });
            return resp.json();
        });
    }

    // -----------------------
    // Navigation helpers
    // -----------------------
    navigate(direction) {
        if (this.currentView === 'month') {
            this.currentDate.setMonth(this.currentDate.getMonth() + direction);
        } else if (this.currentView === 'week') {
            this.currentDate.setDate(this.currentDate.getDate() + (7 * direction));
        } else if (this.currentView === 'day') {
            this.currentDate.setDate(this.currentDate.getDate() + direction);
        }
        this.render();
    }

    // -----------------------
    // Utility helpers
    // -----------------------
    getStartOfWeek(date) {
        // Monday as first day
        const d = new Date(date);
        const day = d.getDay();
        const diff = (day + 6) % 7; // days since Monday
        d.setDate(d.getDate() - diff);
        d.setHours(0,0,0,0);
        return d;
    }

    isoToLocalInput(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        // produce YYYY-MM-DDTHH:MM
        const YYYY = d.getFullYear();
        const MM = String(d.getMonth() + 1).padStart(2, '0');
        const DD = String(d.getDate()).padStart(2, '0');
        const hh = String(d.getHours()).padStart(2, '0');
        const mm = String(d.getMinutes()).padStart(2, '0');
        return `${YYYY}-${MM}-${DD}T${hh}:${mm}`;
    }

    localInputToIso(localValue) {
        if (!localValue) return null;
        // localValue like "2025-09-25T13:45"
        const d = new Date(localValue);
        // toISOString converts to UTC, which is usually fine because backend stores iso
        return d.toISOString();
    }

    capitalize(s) {
        if (!s) return s;
        return s.charAt(0).toUpperCase() + s.slice(1);
    }

    darkenColor(hex) {
        try {
            let c = hex.replace('#', '');
            if (c.length === 3) c = c.split('').map(ch => ch + ch).join('');
            const num = parseInt(c, 16);
            const r = Math.max(0, (num >> 16) - 30);
            const g = Math.max(0, ((num >> 8) & 0xFF) - 30);
            const b = Math.max(0, (num & 0xFF) - 30);
            return `rgb(${r}, ${g}, ${b})`;
        } catch (e) {
            return hex;
        }
    }
}

// Initialize from template-provided eventsData (already present in template)
if (typeof window !== 'undefined') {
    // eventsData variable expected from server template
    if (!window.calendarManager && typeof eventsData !== 'undefined') {
        document.addEventListener('DOMContentLoaded', function() {
            window.calendarManager = new CalendarManager(eventsData || []);
        });
    }
}
