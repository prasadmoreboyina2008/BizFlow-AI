from datetime import date, datetime, timedelta
import hmac
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import DEMO_PASSWORD, FRONTEND_ORIGIN
from .database import init_db, session
from .schemas import LoginRequest, TaskInput, EmployeeInput, AnalyzeInput
from .security import create_token, read_token
from .ai_service import analyze

app = FastAPI(title='BizFlow AI API', version='1.0.0')
local_development = FRONTEND_ORIGIN.startswith(('http://localhost:', 'http://127.0.0.1:'))
vite_dev_origin_regex = r'http://(?:localhost|127\.0\.0\.1|10(?:\.\d{1,3}){3}):517[3-9]' if local_development else None
app.add_middleware(CORSMiddleware, allow_origins=[FRONTEND_ORIGIN, 'http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:5174', 'http://127.0.0.1:5174'], allow_origin_regex=vite_dev_origin_regex, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
auth_scheme = HTTPBearer(auto_error=False)


@app.on_event('startup')
def startup():
    init_db()


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme)):
    if not credentials or not (email := read_token(credentials.credentials)):
        raise HTTPException(401, 'Please sign in to continue')
    return email


def task_dict(row):
    item = dict(row)
    raw_status = item['status']
    item['task_status'] = raw_status
    item['is_overdue'] = raw_status != 'Completed' and item['deadline'] < date.today().isoformat()
    item['status'] = 'Overdue' if item['is_overdue'] else raw_status
    return item


def all_tasks(db):
    rows = db.execute('''SELECT t.*,e.name AS employee_name,e.avatar AS employee_avatar FROM tasks t LEFT JOIN employees e ON e.id=t.employee_id ORDER BY t.deadline ASC,t.id DESC''').fetchall()
    return [task_dict(r) for r in rows]


def dashboard_data(db):
    tasks = all_tasks(db)
    total = len(tasks)
    completed_tasks = [t for t in tasks if t['task_status'] == 'Completed']
    pending = sum(t['status'] == 'Pending' for t in tasks)
    active = sum(t['status'] == 'In Progress' for t in tasks)
    overdue = sum(t['is_overdue'] for t in tasks)
    on_time = sum(bool(t['completed_at']) and t['completed_at'][:10] <= t['deadline'] for t in completed_tasks)
    weekly = []
    for offset in range(6, -1, -1):
        day = date.today() - timedelta(days=offset)
        weekly.append({
            'day': day.strftime('%a'),
            'created': sum(t['created_at'][:10] == day.isoformat() for t in tasks),
            'completed': sum(bool(t['completed_at']) and t['completed_at'][:10] == day.isoformat() for t in tasks),
        })
    employees = db.execute('SELECT id,name,email,role,department,avatar,created_at FROM employees ORDER BY name').fetchall()
    workload = []
    for e in employees:
        owned = [t for t in tasks if t['employee_id'] == e['id']]
        workload.append({
            'employee_id': e['id'], 'name': e['name'],
            'completed': sum(t['task_status'] == 'Completed' for t in owned),
            'open': sum(t['task_status'] != 'Completed' for t in owned),
        })
    return {
        'total_tasks': total, 'completed': len(completed_tasks), 'pending': pending,
        'overdue': overdue, 'in_progress': active,
        'completion_rate': round(100 * len(completed_tasks) / total) if total else 0,
        'on_time_percentage': round(100 * on_time / len(completed_tasks)) if completed_tasks else 0,
        'productivity_percentage': round(100 * len(completed_tasks) / total) if total else 0,
        'weekly_activity': weekly, 'employee_productivity': workload,
        'tasks': tasks, 'employees': [dict(e) for e in employees],
    }


@app.get('/api/health')
def health():
    return {'status': 'ok', 'service': 'BizFlow AI API'}


@app.post('/api/auth/login')
def login(payload: LoginRequest):
    email = payload.email.strip().lower()
    if not DEMO_PASSWORD:
        raise HTTPException(503, 'Demo login is not configured. Set DEMO_PASSWORD in backend/.env.')
    if not hmac.compare_digest(payload.password, DEMO_PASSWORD):
        raise HTTPException(401, 'Incorrect email or password')
    if email == 'manager@bizflow.demo':
        user = {'name': 'Prasad', 'email': email, 'role': 'Manager'}
    else:
        with session() as db:
            employee = db.execute('SELECT name,email,role FROM employees WHERE email=?', (email,)).fetchone()
        if not employee:
            raise HTTPException(401, 'Incorrect email or password')
        user = {'name': employee['name'], 'email': employee['email'], 'role': employee['role']}
    return {'access_token': create_token(email), 'token_type': 'bearer', 'user': user}


@app.get('/api/tasks')
def get_tasks(search: str = '', status: str = '', priority: str = '', employee_id: int | None = None, user=Depends(current_user)):
    with session() as db:
        tasks = all_tasks(db)
    if search:
        tasks = [t for t in tasks if search.lower() in (t['title'] + ' ' + t['description'] + ' ' + (t['employee_name'] or '')).lower()]
    if status:
        tasks = [t for t in tasks if t['is_overdue']] if status == 'Overdue' else [t for t in tasks if t['status'] == status]
    if priority:
        tasks = [t for t in tasks if t['priority'] == priority]
    if employee_id:
        tasks = [t for t in tasks if t['employee_id'] == employee_id]
    return tasks


@app.post('/api/tasks', status_code=201)
def create_task(payload: TaskInput, user=Depends(current_user)):
    with session() as db:
        if payload.employee_id and not db.execute('SELECT id FROM employees WHERE id=?', (payload.employee_id,)).fetchone():
            raise HTTPException(422, 'Selected employee does not exist')
        cursor = db.execute('INSERT INTO tasks(title,description,employee_id,status,priority,deadline,completed_at) VALUES(?,?,?,?,?,?,?)', (payload.title.strip(), payload.description.strip(), payload.employee_id, payload.status, payload.priority, payload.deadline.isoformat(), date.today().isoformat() if payload.status == 'Completed' else None))
        row = db.execute('SELECT t.*,e.name AS employee_name,e.avatar AS employee_avatar FROM tasks t LEFT JOIN employees e ON e.id=t.employee_id WHERE t.id=?', (cursor.lastrowid,)).fetchone()
        return task_dict(row)


@app.get('/api/tasks/{task_id}')
def get_task(task_id: int, user=Depends(current_user)):
    with session() as db:
        row = db.execute('SELECT t.*,e.name AS employee_name,e.avatar AS employee_avatar FROM tasks t LEFT JOIN employees e ON e.id=t.employee_id WHERE t.id=?', (task_id,)).fetchone()
    if not row:
        raise HTTPException(404, 'Task not found')
    return task_dict(row)


@app.put('/api/tasks/{task_id}')
def update_task(task_id: int, payload: TaskInput, user=Depends(current_user)):
    with session() as db:
        old = db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
        if not old:
            raise HTTPException(404, 'Task not found')
        if payload.employee_id and not db.execute('SELECT id FROM employees WHERE id=?', (payload.employee_id,)).fetchone():
            raise HTTPException(422, 'Selected employee does not exist')
        completed_at = (old['completed_at'] or date.today().isoformat()) if payload.status == 'Completed' else None
        db.execute('UPDATE tasks SET title=?,description=?,employee_id=?,status=?,priority=?,deadline=?,completed_at=? WHERE id=?', (payload.title.strip(), payload.description.strip(), payload.employee_id, payload.status, payload.priority, payload.deadline.isoformat(), completed_at, task_id))
        row = db.execute('SELECT t.*,e.name AS employee_name,e.avatar AS employee_avatar FROM tasks t LEFT JOIN employees e ON e.id=t.employee_id WHERE t.id=?', (task_id,)).fetchone()
        return task_dict(row)


@app.delete('/api/tasks/{task_id}', status_code=204)
def delete_task(task_id: int, user=Depends(current_user)):
    with session() as db:
        cur = db.execute('DELETE FROM tasks WHERE id=?', (task_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, 'Task not found')


@app.get('/api/employees')
def get_employees(user=Depends(current_user)):
    with session() as db:
        return [dict(r) for r in db.execute('SELECT id,name,email,role,department,avatar,created_at FROM employees ORDER BY name').fetchall()]


@app.post('/api/employees', status_code=201)
def create_employee(payload: EmployeeInput, user=Depends(current_user)):
    with session() as db:
        try:
            cur = db.execute('INSERT INTO employees(name,email,role,department,avatar) VALUES(?,?,?,?,?)', (payload.name.strip(), payload.email.strip().lower(), payload.role.strip(), payload.department.strip(), payload.name.strip()[0].upper()))
        except Exception:
            raise HTTPException(409, 'An employee with that email already exists')
        return dict(db.execute('SELECT id,name,email,role,department,avatar,created_at FROM employees WHERE id=?', (cur.lastrowid,)).fetchone())


@app.get('/api/dashboard')
def get_dashboard(user=Depends(current_user)):
    with session() as db:
        return dashboard_data(db)


def report_data(period: str):
    with session() as db:
        data = dashboard_data(db)
    today = date.today()
    start = today if period == 'daily' else today - timedelta(days=6)
    done = [t for t in data['tasks'] if t['task_status'] == 'Completed' and t['completed_at'] and t['completed_at'][:10] >= start.isoformat()]
    activity = data['weekly_activity'][-1:] if period == 'daily' else data['weekly_activity']
    summary = {key: data[key] for key in ('total_tasks', 'completed', 'pending', 'in_progress', 'overdue', 'completion_rate', 'on_time_percentage', 'productivity_percentage')}
    summary.update({'completed_this_week': len(done), 'open_tasks': data['pending'] + data['in_progress']})
    return {'period': {'range': period, 'start': start.isoformat(), 'end': today.isoformat()}, 'summary': summary, 'daily_activity': activity, 'employee_productivity': data['employee_productivity'], 'completed_tasks': done, 'priority_tasks': [t for t in data['tasks'] if t['status'] in ('Overdue', 'Pending', 'In Progress')][:5]}


@app.get('/api/reports/weekly')
def weekly_report(user=Depends(current_user)):
    return report_data('weekly')


@app.get('/api/reports/daily')
def daily_report(user=Depends(current_user)):
    return report_data('daily')


@app.post('/api/ai/analyze')
def ai_analyze(payload: AnalyzeInput, user=Depends(current_user)):
    with session() as db:
        data = dashboard_data(db)
    return analyze(data['tasks'], data)
