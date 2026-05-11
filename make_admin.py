"""Promote a user to admin and activate their account."""
import sqlite3
import sys
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'coworking.db')

if not os.path.exists(db_path):
    print(f'Database not found at {db_path}')
    sys.exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

if len(sys.argv) < 2:
    print('Usage: python3 make_admin.py <username>')
    print('Existing users:')
    for row in cursor.execute('SELECT username, role, status FROM users'):
        print(f'  {row["username"]} (role={row["role"]}, status={row["status"]})')
    conn.close()
    sys.exit(1)

username = sys.argv[1]
cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
user = cursor.fetchone()
if not user:
    print(f'User "{username}" not found')
    conn.close()
    sys.exit(1)

cursor.execute('UPDATE users SET role = ?, status = ? WHERE username = ?', ('admin', 'active', username))
conn.commit()
conn.close()
print(f'User "{username}" is now admin (status=active)')
