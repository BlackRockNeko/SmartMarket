from services import app
from flask import request, make_response
import requests
from services.lineBotUtility import replyMsg, updateUser, readimage, templateMsg
from services.dbUtility import query, createConnection, update
from services.CustomVisionUtility import SharchPhoto
from services import sysConfig
from services.linepayService import linepaySystem, CreateOrderID, updateOrder
import uuid
import tempfile

profileURL = 'https://api.line.me/v2/bot/profile/'
lineBotKey = f'Bearer {sysConfig['LineBotKey']}'
conn = createConnection()

@app.route('/api/v1/linebot/hook', methods = ['POST'])
#LineBot主要程式
def lineBotProcess():
    hookData = request.get_json() # 抓出LineBot的json檔案
    data = hookData['events'][0]
    source = data['source']
    if source['type'] == 'user':
        userID = source['userId'] # 取出line使用者ID
    # print(f'使用者 :{userID}')
    if data['type'] == 'follow':
        replyKey = data['replyToken']
        userProfileURL = profileURL + userID
        proHeader = {"Authorization" : lineBotKey}
        userData = requests.get(url = userProfileURL, headers = proHeader).json()
        displayName = userData['displayName']
        language = userData['language']
        picURL = userData['pictureUrl']
        msg = f'{displayName}安安你好這裡是AI智慧商店,有任何問題都可以詢問喔'
        print(type(msg))
        replyMsg(replyKey, msg)
        updateUser(userID, displayName, language, picURL, True)
        response = make_response("", 204)
    elif data['type'] == 'unfollow':
        updateUser(id = userID, isfollow = False)
        response = make_response("", 204)
    elif data['type'] == 'message':
        messages = data['message']
        if messages['type'] == 'text':
            replyMessage = messages['text']
            replyKey = data['replyToken']
            if replyMessage == '對我要買這個':
                OrderID = CreateOrderID()
                proTemp = query(conn, "select ProductID, Quantity, UnitPrice from TempOrder where CustomerID = %s ORDER BY createtime DESC", userID)
                if proTemp != None:
                    productName = query(conn, "select productName from product where ProductID = %s", proTemp[0])[0]
                    result = linepaySystem(orderid = OrderID, productid = proTemp[0],quantity = proTemp[1], amount= proTemp[2],productname=productName,lineText=True)
                    updateOrder(orderid = OrderID, customerid = userID, productid = proTemp[0], quantity = proTemp[1], price = proTemp[2], paytype = 1)
                    templateMsg(replyKey, 'buttons', result)
                else:
                    replyMsg(replyKey, '好像沒有商品喔,請掃描商品')
            elif replyMessage == '好像不是這個':
                update(conn, 'Delete From TempOrder Where CustomerID = %s', userID)
                replyMsg(replyKey, '好喔,幫你刪除掃條紀錄')
            else:
                replyMsg(replyKey, f'目前還沒有功能喔,只好學你說:{replyMessage}')
            response = make_response("", 204)
        elif messages['type'] == 'image':
            imageid = messages['id']
            resultimg = readimage(imageid)
            Airesult = SharchPhoto(resultimg)
            replyKey = data['replyToken']
            if Airesult == "None":
                replyMsg(replyKey, '沒有找到類似的商品,日後會新增更多商品')
            else:
                templateMsg(replyKey, 'confirm', "找到的商品是" + Airesult)
                produId = query(conn, "select ProductID, UnitPrice from product where ProductName = %s", Airesult)
                id = produId[0]
                price = produId[1]
                update(conn, "insert into TempOrder(CustomerID, ProductID, Quantity, UnitPrice) values (%s, %d, %d, %d)", (userID, produId[0], 1, produId[1]))
                
                
            response = make_response("", 204)
    return response