from flask import Flask, request, abort
import requests
import json
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,LocationMessage,FlexSendMessage
)

app = Flask(__name__)

line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')
#======Define Variables=====#
#----พยากรณ์อากาศ TMD ---#
url_tmd = "https://data.tmd.go.th/nwpapi/v1/forecast/location/daily/at" # From Thailand Meteorological Department
headers_tmd = {
    'accept': "application/json",
    'authorization': "Bearer YOUR_TOKEN",
    }
#------------------------#
#---AQI-----#
token_aqi = "YOUR_TOKEN" # From https://waqi.info/
#=================#
###==============Weather==============###
##--check weather status-##
def weathercheck(c):
    if c ==1:
        return("ท้องฟ้าแจ่มใส (Clear)")
    elif c ==2:
        return("มีเมฆบางส่วน (Partly cloudy)")
    elif c ==3:
        return("เมฆเป็นส่วนมาก (Cloudy)")
    elif c ==4:
        return("มีเมฆมาก (Overcast)")
    elif c ==5:
        return("ฝนตกเล็กน้อย (Light rain)")
    elif c ==6:
        return("ฝนปานกลาง (Moderate rain)")
    elif c ==7:
        return("ฝนตกหนัก (Heavy rain)")
    elif c ==8:
        return("ฝนฟ้าคะนอง (Thunderstorm)")
    elif c ==9:
        return("อากาศหนาวจัด (Very cold)")
    elif c ==10:
        return("อากาศหนาว (Cold)")
    elif c ==11:
        return("อากาศเย็น (Cool)")
    elif c ==12:
        return("อากาศร้อนจัด (Very hot)")
    else :
        return("No data")
##-----------------------##
def tmd_th(lat,lng):
    try:
        querystring = {"lat":lat, "lon":lng, "fields":"cond,tc_max,tc_min"}
        response = requests.request("GET", url_tmd, headers=headers_tmd, params=querystring)
        data_tmd = response.json()
        cond = data_tmd['WeatherForecasts'][0]['forecasts'][0]['data']['cond']#สภาพอากาศวันนี้
        tc_m = data_tmd['WeatherForecasts'][0]['forecasts'][0]['data']['tc_max']#อุณหภูมิสูงสุด
        tcmax_str = str(tc_m)+" °C"
        tc_n = data_tmd['WeatherForecasts'][0]['forecasts'][0]['data']['tc_min']#อุณหภูมิต่ำสุด
        tcmin_str = str(tc_n)+" °C"
        weatherTd = weathercheck(cond)
        return (weatherTd,tcmax_str,tcmin_str)
    except Exception as e:
        print("Error: " + str(e))
###===================================###
###===========AQI===========###
##----Check AQI status----##
def pm25check(pm):
    if pm <= 50 :
      _pm_dict = {"name":"Good",
            "color":"#a8e05f"}      
      return(_pm_dict)
    elif pm <= 100 :
      _pm_dict = {"name":"Moderate",
            "color":"#fdd74b"}
      return(_pm_dict)
    elif pm <= 150 :
      _pm_dict = {"name":"Unhealthy for Sensitive Groups",
            "color":"#fe9b57"}
      return(_pm_dict)
    elif pm <= 200 :
      _pm_dict = {"name":"Unhealthy",
            "color":"#fe6a69"}
      return(_pm_dict)
    elif pm <= 300 :
      _pm_dict = {"name":"Very Unhealthy",
            "color":"#a97abc"}      
      return(_pm_dict)
    else :
      _pm_dict = {"name":"Hazardous",
            "color":"#a87383"} 
      return(_pm_dict)
##------------------------## 
def aqi(lat,lng):
    try:
        url_aqi = "https://api.waqi.info/feed/geo:%s;%s/?token=%s"%(lat,lng,token_aqi)
        response_aqi = requests.request("GET", url_aqi)
        data_aqi = response_aqi.json()
        station = data_aqi['data']['city']['name']
        pm= data_aqi['data']['iaqi']['pm25']['v']
        time_update = str(data_aqi['data']['time']['s'])
        aqi_lv_dict = pm25check(pm)
        return (station,pm,aqi_lv_dict,time_update)
    except Exception as e:
        print("Error: " + str(e))
###=========================###
####========Flex Message (LINE)========####
def flex_message_t(weatherTd,tcmax_str,tcmin_str,station,pm,aqi_lv_dict,time_update):
    flex_str ="""
    {
  "type": "carousel",
  "contents": [
    {
      "type": "bubble",
      "size": "kilo",
      "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": "Air Quality Index",
            "color": "#ffffff",
            "align": "start",
            "size": "xl",
            "gravity": "center",
            "weight": "bold"
          },
          {
            "type": "text",
            "color": "#ffffffaa",
            "align": "start",
            "size": "sm",
            "gravity": "center",
            "margin": "xs",
            "text": "Source : aqicn"
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "color": "#ffffff",
                "size": "sm",
                "wrap": true,
                "text": "%s US AQI",
                "weight": "bold"
              },
              {
                "type": "text",
                "text": "%s",
                "color": "#ffffff",
                "size": "xs",
                "align": "center",
                "wrap": true,
                "weight": "bold"
              }
            ],
            "flex": 1,
            "margin": "lg"
          }
        ],
        "backgroundColor": "%s",
        "paddingTop": "19px",
        "paddingAll": "12px",
        "paddingBottom": "16px"
      },
      "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": "Station",
            "size": "sm",
            "color": "#8C8C8CFF",
            "weight": "bold"
          },
          {
            "type": "text",
            "text": "%s",
            "size": "xs",
            "wrap": true,
            "color": "#8C8C8C",
            "margin": "none",
            "align": "start"
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "text": "Updated",
                "color": "#8C8C8CAA",
                "size": "xxs",
                "wrap": true
              },
              {
                "type": "text",
                "size": "xxs",
                "align": "end",
                "color": "#8C8C8CAA",
                "text": "%s",
                "wrap": false
              }
            ],
            "flex": 1
          }
        ],
        "spacing": "md",
        "paddingAll": "12px"
      },
      "styles": {
        "footer": {
          "separator": false
        }
      }
    },
    {
      "type": "bubble",
      "size": "kilo",
      "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "text",
            "text": "Weather Today",
            "color": "#ffffffff",
            "align": "start",
            "size": "xl",
            "gravity": "center",
            "weight": "bold"
          },
          {
            "type": "text",
            "text": "Source : TMD",
            "color": "#ffffffaa",
            "align": "start",
            "size": "sm",
            "gravity": "center",
            "margin": "xs"
          },
          {
            "type": "text",
            "text": "%s",
            "color": "#ffffff",
            "size": "md",
            "margin": "md",
            "align": "start"
          }
        ],
        "backgroundColor": "#27ACB2",
        "paddingTop": "19px",
        "paddingAll": "12px",
        "paddingBottom": "16px"
      },
      "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "color": "#8C8C8C",
                "size": "sm",
                "wrap": true,
                "text": "Max Temperature"
              },
              {
                "type": "text",
                "text": "%s",
                "color": "#8C8C8C",
                "size": "sm",
                "align": "end"
              }
            ],
            "flex": 1
          },
          {
            "type": "box",
            "layout": "horizontal",
            "contents": [
              {
                "type": "text",
                "color": "#8C8C8C",
                "size": "sm",
                "wrap": true,
                "text": "Min Temperature"
              },
              {
                "type": "text",
                "text": "%s",
                "color": "#8C8C8C",
                "size": "sm",
                "align": "end"
              }
            ],
            "flex": 1
          }
        ],
        "spacing": "md",
        "paddingAll": "12px"
      },
      "styles": {
        "footer": {
          "separator": false
        }
      }
    }
  ]
}"""
    flex_str_2 = flex_str %(pm,aqi_lv_dict['name'],aqi_lv_dict['color'],station,time_update,weatherTd,tcmax_str,tcmin_str)
    return flex_str_2
####===================================####
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    print(body)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=(TextMessage,LocationMessage))
def handle_message(event):
    try:
        if isinstance(event.message,LocationMessage):
            lat = event.message.latitude
            lng = event.message.longitude
            weatherTd,tcmax_str,tcmin_str = tmd_th(lat,lng)
            station,pm,aqi_lv_dict,time_update = aqi(lat,lng)
            flex_str = flex_message_t(weatherTd,tcmax_str,tcmin_str,station,pm,aqi_lv_dict,time_update)
            Reply = FlexSendMessage(alt_text="flex message", contents=json.loads(flex_str)) # Create Flex Message
            line_bot_api.reply_message(event.reply_token,Reply) # Send Flex Message
        else :
            print("Not Location Message")
    except Exception as e:
        print("Error: " + str(e))

if __name__ == "__main__":
    app.run()
