import requests
from bs4 import BeautifulSoup
import time
import random

def is_sentence(text):
    """判斷傳入的文字是否看起來像一句完整的句子"""
    text = text.strip()
    words = text.split()
    # 若至少有5個單字，且結尾為標點或包含逗號，則視為完整句子
    if len(words) >= 5 and (text.endswith('.') or text.endswith('?') or text.endswith('!') or ',' in text):
        return True
    # 或若字數較多（超過30個字元）且首字母大寫
    if len(text) > 30 and text[0].isupper():
        return True
    return False

def auto_lookup(word):
    url = f"https://dictionary.cambridge.org/zht/詞典/英語-漢語-繁體/{word}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.google.com/"
    }
    
    try:
        time.sleep(random.uniform(1, 3))  # 增加隨機延遲，模擬人類行為
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 抓取所有詞義區塊
            entries = soup.find_all("div", class_="pr entry-body__el")
            if not entries:
                print("無法找到翻譯資料，請檢查網頁結構或單字拼寫是否正確。")
                return []
            
            results = []
            for entry in entries:
                # 抓取詞性
                pos_elem = entry.find("span", class_="pos dpos")
                part_of_speech = pos_elem.text.strip() if pos_elem else "無詞性資料"
                
                # 抓取該詞性的所有定義
                sense_blocks = entry.find_all("div", class_="def-block ddef_block")
                
                for block in sense_blocks:
                    # 抓取翻譯
                    translation_elem = block.find("span", class_="dtrans")
                    translation = translation_elem.text.strip() if translation_elem else "無翻譯資料"
    
                    # 抓取例句
                    example_elems = block.find_all("div", class_="examp dexamp")
                    examples = [example.text.strip() for example in example_elems] if example_elems else ["無例句"]
                    
                    results.append({
                        'part_of_speech': part_of_speech,
                        'translation': translation,
                        'examples': examples
                    })
            
            return results
        else:
            print(f"HTTP 請求失敗，狀態碼：{response.status_code}")
            return []
    
    except requests.exceptions.RequestException as e:
        print(f"發生錯誤：{e}")
        return []

import requests
from bs4 import BeautifulSoup
import time
import random

def is_sentence(text):
    """判斷傳入的文字是否看起來像一句完整的句子"""
    text = text.strip()
    words = text.split()
    if len(words) >= 5 and (text.endswith('.') or text.endswith('?') or text.endswith('!') or ',' in text):
        return True
    if len(text) > 30 and text[0].isupper():
        return True
    return False

def auto_lookup_reverse(chinese_word):
    """
    輸入中文，爬取劍橋字典漢語-繁體-英語頁面中的所有英文單字、詞性、定義、中文解釋與例句。
    如果例句中有斜線且不是完整句子，則拆分成多個單字；若看起來像完整句子，則保留原樣。
    中文解釋改從前一個 <div class="dpos-h di-head normal-entry"> 中抓取其 <h2> 的內容。
    """
    url = f"https://dictionary.cambridge.org/zht/詞典/漢語-繁體-英語/{chinese_word}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.google.com/"
    }
    
    try:
        time.sleep(random.uniform(1, 3))  # 避免過於頻繁的請求
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 每個英文單字的區塊在 <div class="dwl han dsensezh">內
            entries = soup.find_all("div", class_="dwl han dsensezh")
            if not entries:
                print("無法找到翻譯資料，請檢查網頁結構或查詢內容是否正確。")
                return []
            
            results = []
            for entry in entries:
                # 1. 抓取英文單字：從 <span class="dtrans"> 中取得
                word_elem = entry.find("span", class_="dtrans")
                english_word = word_elem.text.strip() if word_elem else "無英文單字"
                
                # 2. 抓取詞性：從 <span class="pos dpos-zh lmr-10 hdib"> 中取得
                pos_elem = entry.find("span", class_="pos dpos-zh lmr-10 hdib")
                part_of_speech = pos_elem.text.strip() if pos_elem else "無詞性資料"
                
                # 3. 抓取英文定義（假設呈現在 <div class="def"> 中）
                def_elem = entry.find("div", class_="def")
                definition = def_elem.text.strip() if def_elem else "無英文定義"
                
                # 4. 抓取中文解釋：從 entry 前一個區塊中取得
                chinese_head_elem = entry.find_previous("div", class_="dpos-h di-head normal-entry")
                if chinese_head_elem:
                    ch_title = chinese_head_elem.find("h2", class_="tw-bw dhw dpos-h_hw di-title")
                    chinese_explanation = ch_title.text.strip() if ch_title else ""
                else:
                    chinese_explanation = ""
                
                # 5. 抓取例句：從 <span class="dtrans-egzh"> 中取得原始例句文字
                ex_elem = entry.find("span", class_="dtrans-egzh")
                if ex_elem:
                    raw_example = ex_elem.text.strip()
                    if "/" in raw_example:
                        parts = raw_example.split("/")
                        if all(not is_sentence(part) for part in parts):
                            derived_examples = []
                            for part in parts:
                                derived_examples.extend(part.split())
                            examples = derived_examples if derived_examples else ["無例句"]
                        else:
                            examples = [raw_example]
                    else:
                        examples = [raw_example]
                else:
                    examples = ["無例句"]

                # 6. 抓取例句的中文解釋：從 <span class="trans dtrans dtrans-zh"> 中取得
                ex_translation_elem = entry.find("span", class_="dtrans-eg-transzh lmr-10 hdb")
                example_translation = ex_translation_elem.text.strip() if ex_translation_elem else "無例句中文解釋"
                
                results.append({
                    'english_word': english_word,
                    'part_of_speech': part_of_speech,
                    'definition': definition,
                    'chinese_explanation': chinese_explanation,
                    'examples': examples,
                    'example_translation': example_translation
                })
            
            return results
        else:
            print(f"HTTP 請求失敗，狀態碼：{response.status_code}")
            return []
    
    except requests.exceptions.RequestException as e:
        print(f"發生錯誤：{e}")
        return []

# 測試範例
if __name__ == "__main__":
    chinese_word_to_lookup = input("請輸入要查詢的中文單字：")
    reverse_results = auto_lookup_reverse(chinese_word_to_lookup)
    if reverse_results:
        print("查詢結果：")
        for idx, result in enumerate(reverse_results, 1):
            print(f"意思 {idx}:")
            print(f"英文單字：{result['english_word']}")
            print(f"詞性：{result['part_of_speech']}")
            print(f"英文定義：{result['definition']}")
            print(f"中文解釋：{result['chinese_explanation']}")
            print("例句：")
            for ex_idx, example in enumerate(result['examples'], 1):
                print(f"  {ex_idx}. {example}")
            print("-" * 40)

# 測試範例
if __name__ == "__main__":
    word_to_lookup = input("請輸入要查詢的單字：")
    results = auto_lookup(word_to_lookup)
    if results:
        print("查詢結果：")
        for idx, result in enumerate(results, 1):
            print(f"意思 {idx}:")
            print(f"詞性：{result['part_of_speech']}")
            print(f"翻譯：{result['translation']}")
            print("例句：")
            for ex_idx, example in enumerate(result['examples'], 1):
                print(f"  {ex_idx}. {example}")
            print("-" * 40)

    chinese_word_to_lookup = input("請輸入要查詢的中文單字：")
    reverse_results = auto_lookup_reverse(chinese_word_to_lookup)
    if reverse_results:
        print("查詢結果：")
        for idx, result in enumerate(reverse_results, 1):
            print(f"意思 {idx}:")
            print(f"英文單字：{result['english_word']}")
            print(f"詞性：{result['part_of_speech']}")
            print(f"翻譯：{result['definition']}")
            print("例句：")
            for ex_idx, example in enumerate(result['examples'], 1):
                print(f"  {ex_idx}. {example}")
            print("-" * 40)