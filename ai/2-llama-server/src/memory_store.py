import threading, sqlite3, random, time
from typing import Optional


class Store:
    def __init__(self):
        self.lock = threading.Lock()
        
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        self.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                unixtime_ttl REAL NOT NULL,
                user_id TEXT NOT NULL,
                request_hash TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'NEW',
                temperature REAL NOT NULL,
                max_tokens INTEGER NOT NULL,
                model TEXT NOT NULL,
                priority INTEGER NOT NULL,
                messages_json TEXT NOT NULL,
                choices_json TEXT,
                t_load_ms REAL,
                t_p_eval_ms REAL,
                t_eval_ms REAL,
                n_p_eval INTEGER,
                n_eval INTEGER,
                CHECK (status IN ('NEW', 'TAKEN', 'DONE', 'ERROR'))
            )
        """)

        self.conn.execute(f"CREATE INDEX idx_unixtime_ttl ON tasks(unixtime_ttl)")
        self.conn.execute(f"CREATE INDEX idx_user_id ON tasks(user_id)")
        self.conn.execute(f"CREATE UNIQUE INDEX idx_user_hash ON tasks(user_id, request_hash)")
        
        self.conn.commit()
    
    def clean_expired_tasks(self):
        with self.lock:
            self.conn.execute("DELETE FROM tasks WHERE unixtime_ttl < ?", (time.time(),))
            self.conn.commit()

    def get_task_count(self, user_id: str) -> int:
        with self.lock:
            cursor = self.conn.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,))
            return cursor.fetchone()[0]

    def enqueue_task(self, user_id: str, request_hash: str, temperature: float, max_tokens: int, model: str, priority: int, messages_json: str, ttl: int = 24 * 60 * 60) -> tuple[int, sqlite3.Row]:
        with self.lock:
            cursor = self.conn.execute("""
                INSERT OR IGNORE INTO tasks (user_id, request_hash, temperature, max_tokens, model, priority, messages_json, unixtime_ttl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING *
            """, (user_id, request_hash, temperature, max_tokens, model, priority, messages_json, time.time() + ttl))
            result = cursor.fetchone()

            add = 0 if result is None else 1
            
            if result is None:
                cursor = self.conn.execute("SELECT * FROM tasks WHERE user_id = ? AND request_hash = ?", (user_id, request_hash))
                result = cursor.fetchone()
            
            self.conn.commit()
            return add, result

    def take_task(self) -> Optional[sqlite3.Row]:
        with self.lock:
            cursor = self.conn.execute("""
                WITH first_tasks AS (
                    SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY unixtime_ttl) as rn
                    FROM tasks 
                    WHERE status = 'NEW'
                )
                SELECT * FROM first_tasks WHERE rn = 1
            """)
            tasks = cursor.fetchall()
            
        if not tasks:
            return None
        
        weighted_indices = []

        for i, task in enumerate(tasks):
            weighted_indices.extend([i] * task["priority"])
        
        selected_task = tasks[random.choice(weighted_indices)]
        
        with self.lock:
            self.conn.execute("UPDATE tasks SET status = 'TAKEN' WHERE task_id = ?", (selected_task["task_id"], ))
            self.conn.commit()
        
        return selected_task

    def finish_task(self, task_id: int, choices_json: str, t_load_ms: float, t_p_eval_ms: float, t_eval_ms: float, n_p_eval: int, n_eval: int):
        with self.lock:
            self.conn.execute("""UPDATE tasks SET status = 'DONE', choices_json = ?, t_load_ms = ?, t_p_eval_ms = ?, t_eval_ms = ?, n_p_eval = ?, n_eval = ? WHERE task_id = ?""",
                (choices_json, t_load_ms, t_p_eval_ms, t_eval_ms, n_p_eval, n_eval, task_id))
            self.conn.commit()

    def error_task(self, task_id: int):
        error = '{"error": {"message": "Inference error"}}'
        with self.lock:
            self.conn.execute("UPDATE tasks SET status = 'ERROR', choices_json = ? WHERE task_id = ?", (error, task_id, ))
            self.conn.commit()
