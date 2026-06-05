from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, PostbackEvent, TextSendMessage
from linebot.models import QuickReply, QuickReplyButton, PostbackAction
from urllib.parse import parse_qsl
from translate import Translator
import variable_settings as varset

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

def readData(event): #讀取使用者id及語言設定
    userid = event.source.user_id #讀取使用者id
    try:
        lang = varset.get(userid) #讀取語言設定
    except: #第一次使用時做使用者初始設定
        varset.set(userid, 'en')
        lang = 'en'
    return userid, lang

def showUse(event):
    try:
        text1 = '''1. 本應用可將中文翻譯為多國語言。
2. 預設的翻譯語言為「英文」，發音預設為「不發音」。
3. 按「譯為英文」、「譯為日文」、「其他語文」鈕可設定翻譯後的語言。
4. 按「顯示設定」會顯示目前翻譯後語言及是否要朗讀翻譯後文字。
5. 輸入中文文句即可進行翻譯。'''
        message = TextSendMessage(
            text = text1
        )
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

def langtoword(lang): #將語言代碼轉為中文字
    if lang == 'en':
        word = '英文'
    elif lang == 'ja':
        word = '日文'
    elif lang == 'ko':
        word = '韓文'
    elif lang == 'th':
        word = '泰文'
    elif lang == 'vi':
        word = '越南文'
    elif lang == 'fr':
        word = '法文'
    return word

def setLang(event, lang, userid): #設定翻譯語言
    try:
        varset.set(userid, lang)
        message = TextSendMessage(
            text = '語言設定為：' + langtoword(lang)
        )
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

def setElselang(event): #設定其他語言
    try:
        message = TextSendMessage(
            text = '請選擇語言：',
            quick_reply = QuickReply( #使用快速選單
                items = [
                    QuickReplyButton(
                        action = PostbackAction(label='韓文', data='item=ko')
                    ),
                    QuickReplyButton(
                        action = PostbackAction(label='泰文', data='item=th')
                    ),
                    QuickReplyButton(
                        action = PostbackAction(label='越南文', data='item=vi')
                    ),
                    QuickReplyButton(
                        action = PostbackAction(label='法文', data='item=fr')
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

def showConfig(event, lang): #顯示設定
    try:
        text1 = '語言設定為：' + langtoword(lang)
        message = TextSendMessage(
            text = text1
        )
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

def sendTranslate(event, lang, mtext): #翻譯
    try:
        translator = Translator(from_lang="zh-Hant", to_lang=lang) #來源是中文,翻譯後語言為lang
        translation = translator.translate(mtext) #進行翻譯
        message = TextSendMessage(text = translation)
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

def sendData(event, backdata, userid): #設定其他語言
    lang = backdata.get('item') #取得快速選單的選取值
    setLang(event, lang, userid) #設定翻譯語言

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

        for event in events:
            if isinstance(event, MessageEvent):
                userid, lang = readData(event) #讀取原有設定
                mtext = event.message.text
                if mtext == '@使用說明':
                    showUse(event)
                elif mtext == '@英文':
                    setLang(event, 'en', userid)
                elif mtext == '@日文':
                    setLang(event, 'ja', userid)
                elif mtext == '@其他語文':
                    setElselang(event)
                elif mtext == '@顯示設定':
                    showConfig(event, lang)
                else: #一般文字進行翻譯
                    sendTranslate(event, lang, mtext)

            if isinstance(event, PostbackEvent): #PostbackAction觸發此事件
                userid, lang = readData(event)
                backdata = dict(parse_qsl(event.postback.data)) #取得data資料
                sendData(event, backdata, userid)

        return HttpResponse()
    else:
        return HttpResponseBadRequest()