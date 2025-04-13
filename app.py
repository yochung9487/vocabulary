from flask import Flask, render_template, request, redirect, url_for
from database import create_db, save_words
from lookup import auto_lookup, auto_lookup_reverse
import random
import sqlite3
from flask import request

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add", methods=["POST"])
def add():
    word = request.form["word"].strip()
    if word:
        data_list = auto_lookup(word)  # 取得所有詞義
        if isinstance(data_list, list):
            # 處理 examples 欄位，確保它是完整的句子
            for item in data_list:
                if isinstance(item.get("examples"), list):
                    # 如果 examples 是句子列表，將其用換行符合併為一個字串
                    item["examples"] = "\n".join(item["examples"])
                elif isinstance(item.get("examples"), str):
                    # 如果 examples 是字串，保持不變
                    item["examples"] = item["examples"]
            save_words(word, data_list)  # 存入資料庫
        # 將搜尋結果傳遞給模板    
        return render_template("add_result.html", word=word, results=data_list)
    return redirect(url_for("index"))

@app.route("/search", methods=["GET"])
def search():
    clean_database()  # 在執行查詢前清理資料庫
    search_word = request.args.get("search_word", "").strip()
    if search_word:
        conn = sqlite3.connect("vocabulary.db")
        cursor = conn.cursor()
        cursor.execute("SELECT translation, part_of_speech, examples FROM vocabulary WHERE word = ?", (search_word,))
        results = cursor.fetchall()
        conn.close()

        if results:
            # 將搜尋結果傳遞給模板
            return render_template("search.html", word=search_word, results=results)
        else:
            return render_template("search.html", word=search_word, results=None, message="找不到相關單字")
    return render_template("search.html", word=None, results=None, message="請輸入要搜尋的單字！")

@app.route("/search_cn", methods=["GET"])
def search_cn():
    # 從 GET 請求中取得查詢關鍵字，假設使用者輸入的是中文
    search_word = request.args.get("search_word", "").strip()
    if search_word:
        conn = sqlite3.connect("vocabulary.db")
        cursor = conn.cursor()
        # 在 translation 欄位中做模糊搜尋（使用 LIKE）
        cursor.execute("""
            SELECT word, translation, part_of_speech, examples 
            FROM vocabulary 
            WHERE translation LIKE ?
        """, ('%' + search_word + '%',))
        results = cursor.fetchall()
        conn.close()

        if results:
            return render_template("search_cn.html", search_word=search_word, results=results)
        else:
            return render_template("search_cn.html", search_word=search_word, results=None, message="找不到相關單字")
    else:
        return render_template("search_cn.html", search_word=None, results=None, message="請輸入要搜尋的中文關鍵字！")

@app.route("/search_cn_reverse", methods=["GET"])
def search_cn_reverse():
    search_word = request.args.get("search_word", "").strip()
    if search_word:
        results = auto_lookup_reverse(search_word)
        return render_template("search_cn_reverse.html", search_word=search_word, results=results)
    return render_template("search_cn_reverse.html", search_word=None, results=None, message="請輸入要查詢的中文內容！")

@app.route("/clean", methods=["GET"])
def clean_database():
        conn = sqlite3.connect("vocabulary.db")
        cursor = conn.cursor()
        
        # 刪除 word 為空或查無翻譯資料的記錄
        cursor.execute("DELETE FROM vocabulary WHERE word IS NULL OR word = '無翻譯資料' OR translation IS NULL OR translation = '無翻譯資料'")

        # 刪除 examples 為空或查無翻譯資料的記錄
        cursor.execute("DELETE FROM vocabulary WHERE examples IS NULL OR examples = '無例句'")
        
        # 刪除 translation、part_of_speech、examples 完全相同的重複記錄，只保留一個
        cursor.execute("""
            DELETE FROM vocabulary
            WHERE rowid NOT IN (
                SELECT MIN(rowid)
                FROM vocabulary
                GROUP BY word, translation, part_of_speech, examples
            )
        """)
        
        conn.commit()
        conn.close()


@app.route("/list", methods=["GET", "POST"])
def list_words():
    clean_database()  # 在執行查詢前清理資料庫

    search_word = request.form.get("search_word", "").strip() if request.method == "POST" else request.args.get("search_word", "").strip()
    page = int(request.args.get("page", 1))  # 獲取當前頁碼，默認為第 1 頁
    per_page = 20  # 每頁顯示的單字數量

    conn = sqlite3.connect("vocabulary.db")
    cursor = conn.cursor()

    if search_word:
        # 如果有搜尋條件，篩選符合條件的單字
        cursor.execute("""
            SELECT word, translation, part_of_speech, examples
            FROM vocabulary
            WHERE word LIKE ?
            ORDER BY word ASC
        """, (f"%{search_word}%",))
    else:
        # 如果沒有搜尋條件，顯示所有單字
        cursor.execute("""
            SELECT word, translation, part_of_speech, examples
            FROM vocabulary
            ORDER BY word ASC
        """)
    words = cursor.fetchall()
    conn.close()

    # 分頁處理
    total_words = len(words)
    total_pages = (total_words + per_page - 1) // per_page  # 計算總頁數
    start = (page - 1) * per_page
    end = start + per_page
    words_paginated = words[start:end]

    # 渲染模板，傳遞分頁數據
    return render_template(
        "list.html",
        words=words_paginated,
        search_word=search_word,
        page=page,
        total_pages=total_pages
    )



@app.route("/quiz")
def quiz():
    conn = sqlite3.connect("vocabulary.db")
    cursor = conn.cursor()
    
    # 隨機選取 5 個單字，每個單字只出現一次
    cursor.execute("""
        SELECT word, translation, part_of_speech, examples 
        FROM vocabulary 
        ORDER BY RANDOM() LIMIT 5
    """)
    words = cursor.fetchall()

    # 為每個單字生成選擇題選項
    quiz_data = []
    for word, correct_translation, part_of_speech, examples in words:
        # 過濾例句中的中文翻譯，僅保留英文部分
        if examples:
            examples = "\n".join([line for line in examples.split("\n") if not any('\u4e00' <= char <= '\u9fff' for char in line)])

        # 隨機選取其他翻譯作為干擾選項
        cursor.execute("""
            SELECT DISTINCT translation 
            FROM vocabulary 
            WHERE translation != ? 
            ORDER BY RANDOM() LIMIT 3
        """, (correct_translation,))
        distractors = [row[0] for row in cursor.fetchall()]
        
        # 確保選項中只有一個正確答案
        options = distractors + [correct_translation]
        random.shuffle(options)  # 隨機排列選項
        
        # 添加題目數據
        quiz_data.append({
            "word": word,
            "options": options,
            "answer": correct_translation,
            "part_of_speech": part_of_speech,
            "examples": examples
        })

    conn.close()
    return render_template("quiz.html", quiz_data=quiz_data)

@app.route('/quiz_result', methods=['POST'])
def quiz_result():
    try:
        num_questions = int(request.form.get("num_questions", 0))
    except ValueError:
        num_questions = 0

    results = []
    for i in range(num_questions):
        word = request.form.get(f"word_{i}", "")
        examples = request.form.get(f"examples_{i}", "")
        user_answer = request.form.get(f"answer_{i}", "")
        correct_answer = request.form.get(f"correct_answer_{i}", "")
        results.append({
            "word": word,
            "examples": examples,
            "user_answer": user_answer,
            "correct_answer": correct_answer
        })

    return render_template("quiz_result.html", results=results)

@app.route("/retry_quiz", methods=["POST"])
def retry_quiz():
    retry_words = request.form.getlist("retry_word")
    if not retry_words:
        return redirect("/quiz")

    conn = sqlite3.connect("vocabulary.db")
    cursor = conn.cursor()
    quiz_data = []

    for word in retry_words:
        cursor.execute("""
            SELECT word, translation, part_of_speech, examples 
            FROM vocabulary 
            WHERE word = ? 
            ORDER BY RANDOM() LIMIT 1
        """, (word,))
        word_data = cursor.fetchone()
        if not word_data:
            continue
        word, correct_translation, part_of_speech, examples = word_data
        if examples:
            examples = "\n".join([line for line in examples.split("\n") if not any('\u4e00' <= char <= '\u9fff' for char in line)])

        cursor.execute("""
            SELECT DISTINCT translation 
            FROM vocabulary 
            WHERE translation != ? 
            ORDER BY RANDOM() LIMIT 3
        """, (correct_translation,))
        distractors = [row[0] for row in cursor.fetchall()]
        options = distractors + [correct_translation]
        random.shuffle(options)

        quiz_data.append({
            "word": word,
            "options": options,
            "answer": correct_translation,
            "part_of_speech": part_of_speech,
            "examples": examples
        })

    conn.close()
    return render_template("quiz.html", quiz_data=quiz_data)

if __name__ == '__main__':
    app.run(debug=True)

if __name__ == "__main__":
    create_db()
    app.run(debug=True)
