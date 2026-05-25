import sqlite3
import re
import sys
import os

def process_dump(dump_file, sqlite_db):
    print(f"Reading from {dump_file} and writing to {sqlite_db}")
    conn = sqlite3.connect(sqlite_db)
    cursor = conn.cursor()
    
    with open(dump_file, 'r', encoding='utf-8') as f:
        in_copy = False
        table_name = ""
        columns = []
        
        for line_num, line in enumerate(f, 1):
            if not in_copy:
                # Look for COPY statement
                m = re.match(r'^COPY\s+(?:public\.)?([^\s]+)\s+\(([^)]+)\)\s+FROM\s+stdin;', line)
                if m:
                    table_name = m.group(1)
                    columns = [c.strip() for c in m.group(2).split(',')]
                    in_copy = True
                    print(f"Found table {table_name} with columns {columns}")
            else:
                if line.startswith('\\.'):
                    in_copy = False
                    print(f"Finished {table_name}")
                    conn.commit()
                    continue
                
                # We are inside a COPY block, parse the line
                # fields are separated by tabs
                row = line.rstrip('\n').split('\t')
                
                # Replace \N with None
                row = [None if val == '\\N' else val for val in row]
                
                # Replace escaped chars like \b \r \n \t
                def unescape(val):
                    if val is None: return None
                    val = val.replace('\\b', '\b').replace('\\f', '\f').replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t').replace('\\v', '\v')
                    val = val.replace('\\\\', '\\')
                    return val
                
                row = [unescape(val) for val in row]
                
                placeholders = ','.join(['?'] * len(columns))
                col_names = ','.join(columns)
                query = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
                
                try:
                    cursor.execute(query, row)
                except sqlite3.IntegrityError as e:
                    # Ignore unique constraint violations (maybe data already exists)
                    pass
                except sqlite3.OperationalError as e:
                    if "no such table" in str(e):
                        pass
                    elif "has no column" in str(e):
                        pass
                    else:
                        print(f"Error on table {table_name}: {e}")
                        
    conn.commit()
    conn.close()
    print("Done")

if __name__ == "__main__":
    dump_path = sys.argv[1]
    db_path = sys.argv[2]
    process_dump(dump_path, db_path)
