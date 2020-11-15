# -*- coding: utf-8 -*-
import requests, json, re
import time, datetime, os, sys
import getpass
from halo import Halo
import smtplib,email,time
from email.mime.text import MIMEText


class DaKa(object):
    """Hit card class

    Attributes:
        username: (str) 浙大统一认证平台用户名（一般为学号）
        password: (str) 浙大统一认证平台密码
        login_url: (str) 登录url
        base_url: (str) 打卡首页url
        save_url: (str) 提交打卡url
        sess: (requests.Session) 统一的session
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.login_url = "https://zjuam.zju.edu.cn/cas/login?service=https%3A%2F%2Fhealthreport.zju.edu.cn%2Fa_zju%2Fapi%2Fsso%2Findex%3Fredirect%3Dhttps%253A%252F%252Fhealthreport.zju.edu.cn%252Fncov%252Fwap%252Fdefault%252Findex"
        self.base_url = "https://healthreport.zju.edu.cn/ncov/wap/default/index"
        self.save_url = "https://healthreport.zju.edu.cn/ncov/wap/default/save"
        self.sess = requests.Session()

    def login(self):
        """Login to ZJU platform"""
        res = self.sess.get(self.login_url)
        execution = re.search('name="execution" value="(.*?)"', res.text).group(1)
        res = self.sess.get(url='https://zjuam.zju.edu.cn/cas/v2/getPubKey').json()
        n, e = res['modulus'], res['exponent']
        encrypt_password = self._rsa_encrypt(self.password, e, n)

        data = {
            'username': self.username,
            'password': encrypt_password,
            'execution': execution,
            '_eventId': 'submit'
        }
        res = self.sess.post(url=self.login_url, data=data)

        # check if login successfully
        if '统一身份认证' in res.content.decode():
            raise LoginError('登录失败，请核实账号密码重新登录')
        return self.sess
    
    def post(self):
        """Post the hitcard info"""
        res = self.sess.post(self.save_url, data=self.info)
        return json.loads(res.text)
    
    def get_date(self):
        """Get current date"""
        today = datetime.date.today()
        return "%4d%02d%02d" %(today.year, today.month, today.day)
        
    def get_info(self, html=None):
        """Get hitcard info, which is the old info with updated new time."""
        if not html:
            res = self.sess.get(self.base_url)
            html = res.content.decode()
        
        try:
            old_info = json.loads(re.findall(r'oldInfo: ({[^\n]+})', html)[0])
            new_info_tmp = json.loads(re.findall(r'def = ({[^\n]+})', html)[0])
            new_id = new_info_tmp['id']
            name = re.findall(r'realname: "([^\"]+)",', html)[0]
            number = re.findall(r"number: '([^\']+)',", html)[0]
        except IndexError as err:
            raise RegexMatchError('Relative info not found in html with regex')
        except json.decoder.JSONDecodeError as err:
            raise DecodeError('JSON decode error')

        new_info = old_info.copy()
        new_info['id'] = new_id
        new_info['name'] = name
        new_info['number'] = number
        new_info["date"] = self.get_date()
        new_info["created"] = round(time.time())
        # form change
        new_info['jrdqtlqk[]'] = 0
        new_info['jrdqjcqk[]'] = 0
        new_info['sfsqhzjkk'] = 1   # 是否申领杭州健康码
        new_info['sqhzjkkys'] = 1   # 杭州健康吗颜色，1:绿色 2:红色 3:黄色
        new_info['sfqrxxss'] = 1    # 是否确认信息属实
        new_info['jcqzrq'] = ""
        new_info['gwszdd'] = ""
        new_info['szgjcs'] = ""
        self.info = new_info
        return new_info

    def _rsa_encrypt(self, password_str, e_str, M_str):
        password_bytes = bytes(password_str, 'ascii') 
        password_int = int.from_bytes(password_bytes, 'big')
        e_int = int(e_str, 16) 
        M_int = int(M_str, 16) 
        result_int = pow(password_int, e_int, M_int) 
        return hex(result_int)[2:].rjust(128, '0')


# Exceptions 
class LoginError(Exception):
    """Login Exception"""
    pass

class RegexMatchError(Exception):
    """Regex Matching Exception"""
    pass

class DecodeError(Exception):
    """JSON Decode Exception"""
    pass
final_return_text = '' #邮件发送内容

def main(username, password):
    """Hit card process

    Arguments:
        username: (str) 浙大统一认证平台用户名（一般为学号）
        password: (str) 浙大统一认证平台密码
    """
    global final_return_text
    print("\n[Time] %s" %datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("🚌 打卡任务启动")
    spinner = Halo(text='Loading', spinner='dots')
    spinner.start('正在新建打卡实例...')
    dk = DaKa(username, password)
    spinner.succeed('已新建打卡实例')

    spinner.start(text='登录到浙大统一身份认证平台...')
    try:
        dk.login()
        spinner.succeed('已登录到浙大统一身份认证平台')
    except Exception as err:
        spinner.fail(str(err))
        return

    spinner.start(text='正在获取个人信息...')
    try:
        dk.get_info()
        spinner.succeed('%s %s同学, 你好~' %(dk.info['number'], dk.info['name']))
    except Exception as err:
        spinner.fail('获取信息失败，请手动打卡，更多信息: ' + str(err))
        final_return_text = "获取信息失败，请手动打卡。错误信息："+str(err)
        return

    spinner.start(text='正在为您打卡打卡打卡')
    try:
        res = dk.post()
        if str(res['e']) == '0':
            spinner.stop_and_persist(symbol='🦄 '.encode('utf-8'), text='已为您打卡成功！')
            final_return_text = "🦄 已为您打卡成功！"
        else:
            spinner.stop_and_persist(symbol='🦄 '.encode('utf-8'), text=res['m'])
            final_return_text = '🦄  '+res['m']
    except:
        final_return_text = '❌数据提交失败'
        spinner.fail('数据提交失败')
        return 
def sendmail():
    #发送邮件提醒打卡结果
    #SMTP服务器地址
    mail_host = 'host'  
    #用户名
    mail_user = 'username'  
    #密码 
    mail_pass = 'password'   
    #邮件发送方邮箱地址
    sender = 'test@test.com'  
    #邮件接受方邮箱地址，注意需要[]包裹，这意味着你可以写多个邮件地址群发
    receivers = ['test@test.com']

    #设置email信息
    #邮件内容设置
    message = MIMEText(final_return_text,'plain','utf-8')
    #邮件主题       
    message['Subject'] = '每日打卡结果通知' 
    #发送方信息
    message['From'] = sender 
    #接受方信息     
    message['To'] = receivers[0]  


    #登录并发送邮件
    try:
        smtpObj = smtplib.SMTP() 
        #连接到服务器
        smtpObj = smtplib.SMTP_SSL(mail_host)
        #登录到服务器
        smtpObj.login(mail_user,mail_pass) 
        #发送
        smtpObj.sendmail(sender,receivers,message.as_string()) 
        #退出
        smtpObj.quit() 
        print('邮件发送成功')
    except smtplib.SMTPException as e:
        print('邮件发送失败',e) #打印错误

if __name__=="__main__":
        main("你的学号","统一认证密码")
        print(final_return_text)
        sendmail()
        sys.exit(0)

