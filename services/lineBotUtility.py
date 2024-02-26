import requests
import json
from services import sysConfig
from services.dbUtility import createConnection, update, query

replyURL = 'https://api.line.me/v2/bot/message/reply' #lineBot回復端點

getContent = 'https://api-data.line.me/v2/bot/message/%s/content'
pushMessageURL = 'https://api.line.me/v2/bot/message/push'
#lineBotAPI金鑰
lineBotKey = f'Bearer {sysConfig['LineBotKey']}'

def replyMsg(replyKey, message):
    msg = {
        "replyToken": replyKey,
        "messages":
        [
            {
                "type":"text",
                "text": message
            }
        ]
    }
    header = {"Content-Type" : "application/json", "Authorization" : lineBotKey}
    requests.post(url = replyURL, data = json.dumps(msg), headers = header)

def makeTemplate(altText, type, text):
    if type == 'confirm':
        template = {
            "type": "template",
            "altText": altText,
            "template": {
                "type": "confirm",
                "text": text,
                "actions":[
                    {
                        "type": "message",
                        "label": "是",
                        "text": "對我要買這個"
                    },
                    {
                        "type": "message",
                        "label": "不是",
                        "text": "好像不是這個"
                    }                     
                ]
            }
        }
    elif type == 'buttons':
        template =  {
            "type": "template",
            "altText": altText,
            "template": {
                "type": "buttons",
                "thumbnailImageUrl": "https://cdn-icons-png.freepik.com/512/625/625599.png",
                "imageAspectRatio": "square",
                "imageSize": "cover",
                "imageBackgroundColor": "#FFFFFF",
                "title": "確認付款",
                "text": "👇點擊下面按鈕付款👇",
                "actions": [
                {
                    "type": "uri",
                    "label": "點我付款",
                    "uri": text
                }
                ]
            }
            }
    return template


def templateMsg(replyKey, type, message):
    msg = {
        "replyToken": replyKey,
        "messages":[makeTemplate(message, type, message)]
    }
    header = {"Content-Type" : "application/json", "Authorization" : lineBotKey}
    requests.post(url = replyURL, data = json.dumps(msg), headers = header)   

def pushMessage(pushName, orderID):
    conn = createConnection()
    orderdata = query(conn, 'select ProductID, Quantity, UnitPrice from OderDetails where OderID = %s', orderID)
    productName = query(conn, 'select ProductName from product where ProductID = %d', orderdata[0])[0]
    totalprice = orderdata[1] * orderdata[2]
    print(totalprice)
    msg ={
        "to":pushName,
        "messages":[
            {
                "type":"text",
                "text":f"交易完成\n----------\n這是您的訂單詳細資料\n---------\n商品名稱:{productName}\n商品數量:{orderdata[1]}\n商品價格:{orderdata[2]}\n總計:{totalprice}"
            }
        ]
    }
    myheader = {"Content-Type" : "application/json", "Authorization" : lineBotKey}
    requests.post(url = pushMessageURL, data = json.dumps(msg), headers = myheader)

def readimage(imageid):
    contectUrl = getContent %imageid
    header = {"Authorization" : lineBotKey}
    response = requests.get(contectUrl, headers= header)
    if response.status_code == 200:
        result = response.content
        with open ('C:/image/temp.jpg', 'wb') as file:
            file.write(result)
    return result

def updateUser(id, displayName = '', language = '', imgurl = '', isfollow = False):
    conn = createConnection()
    result = query(conn, 'select UserID from LineUser Where UserID = %s', id)
    if result == None:
        sql = 'Insert Into LineUser(UserID, DisplayName, PictureURL, Language, IsAcive) values (%s, %s, %s, %s, %d)'
        update(conn, sql, (id, displayName, language, imgurl, isfollow))
    else:
        sql = 'update LineUser set IsAcive = %s where UserID = %s'
        update(conn, sql, (isfollow, id))