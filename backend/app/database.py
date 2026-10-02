import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from .config import DATABASE_PATH

def connect():
    path = Path(DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db

@contextmanager
def session():
    db = connect()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    with session() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL DEFAULT 'Team member',
            department TEXT NOT NULL DEFAULT 'Operations',
            avatar TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','In Progress','Completed')),
            priority TEXT NOT NULL DEFAULT 'Medium' CHECK(priority IN ('Low','Medium','High')),
            deadline TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        );
        """)
        if db.execute("SELECT COUNT(*) FROM employees").fetchone()[0] == 0:
            people = [
                ('Suresh','suresh@bizflow.demo','Sales Lead','Sales','S'),
                ('Krishna','krishna@bizflow.demo','Marketing Executive','Marketing','K'),
                ('Prasad','prasad@bizflow.demo','Operations Manager','Operations','P'),
                ('Niswanth','niswanth@bizflow.demo','Client Relations','Sales','N'),
                ('Srinu','srinu@bizflow.demo','Inventory Coordinator','Operations','S'),
            ]
            db.executemany("INSERT INTO employees(name,email,role,department,avatar) VALUES(?,?,?,?,?)", people)
        if db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0:
            today = date.today()
            sample = [
                ('Prepare client quotation','Finalize pricing and share the proposal with the client.',1,'In Progress','High',today+timedelta(days=1),None),
                ('Update marketing report','Compile campaign performance and channel insights.',2,'Pending','Medium',today-timedelta(days=2),None),
                ('Contact new client','Follow up on the inbound partnership enquiry.',4,'Completed','High',today-timedelta(days=1),today.isoformat()),
                ('Prepare weekly sales report','Summarize pipeline, conversions, and forecast.',1,'Completed','Medium',today-timedelta(days=2),today.isoformat()),
                ('Update inventory records','Reconcile stock movement for the current week.',5,'Pending','Low',today+timedelta(days=3),None),
                ('Review onboarding checklist','Confirm access and welcome materials for new account.',3,'In Progress','Medium',today+timedelta(days=2),None),
                ('Schedule product walkthrough','Coordinate a product demo with the prospect.',4,'Pending','High',today+timedelta(days=4),None),
                ('Reconcile supplier invoices','Match this month invoices against purchase orders.',5,'Completed','Low',today-timedelta(days=3),today.isoformat()),
            ]
            db.executemany("INSERT INTO tasks(title,description,employee_id,status,priority,deadline,completed_at) VALUES(?,?,?,?,?,?,?)", sample)

