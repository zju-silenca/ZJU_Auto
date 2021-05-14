import requests
import json
import re
import sys

if __name__ == "__main__":
    getToken_url = 'https://qczj.h5yunban.com/qczj-youth-learning/cgi-bin/login/we-chat/callback?'
    getUserInfo_url = 'https://qczj.h5yunban.com/qczj-youth-learning/cgi-bin/user-api/course/last-info'
    getClass_url = 'https://qczj.h5yunban.com/qczj-youth-learning/cgi-bin/common-api/course/current'
    checkin_url = 'https://qczj.h5yunban.com/qczj-youth-learning/cgi-bin/user-api/course/join'
    openId = {
        'appid':'wx56b888a1409a2920',
        'openid': 'oO-a2tzI7bG_4nBsKwBckYO4rZK4'
    }
    headers = {
        'Content-Type': 'text/plain'
    }
    try:
        getToken = requests.get(url=getToken_url,params=openId,headers=headers)
        Token_raw = getToken.text

        Token = re.findall('[A-Z0-9]{8}[-][A-Z0-9]{4}[-][A-Z0-9]{4}[-][A-Z0-9]{4}[-][A-Z0-9]{12}', Token_raw)[0]
        print('获取Token为:'+Token)
    except:
        print('获取Token失败，请检查openId是否正确')
    accessToken = {
        'accessToken':Token
    }
    try:
        getUserInfo = requests.get(getUserInfo_url,params=accessToken,headers=headers)
        userInfo = getUserInfo.json()

        cardNo = userInfo["result"]["cardNo"]
        nid = userInfo["result"]["nid"]
        getClass = requests.get(getClass_url,params=accessToken,headers=headers)
        Class = getClass.json()
        classId = Class["result"]["id"]
        Faculty = userInfo["result"]["nodes"][2]["title"]+userInfo["result"]["nodes"][3]["title"]
        print('签到课程为：'+classId,'\n您填写的个人信息为：'+ cardNo,'\n您的签到所属组织为：' +Faculty)
    except:
        print('获取历史信息失败，请您手动打卡')

    checkinData = {
        'course':classId,
        'subOrg':None,
        'nid':nid,
        'cardNo':cardNo
    }


    checkin = requests.post(checkin_url,params=accessToken,data=json.dumps(checkinData),headers=headers)
    result = checkin.json()

    if(result["status"]==200):
        print("签到成功")
    else:
        print('出现错误，错误码：'+ str(result["status"]))
        print('错误信息：'+result["message"])
    input('按任意键关闭')
    sys.exit(0)
    