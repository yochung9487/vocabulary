import sqlite3

# 連接到資料庫
conn = sqlite3.connect("vocabulary.db")
cursor = conn.cursor()

# 查詢 vocabulary 資料表中的所有資料
cursor.execute("SELECT * FROM vocabulary")
rows = cursor.fetchall()

# 列印查詢結果
for row in rows:
    print(row)

# 關閉資料庫連線
conn.close()