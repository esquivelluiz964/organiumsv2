# Flask MVP Template

Unzip and run:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
export FLASK_APP=manage.py
flask db upgrade  # creates migrations (configure DB_URI first)
python run.py
```

Structure highlights:
- `app/` - frontend blueprint (templates with Jinja components)
- `api/` - backend/api blueprint (JSON endpoints)
- `migrations/` - created after running `flask db init` (not included)
- `manage.py` - Flask app factory + cli
- `run.py` - simple runner
- `clean.py` - removes .pyc and __pycache__
- `requirements.txt` - pinned libs (you can adjust)

CSS root variables in `app/static/css/vars.css`.
Jinja components are in `app/templates/components/` as macros for reuse.

--- Aux

        OBJETIVOS
        <h3>Objetivos</h3>
        <ul>
          {% for o in objectives if o.level == level %}
            <li>
              <div>
                <strong>{{ o.title }}</strong> - {{ o.description or "-" }}
              </div>
              <div class="actions">
                <button class="btn-edit" onclick="openEditModal('goal', {{ o.id }}, '{{ o.title }}', '{{ o.description or '' }}', '{{ level }}')">Editar</button>
              </div>
            </li>
          {% endfor %}
        </ul>
        <button class="btn-add" onclick="openCreateModal('goal', '{{ level }}')">+ Novo Objetivo</button>

        <!-- PLANOS -->
        <h3>Planos</h3>
        <ul>
          {% for p in plans if p.level == level %}
            <li>
              <div>
                <strong>{{ p.title }}</strong> - {{ p.description or "-" }}  
                <br><small>👤 {{ p.who }} | 📅 {{ p.when }} | 📍 {{ p.where }}</small>
              </div>
              <div class="actions">
                <button class="btn-edit" onclick="openEditModal('goal', {{ p.id }}, '{{ p.title }}', '{{ p.description or '' }}', '{{ level }}', '{{ p.who }}', '{{ p.when }}', '{{ p.where }}')">Editar</button>
              </div>
            </li>
          {% endfor %}
        </ul>
        <button class="btn-add" onclick="openCreateModal('goal', '{{ level }}')">+ Novo Plano</button>

