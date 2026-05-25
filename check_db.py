import sqlite3
import os

# Files in processed folder
processed_dir = 'documents/processed'

# Documents in DB
conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT title, length(content) FROM documents_document ORDER BY title LIMIT 30")
rows = cur.fetchall()
print('First 30 DB titles (format):')
for title, clen in rows:
    print(f'  title={title!r}  content_len={clen}')

conn.close()
