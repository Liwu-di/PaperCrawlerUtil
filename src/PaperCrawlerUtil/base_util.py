# -*- coding: utf-8 -*-
# @Time    : 2023/6/29 11:35
# @Author  : 银尘
# @FileName: base_util.py.py
# @Software: PyCharm
# @Email   : liwudi@liwudi.fun
# @Info    : the most base object or function
from PaperCrawlerUtil.constant import *
from bs4 import Tag
import time
from PIL import Image, ImageDraw, ImageFont


def verify_rule(rule: dict, origin: float or str or Tag) -> bool:
    """
    verify the element string. if element satisfy all rules provided by rule arg,
    return true.
    :param rule:a dictionary that represent rules. the key is the match string and the value
    is the rule. The rule is only support "in" and "not in" and "equal" and "not equal",
    and more than, less than and greater or equal and less than or equal.
     example:{"href": "in"}
    :param origin:the string will be verified
    :return:a bool value represent whether element satisfy all rule
    """
    if rule is None or len(rule) == 0:
        return True
    if origin is None:
        return False
    for key, value in rule.items():
        if str(value) == IN and str(key) not in str(origin):
            return False
        elif str(value) == NOT_IN and str(key) in str(origin):
            return False
        elif str(value) == EQUAL and str(key) != str(origin):
            return False
        elif str(value) == NOT_EQUAL and str(key) == str(origin):
            return False
        elif str(value) == LESS_THAN or str(value) == LESS_THAN or str(value) == LESS_THAN_AND_EQUAL or str(
                value) == MORE_THAN or str(value) == GREATER_AND_EQUAL:
            if type(origin) != float and type(origin) != int:
                return False
            else:
                if str(value) == LESS_THAN and float(origin) >= float(key):
                    return False
                elif str(value) == LESS_THAN_AND_EQUAL and float(origin) > float(key):
                    return False
                elif str(value) == GREATER_AND_EQUAL and float(origin) < float(key):
                    return False
                elif str(value) == MORE_THAN and float(origin) <= float(key):
                    return False
    return True


def get_timestamp(split: str or list = ["-", "-", " ", ":", ":"], accuracy: int = 6) -> str:
    """
    %Y  Year with century as a decimal number.
    %m  Month as a decimal number [01,12].
    %d  Day of the month as a decimal number [01,31].
    %H  Hour (24-hour clock) as a decimal number [00,23].
    %M  Minute as a decimal number [00,59].
    %S  Second as a decimal number [00,61].
    %z  Time zone offset from UTC.
    %a  Locale's abbreviated weekday name.
    %A  Locale's full weekday name.
    %b  Locale's abbreviated month name.
    %B  Locale's full month name.
    %c  Locale's appropriate date and time representation.
    %I  Hour (12-hour clock) as a decimal number [01,12].
    %p  Locale's equivalent of either AM or PM.
    :param split:
    :param accuracy:
    :return:
    """
    time_stamp_name = ["Y", "m", "d", "H", "M", "S", "z", "a", "A", "B", "c", "I", "p"]
    if accuracy >= len(time_stamp_name):
        accuracy = len(time_stamp_name)
    time_style = ""
    if type(split) == str:
        temp = split
        split = []
        for i in range(accuracy):
            split.append(temp)
    elif type(split) == list:
        if len(split) < accuracy:
            for i in range(accuracy - len(split)):
                split.append("-")
    for i in range(accuracy):
        if i == accuracy - 1:
            time_style = time_style + "%" + time_stamp_name[i]
        else:
            time_style = time_style + "%" + time_stamp_name[i] + split[i]
    return time.strftime(time_style, time.localtime())


def get_split(lens: int = 20, style: str = '=') -> str:
    """
    get a series of splits,like "======"
    :param lens: the length of split string
    :param style: the char used to create split string
    :return: a string of split
    """
    splits = ''
    lens = max(lens, 1)
    for i in range(lens):
        splits = splits + style
    return splits





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
