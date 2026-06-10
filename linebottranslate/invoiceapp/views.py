from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, PostbackEvent, TextSendMessage
from linebot.models import QuickReply, QuickReplyButton, PostbackAction, MessageAction
from linebot.models import TemplateSendMessage, ButtonsTemplate, AudioSendMessage, CarouselTemplate, CarouselColumn
from urllib.parse import parse_qsl
import random
from datetime import datetime

ARTICLES = [
    "Hello, I am a young student. I have a big red apple. I eat the apple in the morning. \n\n(大家好，我是個年輕的學生。我有一顆紅色的大蘋果，我都在早上吃蘋果。)",
    "My family is small. I live with my father and mother. We have a happy dog. \n\n(我的家庭成員不多，我跟爸爸媽媽住在一起，我們還養了一隻很快樂的狗狗。)",
    "Today is a sunny day. I go to the park. I play and run. \n\n(今天是晴朗的一天，我去公園裡開心地跑步和玩耍。)",
    "I see a bird in the sky. The bird is beautiful. It is blue. \n\n(我看到天空中有一隻藍色的小鳥，牠長得非常漂亮。)",
    "My mother buys a green watermelon. It is big and sweet. We eat it in the afternoon. \n\n(媽媽買了一顆綠色的西瓜，吃起來又大又甜，我們在下午一起把它吃光了。)",
    "I have a book and a yellow pencil. I study at school. My teacher is very nice. \n\n(我帶了一本書和黃色的鉛筆去學校上課，我的老師人非常親切喔。)",
    "It is rainy today. The weather is cool. I read a book at home. \n\n(今天外面下著雨，天氣涼涼的，我待在家裡安靜地看書。)",
    "I drink milk and eat bread. Milk is good. I like it. \n\n(我吃麵包配牛奶，牛奶對身體很好，我很喜歡喝。)",
    "My sister has a pink rabbit. It is small and cute. It likes to jump. \n\n(我姊姊有一隻粉紅色的小兔子，小小的非常可愛，而且很喜歡跳來跳去。)",
    "We go to the zoo on Sunday. I see a monkey. The monkey eats a yellow banana. \n\n(我們星期天去動物園玩，我看到一隻猴子正在吃著黃色的香蕉。)",
    "My grandfather is old but happy. He has a brown horse. The horse runs fast. \n\n(爺爺雖然年紀大了，但每天都很開心。他養了一匹棕色的馬，跑起來非常快！)",
    "I like to swim in the water. The water is cold. I am very happy. \n\n(我很喜歡在水裡游泳，雖然水有點冰，但我還是玩得非常開心！)",
    "My grandmother cooks dinner in the evening. We eat rice and fish. \n\n(奶奶晚上煮了豐盛的晚餐，我們一起吃了白飯跟美味的魚。)",
    "I ride my bicycle to the library. The library has many books. I like to read. \n\n(我騎著腳踏車去圖書館，那裡有好多好多書，我非常喜歡閱讀。)",
    "It is a hot day. I drink juice. I sit under a big tree. \n\n(今天天氣非常熱，我坐在大樹底下乘涼，一邊喝著冰涼的果汁。)"
]

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

# 1. 建立 300 字單字庫 (這裡先建立雙向對查字典)
# 提示：為了方便查找，建議英文都存小寫，查詢時也把輸入轉小寫
VOCAB_DB = {
    # 數字與顏色
    "one": "一", "two": "二", "three": "三", "four": "四", "five": "五",
    "six": "六", "seven": "七", "eight": "八", "nine": "九", "ten": "十",
    "red": "紅色", "blue": "藍色", "yellow": "黃色", "green": "綠色",
    "orange": "橘色/柳橙", "purple": "紫色", "black": "黑色", "white": "白色",
    "brown": "棕色", "pink": "粉紅色",
    # 家人與動物
    "father": "爸爸", "mother": "媽媽", "brother": "哥哥/弟弟", "sister": "姐姐/妹妹",
    "grandfather": "爺爺/外公", "grandmother": "奶奶/外婆", "uncle": "叔叔/舅舅", "aunt": "阿姨/姑姑",
    "dog": "狗", "cat": "貓", "bird": "鳥", "fish": "魚", "rabbit": "兔子",
    "duck": "鴨子", "chicken": "雞", "pig": "豬", "cow": "牛", "horse": "馬",
    "sheep": "羊", "monkey": "猴子",
    # 食物
    "apple": "蘋果", "banana": "香蕉", "grape": "葡萄", "watermelon": "西瓜",
    "strawberry": "草莓", "mango": "芒果", "pear": "梨子", "bread": "麵包",
    "rice": "米飯", "noodle": "麵條", "egg": "雞蛋", "milk": "牛奶",
    "juice": "果汁", "water": "水", "cake": "蛋糕", "cookie": "餅乾",
    "candy": "糖果", "chocolate": "巧克力",
    # 文具與人、地點
    "book": "書", "notebook": "筆記本", "pencil": "鉛筆", "pen": "原子筆",
    "eraser": "橡皮擦", "ruler": "尺", "bag": "書包", "desk": "書桌",
    "chair": "椅子", "paper": "紙", "computer": "電腦",
    "teacher": "老師", "student": "學生", "doctor": "醫生", "nurse": "護士",
    "police officer": "警察", "firefighter": "消防員", "driver": "司機",
    "cook": "廚師", "singer": "歌手", "pilot": "飛行員",
    "school": "學校", "classroom": "教室", "library": "圖書館", "park": "公園",
    "zoo": "動物園", "hospital": "醫院", "supermarket": "超市", "restaurant": "餐廳",
    "home": "家", "playground": "操場",
    # 天氣與身體、動作
    "sunny": "晴天的", "rainy": "下雨的", "cloudy": "多雲的", "windy": "有風的",
    "snowy": "下雪的", "hot": "熱的", "warm": "溫暖的", "cool": "涼爽的",
    "cold": "寒冷的", "weather": "天氣", "head": "頭", "eye": "眼睛",
    "ear": "耳朵", "nose": "鼻子", "mouth": "嘴巴", "hand": "手",
    "finger": "手指", "leg": "腿", "foot": "腳", "hair": "頭髮",
    "run": "跑步", "walk": "走路", "jump": "跳躍", "swim": "游泳",
    "eat": "吃", "drink": "喝", "sleep": "睡覺", "read": "閱讀",
    "write": "寫", "study": "學習",
    # 形容詞與時間、交通
    "big": "大的", "small": "小的", "tall": "高的", "short": "矮的/短的",
    "long": "長的", "young": "年輕的", "old": "年老的", "happy": "開心的",
    "sad": "傷心的", "beautiful": "美麗的",
    "monday": "星期一", "tuesday": "星期二", "wednesday": "星期三", "thursday": "星期四",
    "friday": "星期五", "saturday": "星期六", "sunday": "星期日",
    "morning": "早上", "afternoon": "下午", "evening": "晚上",
    "car": "汽車", "bus": "公車", "train": "火車", "bicycle": "腳踏車",
    "airplane": "飛機", "boat": "船", "taxi": "計程車", "truck": "卡車",
    "motorcycle": "機車", "subway": "捷運",
    # 介系詞與疑問詞
    "in": "在 裡 面", "on": "在 上面", "under": "在 下面", "behind": "在 後面",
    "beside": "在 旁邊", "between": "在 之間", "near": "在 附近", "above": "在 上 方",
    "around": "在 周 圍", "by": "在 旁邊",
    "who": "誰", "what": "什麼", "where": "哪裡", "when": "何時",
    "why": "為什麼", "how": "如何", "which": "哪一個", "whose": "誰的",
    "yes": "是", "no": "否"
}

# 反向字典：把上面的「中翻英」也自動建立出來
REVERSE_VOCAB_DB = {v: k for k, v in VOCAB_DB.items()}

def showUse(event):
    try:
        text1 = '''1. 本應用為國小必備單字學習系統。
2. 輸入「@+單字」即可查詢。
3. 例如輸入：@蘋果 ➔ 系統會回答 apple
4. 例如輸入：@apple ➔ 系統會回答 蘋果
5. 查詢單字必須在國小 300 字範圍內喔！'''
        message = TextSendMessage(text=text1)
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

# 新增：核心查單字功能
def searchWord(event, mtext):
    try:
        # 移除開頭的 @ 符號，並去掉前後空白
        query = mtext.replace('@', '').strip()
        
        # 1. 先嘗試用「英文」查「中文」 (轉小寫比對)
        if query.lower() in VOCAB_DB:
            reply_text = VOCAB_DB[query.lower()]
        # 2. 再嘗試用「中文」查「英文」
        elif query in REVERSE_VOCAB_DB:
            reply_text = REVERSE_VOCAB_DB[query]
        # 3. 處理一些斜線分開的多重翻譯情況 (例如: 哥哥/弟弟)
        else:
            found = False
            for eng, chn in VOCAB_DB.items():
                if query in chn: # 模糊比對中文
                    reply_text = eng
                    found = True
                    break
            if not found:
                reply_text = f"抱歉，『{query}』不在國小 300 字的背誦範圍內喔！"

        message = TextSendMessage(text=reply_text)
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='查詢時發生錯誤！'))

# 新增功能：今日必背單字
def get_daily_words(event):
    try:
        # 用當天的日期作為種子，確保今天抽到的單字都一樣
        today_str = datetime.now().strftime("%Y%m%d")
        random.seed(today_str)
        
        vocab_list = list(VOCAB_DB.items())
        daily_words = random.sample(vocab_list, 5)
        
        reply_text = "【今日必背單字】\n每天背 5 個，英文變厲害！\n\n"
        for idx, (eng, chn) in enumerate(daily_words, 1):
            reply_text += f"{idx}. {eng} ({chn})\n"
            
        message = TextSendMessage(text=reply_text)
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

# 新增功能：全部單字列表 (改為輪播按鈕選單)
def get_all_vocab(event):
    try:
        carousel_template = CarouselTemplate(columns=[
            CarouselColumn(
                title='單字分類 (1/5)',
                text='請選擇想學習的單字分類',
                actions=[
                    MessageAction(label='數字', text='@單字分類 數字'),
                    MessageAction(label='顏色', text='@單字分類 顏色'),
                    MessageAction(label='家人', text='@單字分類 家人')
                ]
            ),
            CarouselColumn(
                title='單字分類 (2/5)',
                text='請選擇想學習的單字分類',
                actions=[
                    MessageAction(label='動物', text='@單字分類 動物'),
                    MessageAction(label='食物', text='@單字分類 食物'),
                    MessageAction(label='文具', text='@單字分類 文具')
                ]
            ),
            CarouselColumn(
                title='單字分類 (3/5)',
                text='請選擇想學習的單字分類',
                actions=[
                    MessageAction(label='人物', text='@單字分類 人物'),
                    MessageAction(label='地點', text='@單字分類 地點'),
                    MessageAction(label='天氣', text='@單字分類 天氣')
                ]
            ),
            CarouselColumn(
                title='單字分類 (4/5)',
                text='請選擇想學習的單字分類',
                actions=[
                    MessageAction(label='身體', text='@單字分類 身體'),
                    MessageAction(label='動作', text='@單字分類 動作'),
                    MessageAction(label='形容詞', text='@單字分類 形容詞')
                ]
            ),
            CarouselColumn(
                title='單字分類 (5/5)',
                text='請選擇想學習的單字分類',
                actions=[
                    MessageAction(label='時間', text='@單字分類 時間'),
                    MessageAction(label='交通', text='@單字分類 交通'),
                    MessageAction(label='介系詞與疑問詞', text='@單字分類 介系詞與疑問詞')
                ]
            )
        ])
        message = TemplateSendMessage(alt_text='單字列表分類', template=carousel_template)
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

# 新增功能：根據分類顯示單字
def handle_vocab_category(event, mtext):
    try:
        category = mtext.replace('@單字分類', '').strip()
        vocab_list = list(VOCAB_DB.items())
        
        category_map = {
            '數字': (0, 10, "【數字】"),
            '顏色': (10, 20, "【顏色】"),
            '家人': (20, 28, "【家人】"),
            '動物': (28, 40, "【動物】"),
            '食物': (40, 58, "【食物】"),
            '文具': (58, 69, "【文具】"),
            '人物': (69, 79, "【人物】"),
            '地點': (79, 89, "【地點】"),
            '天氣': (89, 99, "【天氣】"),
            '身體': (99, 109, "【身體】"),
            '動作': (109, 119, "【動作】"),
            '形容詞': (119, 129, "【形容詞】"),
            '時間': (129, 139, "【時間】"),
            '交通': (139, 149, "【交通】"),
            '介系詞與疑問詞': (149, 169, "【介系詞與疑問詞】")
        }
        
        if category in category_map:
            start_idx, end_idx, title = category_map[category]
            words = vocab_list[start_idx:end_idx]
        else:
            title = "【單字列表】"
            words = vocab_list
            
        reply_text = f"{title}\n\n"
        for eng, chn in words:
            reply_text += f"{eng} ({chn})\n"
            
        message = TextSendMessage(text=reply_text)
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

# 新增功能：隨機測驗出題
def generate_quiz(event):
    try:
        # 隨機挑 4 個單字
        vocab_list = list(VOCAB_DB.items())
        choices = random.sample(vocab_list, 4)
        
        # 隨機決定哪個是正確答案
        correct_answer = random.choice(choices)
        question_chn = correct_answer[1]
        correct_eng = correct_answer[0]
        
        reply_text = f"【隨機測驗】\n請問『{question_chn}』的英文是什麼？"
        
        # 建立 QuickReply 按鈕
        quick_reply_buttons = []
        for eng, chn in choices:
            # 改用 PostbackAction，對話框只會出現點擊的單字，
            # 但系統可以收到完整正確答案與使用者答案的資料 (data)
            action = PostbackAction(
                label=eng, 
                display_text=eng,
                data=f"quiz_answer&{correct_eng}&{eng}"
            )
            quick_reply_buttons.append(QuickReplyButton(action=action))
            
        message = TextSendMessage(
            text=reply_text,
            quick_reply=QuickReply(items=quick_reply_buttons)
        )
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

# 新增功能：批改測驗答案 (Postback)
def handle_quiz_answer_postback(event, data):
    try:
        # 格式：quiz_answer&正確答案&使用者答案
        parts = data.split('&')
        if len(parts) >= 3:
            correct_eng = parts[1]
            user_eng = parts[2]
            
            if user_eng == correct_eng:
                reply_text = "答對囉！你太棒了！"
            else:
                correct_chn = VOCAB_DB.get(correct_eng, "")
                reply_text = f"答錯囉！\n正確答案應該是：{correct_eng} ({correct_chn})"
        else:
            reply_text = "測驗格式錯誤，請重新點擊「測驗」。"
            
        message = TextSendMessage(text=reply_text)
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

# 新增功能：今日閱讀連續
def get_daily_article(event):
    try:
        # 取得今天是一年中的第幾天
        day_of_year = datetime.now().timetuple().tm_yday
        article_index = day_of_year % 15
        
        article_text = ARTICLES[article_index]
        
        reply_text = f"【今日閱讀】(第 {article_index + 1} 篇)\n\n{article_text}"
        
        message = TextSendMessage(text=reply_text)
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

# 新增功能：特別教學語音
def handle_special_teaching(event, mtext):
    try:
        # 由於需要 https 的音檔網址，這裡先放一個測試音檔的連結
        # 可以將自己念文章的音檔上傳到雲端，並替換為直連 .mp3 或 .m4a 網址
        audio_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
        
        message = AudioSendMessage(
            original_content_url=audio_url,
            duration=60000  # 語音長度，單位為毫秒 (60000 = 60秒)
        )
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        from linebot.models import TextMessage

        for event in events:
            if isinstance(event, MessageEvent):
                # 確保收到的訊息是文字訊息
                if not isinstance(event.message, TextMessage):
                    continue
                
                mtext = event.message.text.strip()
                
                # 判斷是否為功能指令
                if mtext == '@使用說明':
                    showUse(event)
                elif mtext == '@今日必背單字':
                    get_daily_words(event)
                elif mtext == '@全部單字列表':
                    get_all_vocab(event)
                elif mtext.startswith('@單字分類'):
                    handle_vocab_category(event, mtext)
                elif mtext == '@測驗':
                    generate_quiz(event)
                elif mtext == '@今日閱讀練習':
                    get_daily_article(event)
                elif mtext.startswith('@特別教學'):
                    handle_special_teaching(event, mtext)
                elif mtext.startswith('@'):
                    # 只要是其他 @ 開頭的，一律進到查單字邏輯
                    searchWord(event, mtext)
                else:
                    # 使用者如果沒打 @，可以提醒他正確用法
                    line_bot_api.reply_message(
                        event.reply_token, 
                        TextSendMessage(text="點擊選單可以使用功能喔！\n想要自己查單字的話，請在單字前面加上 @！例如：@蘋果")
                    )
            elif isinstance(event, PostbackEvent):
                data = event.postback.data
                if data.startswith('quiz_answer'):
                    handle_quiz_answer_postback(event, data)

        return HttpResponse()
    else:
        return HttpResponseBadRequest()