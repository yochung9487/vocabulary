import sqlite3

def create_db():
    conn = sqlite3.connect("vocabulary.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            translation TEXT NOT NULL,
            part_of_speech TEXT,
            examples TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_words(word, data_list):
    conn = sqlite3.connect("vocabulary.db")
    cursor = conn.cursor()
    for item in data_list:
        translation = item.get("translation", "")
        part_of_speech = item.get("part_of_speech", "")
        examples = item.get("examples", "")
        # 確保 examples 是字串
        if isinstance(examples, list):
            examples = "\n".join(examples)
        cursor.execute(
            "INSERT INTO vocabulary (word, translation, part_of_speech, examples) VALUES (?, ?, ?, ?)",
            (word, translation, part_of_speech, examples)
        )
    conn.commit()
    conn.close()

def clean_database():
    conn = sqlite3.connect("vocabulary.db")
    cursor = conn.cursor()

    # 刪除完全重複的記錄，只保留一筆
    cursor.execute("""
        DELETE FROM vocabulary
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM vocabulary
            GROUP BY word, translation, part_of_speech, examples
        )
    """)

    # 刪除無翻譯資料的記錄
    cursor.execute("""
        DELETE FROM vocabulary
        WHERE translation IS NULL OR translation = '無翻譯資料'
    """)

    conn.commit()
    conn.close()
