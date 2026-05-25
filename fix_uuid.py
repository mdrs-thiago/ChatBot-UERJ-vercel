import sqlite3
c = sqlite3.connect('db.sqlite3')
c.execute("UPDATE documents_document SET public_id = replace(public_id, '-', '')")
c.commit()
print("Dashes removed from public_id!")
