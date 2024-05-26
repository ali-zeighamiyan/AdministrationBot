import sqlite3
class DataBaseFetch:
    def __init__(self, db_name) -> None:
        self.conn = sqlite3.connect(db_name)
        self.conn.execute('PRAGMA foreign_keys = ON')  # Enable foreign key support

        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS workers (
                worker_username TEXT,
                worker_name TEXT PRIMARY KEY
            )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            role_name TEXT PRIMARY KEY
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS worker_roles (
            worker_name TEXT,
            role_name TEXT,
            FOREIGN KEY (worker_name) REFERENCES workers(worker_name) ON DELETE CASCADE,
            FOREIGN KEY (role_name) REFERENCES roles(role_name) ON DELETE CASCADE,
            PRIMARY KEY (worker_name, role_name)
        )
        ''')
        self.conn.commit()    

    def add_worker(self, worker_name, worker_username):
        self.cursor.execute('''
            INSERT INTO workers (worker_name, worker_username) VALUES (?, ?)
            ON CONFLICT(worker_name) DO UPDATE SET worker_name=excluded.worker_name, worker_username=excluded.worker_username
        ''', (worker_name, worker_username))
        self.conn.commit()

    def get_workers(self):
        self.cursor.execute('SELECT worker_name, worker_username FROM workers')
        workers = self.cursor.fetchall()
        return workers

    def add_role(self, role_name):
        self.cursor.execute('INSERT OR IGNORE INTO roles (role_name) VALUES (?)', (role_name,))
        self.conn.commit()
        
    def assign_role_to_worker(self, worker_name, role_name):
        self.cursor.execute('''
                            INSERT OR IGNORE INTO worker_roles (worker_name, role_name) VALUES (?, ?)
                            ''', (worker_name, role_name))
        self.conn.commit()

    # Function to get all workers with their roles
    def get_workers_with_roles(self, role=None):
        query = '''
            SELECT wr.worker_name, wr.role_name
            FROM worker_roles wr
        '''
        if role:
            query += "\n" + "WHERE wr.role_name = ?"
            self.cursor.execute(query, (role, ))
        else:
            self.cursor.execute(query)
            
        return self.cursor.fetchall()

    # Function to get all roles with their workers
    def get_roles_with_workers(self, worker=None):
        query = '''
            SELECT wr.role_name, wr.worker_name
            FROM worker_roles wr
        '''
        if worker:
            query += "\n" + "WHERE wr.worker_name = ?"
            self.cursor.execute(query, (worker, ))
        else:
            self.cursor.execute(query)
        res = self.cursor.fetchall()
        if worker:
            res = [role[0] for role in res]
        return res

    
    def delete_role_from_worker(self, worker_name, role_name):
        self.cursor.execute('SELECT worker_name, role_name FROM worker_roles WHERE worker_name = ? AND role_name = ?', (worker_name, role_name))
        if self.cursor.fetchone():
            self.cursor.execute('DELETE FROM worker_roles WHERE worker_name = ? AND role_name = ?', (worker_name, role_name))
            self.conn.commit()
            print(f"Role '{role_name}' removed from worker '{worker_name}'.")
        
        else:
            print(f"Role '{role_name}' from worker '{worker_name}' doesn't exist!.")
            
    def delete_worker(self, worker_name):
        self.cursor.execute('DELETE FROM workers WHERE worker_name = ?', (worker_name, ))
        self.conn.commit()
        print(f"worker: {worker_name} Removed!")

