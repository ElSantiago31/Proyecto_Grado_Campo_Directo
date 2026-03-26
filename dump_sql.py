import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL ORDER BY name")
rows = cur.fetchall()

with open('base.sql', 'w', encoding='utf-8') as f:
    for name, sql in rows:
        f.write(f"-- Tabla: {name}\n")
        f.write(sql + ";\n\n")

conn.close()
print("SQL dump completado en base.sql")
