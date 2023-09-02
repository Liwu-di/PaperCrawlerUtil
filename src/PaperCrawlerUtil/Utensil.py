# -*- coding: utf-8 -*-
# @Time    : 2023/8/30 20:32
# @Author  : 银尘
# @FileName: Utensil.py
# @Software: PyCharm
# @Email   : liwudi@liwudi.fun
# @Info    : some useful tools
import json

import requests
from PIL import Image, ImageDraw, ImageFont


def add_text_to_image(image, text, position, font_size=12, text_color=(255, 255, 255)):
    font = ImageFont.truetype("simsun.ttc", font_size)
    draw = ImageDraw.Draw(image)
    draw.text(position, text, font=font, fill=text_color)


def add_hollow_watermark_to_image(image, text, font_size=36, outline_color=(0, 0, 0), outline_width=1):
    watermark_font = ImageFont.truetype("STCAIYUN.TTF", font_size)  # 使用华文彩云字体
    text_width, text_height = watermark_font.getsize(text)

    # Create a new image with transparent background
    watermark_image = Image.new("RGBA", (text_width + 2 * outline_width, text_height + 2 * outline_width), (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark_image)

    # Draw the outline
    for x_offset in range(-outline_width, outline_width + 1):
        for y_offset in range(-outline_width, outline_width + 1):
            draw.text((outline_width + x_offset, outline_width + y_offset), text, font=watermark_font,
                      fill=outline_color)

    return watermark_image


def add_water_paint(image_path, latitude, longitude, address, timestamp, altitude
                    , weather, note, watermark_text="现场拍照", out="output_image.png"):
    image = Image.open(image_path)

    # Add text information to the image
    text_info = f"经度：{longitude}\n纬度：{latitude}\n地址：{address}\n时间：{timestamp}\n海拔：{altitude}\n天气：{weather}\n备注：{note}"
    text_position = (40, image.height - 150)
    add_text_to_image(image, text_info, text_position)

    # Add hollow watermark to the center of the image
    watermark_image = add_hollow_watermark_to_image(image, watermark_text, outline_color=(0, 0, 0),
                                                    outline_width=0)  # 调整为更细的边框
    watermark_position = ((image.width - watermark_image.width) // 2, (image.height - watermark_image.height) // 2)
    image.paste(watermark_image, watermark_position, watermark_image)

    image.save(out)
    image.show()


class SMSClient:
    def __init__(self, access_key_id, access_key_secret, sign_name, template_code):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.sign_name = sign_name
        self.template_code = template_code
        self.url = "https://dysmsapi.aliyuncs.com/"

    def send_sms(self, phone_number, template_param):
        data = {
            "AccessKeyId": self.access_key_id,
            "AccessKeySecret": self.access_key_secret,
            "PhoneNumbers": phone_number,
            "SignName": self.sign_name,
            "TemplateCode": self.template_code,
            "TemplateParam": json.dumps(template_param)
        }

        try:
            response = requests.post(self.url, data=data)
            response_json = response.json()
            if response_json.get('Code') == 'OK':
                print("短信发送成功")
            else:
                print(f"短信发送失败，错误信息：{response_json.get('Message')}")
        except Exception as e:
            print(f"发送短信时出现异常：{e}")


if __name__ == "__main__":
    access_key_id = "your_access_key_id"
    access_key_secret = "your_access_key_secret"
    sign_name = "your_sign_name"
    template_code = "your_template_code"

    client = SMSClient(access_key_id, access_key_secret, sign_name, template_code)

    phone_number = input("请输入接收短信的手机号码：")
    message = input("请输入要发送的短信内容：")

    template_param = {
        "code": message
    }

    client.send_sms(phone_number, template_param)
