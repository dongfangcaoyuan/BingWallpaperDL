#!/bin/python
#-*- coding:utf-8 -*-

import os
import re
import sys
import time
import random
import datetime
import argparse
import urllib.request
import requests
import platform
import shutil
import glob

from PIL import Image
from lxml import etree
from common_logger import Logger

"""
http://www.prohui.com/wallpaper/OHR.SpringBadlands_ZH-CN8280871661_1920x1080.jpg
https://www.prohui.com/plugin.php?id=mini_download:index&c=14&types=time&page=2
1、从壁纸网站prohui爬取壁纸
"""

logger = Logger('HUI_WP')

URL_HUI_BASE = 'https://www.prohui.com/plugin.php?id=mini_download:index&c=14&types=time&page=%s'


def get_date_from_today_by_delta(idate_delta):
    """
    获取距离今天X天的某一天日期
    1、 参数为日期距离今天delta天
    """

    d_now = datetime.datetime.now()
    d_old = d_now - datetime.timedelta(days=int(idate_delta))
    syear = str(d_old.year)

    if d_old.month < 10:
        smonth = '0' + str(d_old.month)
    else:
        smonth = str(d_old.month)

    if d_old.day < 10:
        sday = '0' + str(d_old.day)
    else:
        sday = str(d_old.day)

    sOldDate = syear + smonth + sday

    return sOldDate


def get_delta_from_today_by_date(sdate):
    """
    获取某一天到今天日期的距离
    1、 参数为某一天日期
    """

    try:
        idate = int(sdate)
    except Exception as e:
        logger.error("the date format not correct, please modify!")
        return 0

    sdate = str(idate).strip()  # 排除字符串前面的0开头部分和空格

    if len(sdate) != 8:
        logger.error("the date length not correct, please modify!")
        return 0

    d_now = datetime.datetime.now()
    d_old = datetime.datetime.strptime(sdate, "%Y%m%d")
    d_delta = d_now - d_old

    # print(d_delta.days)
    # print(d_delta.microseconds)
    # print(d_delta.seconds)

    return d_delta.days


def check_download_image(image_dir):
    """
    检查下载的图片是否正确
    1、图片带路径名称
    """
    if not os.path.exists(image_dir):
        return False

    try:
        img = Image.open(image_dir)
        imgSize = img.size       # 图片尺寸
        imgwd = img.width        # 图片的宽
        imght = img.height       # 图片的高
        imgft = img.format       # 图像格式

        logger.info("the download file size: %s" % str(imgSize))
        logger.info("the image file width: %s" % str(imgwd))
        logger.info("the file height: %s" % str(imght))
        logger.info("the file format: %s" % str(imgft))

        if int(imght) != 1080:
            try:
                if os.path.exists(image_dir):
                    os.remove(image_dir)
                    logger.info("the damaged file is delete: %s" % str(image_dir))
                    time.sleep(0.1)
            except Exception as e:
                pass

            return False
        else:
            return True

    except Exception as e:
        logger.error("get picture info error: %s" % str(e))

        try:
            if os.path.exists(image_dir):
                os.remove(image_dir)
                logger.info("the damaged file is delete: %s" % str(image_dir))
                time.sleep(0.1)
        except Exception as e:
            pass

        return False


def list_all_files(rootdir):
    """
    列出指定路径下的所有文件
    1、指定的路径
    """

    all_files = []
    list = os.listdir(rootdir)  # 列出文件夹下所有的目录与文件
    for i in range(0, len(list)):
        path = os.path.join(rootdir, list[i])
        if os.path.isdir(path):
            all_files.extend(list_all_files(path))
        if os.path.isfile(path):
            all_files.append(path)
    return all_files


def test_check_image(root_dir):
    """
    开始下载指定的某一张图片并保存
    1、图片带路径名称
    2、和下载地址
    """

    all_files = list_all_files(root_dir)
    for i in range(0, len(all_files)):
        image_path = all_files[i]
        check_download_image(image_path)

    logger.info("File Count: %s" % str(i))


def download_one_image(image_path_name, image_url):
    """
    开始下载指定的某一张图片并保存
    1、图片带路径名称
    2、和下载地址
    """

    logger.info("++==begin download image: %s" % image_url)
    try:
        response = requests.get(image_url)
        if response.status_code != 200:
            logger.error("download the wallpaper error: %s" % image_url)
            return False

        with open(image_path_name, "wb") as code:
            code.write(response.content)

        return True

    except Exception as e:
        logger.error("can not connect website when download: %s" % str(e))
        return False


def chceck_image_exist_by_date(image_date, wp_root_dir):
    """
    通过日期检查指定的图片是否存在
    1、检查图片所指定的日期
    2、图片下载存在根目录
    """

    img_pattern_path = wp_root_dir + os.sep + str(image_date) + '_*.jpg'

    match_image = glob.glob(img_pattern_path)
    iCount = len(match_image)
    if iCount > 0:
        image_name = match_image[0]
    else:
        image_name = ''

    # print(iCount, image_name)
    return iCount, image_name


def download_all_prohui_wallpaper(url, wp_root_dir):
    '''
    从prohui网站下载所有的bing壁纸
    1、prohui网站爬取基地址
    2、保存图片的根目录
    '''

    headers = ["Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36"
               " (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36"
               " (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36",
               "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0"
               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14"
               " (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14",
               "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)"]

    randdom_header = random.choice(headers)
    req = urllib.request.Request(url)
    req.add_header("User-Agent", randdom_header)
    content = urllib.request.urlopen(req).read()
    html = etree.HTML(content)  # 初始化生成一个XPath解析对象
    # result = etree.tostring(html, encoding='utf-8')  # 解析对象输出代码
    links = html.xpath('//ul[@class="appList"]/li[@class="item"]')
    # print(type(html))
    # print(type(result))
    # print(len(result))
    # print(result)
    # print(result[0][0][0][0][0])

    # for item in links:
    #     print(item.attrib)
    #     print(item.tag)
    #     print(item.text)
    # print('当前页面壁纸数量：', len(links))
    wp_count = len(links)
    for index in range(wp_count):
        # links[index]返回的是一个字典
        # if (index % 2) == 0:
        # print(type(links[index]))
        # print(links[index].tag)
        # print(links[index].attrib)
        # print(links[index].text)

        result1 = links[index].xpath('./a/div/span[@class="z"]')
        # print(result1[0].text.strip())
        # for item in result:
        #     #print(item.attrib)
        #     #print(item.tag)
        #     print(item.text)

        result2 = links[index].xpath('./a/img')
        #print(result1[0].text.strip()[0:10], '==', result2[0].attrib['src'].strip())
        # for item in result:
        #     print(item.attrib)
        #     #print(item.tag)
        #     #print(item.text)
        image_date = result1[0].text.strip()[0:10].replace('-', '')
        image_url = result2[0].attrib['src'].strip().replace('/w/500', '/w/1920').replace('/h/284', '/h/1080')
        print(image_url)

        name_index_start = len("http://cdn.prohui.com/wallpaper/")
        name_index_endin = image_url.index("?imageView2")
        str_pic_name = image_url[name_index_start:name_index_endin]

        image_name = wp_root_dir + os.sep + image_date + '_' + str_pic_name

        image_name = image_name.replace('OHR.', '')
        image_name = image_name.replace('_1920x1080', '')
        image_name = image_name.replace('_1080x1920', '')

        print(image_name)

        randdom_header = random.choice(headers)
        req = urllib.request.Request(image_url)
        req.add_header("User-Agent", randdom_header)
        content = urllib.request.urlopen(req).read()

        try:
            with open(image_name, "wb") as code:
                code.write(content)

        except Exception as e:
            logger.error("download image from prohui error: %s" % str(e))


def get_prohui_wpurl_by_index(page_index):
    '''
    从prohui网站获取指定页面的下载地址
    1、指定页面的索引    
    '''

    headers = ["Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36"
               " (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36"
               " (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36",
               "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0"
               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14"
               " (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14",
               "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)"]

    url_hui = URL_HUI_BASE % str(page_index)

    randdom_header = random.choice(headers)
    req = urllib.request.Request(url_hui)
    req.add_header("User-Agent", randdom_header)
    content = urllib.request.urlopen(req).read()
    html = etree.HTML(content)  # 初始化生成一个XPath解析对象
    result = etree.tostring(html, encoding='utf-8')  # 解析对象输出代码
    links = html.xpath('//ul[@class="appList"]/li[@class="item"]')
    wp_count = len(links)
    print('当前页面壁纸数量：', wp_count)
    for index in range(wp_count):
        result1 = links[index].xpath('./a/div/span[@class="z"]')
        result2 = links[index].xpath('./a/img')
        print(result1[0].text.strip()[0:10], '==', result2[0].attrib['src'].strip())

        image_date = result1[0].text.strip()[0:10].replace('-', '')
        image_url = result2[0].attrib['src'].strip().replace('/w/500', '/w/1920').replace('/h/284', '/h/1080')
        print(image_url)

        name_index_start = len("http://cdn.prohui.com/wallpaper/")
        name_index_endin = image_url.index("?imageView2")
        str_pic_name = image_url[name_index_start:name_index_endin]

        image_name = image_date + '_' + str_pic_name

        image_name = image_name.replace('OHR.', '')
        image_name = image_name.replace('_1920x1080', '')
        image_name = image_name.replace('_1080x1920', '')

        print(image_name)


def get_wallpaper_from_prohui(wp_root_dir, idate_delta):
    """
    获取ioliu下载指定的某一张图片的地址，
    1、图片存放地址
    2、日期间隔
    """

    URL_HUI = 'http://cdn.prohui.com/wallpaper/OHR.'

    image_name, image_url, image_date = get_wallpaper_url_ioliu(wp_root_dir, idate_delta)

    if image_name == '':
        return False

    mini_image_name = image_name.split("\\")
    mini_image_name = mini_image_name[len(mini_image_name) - 1]
    mini_image_name = mini_image_name[9:-4]

    image_url_hui = URL_HUI + mini_image_name + '_1920x1080.jpg'

    try:
        picture_data = get_url_content(image_url_hui)
        with open(image_name, "wb") as code:
            code.write(picture_data)

    except Exception as e:
        logger.error("download image from prohui error: %s" % str(e))
        return False

    return True


def download_assign_one_wallpaper(idate_delta, wp_root_dir):
    """
    下载指定的某一张图片
    1、日期间隔
    2、图片存放地址
    3、返回失败的图片日期和名称
    """

    image_date = get_date_from_today_by_delta(idate_delta)

    img_chk_count, image_chk_name = chceck_image_exist_by_date(image_date, wp_root_dir)
    if img_chk_count > 1:       # 如果同一天存在多张则需要手工处理
        logger.error("exists repeat wallpaper on the day: %s" % str(image_date))
        return image_chk_name, image_date

    image_name_bing, image_url_bing, image_date_bing = get_wallpaper_url_bing(wp_root_dir, idate_delta)
    image_name, image_url, image_date = get_wallpaper_url_ioliu(wp_root_dir, idate_delta)

    if image_chk_name != '' and image_name != '' and image_chk_name != image_name:
        logger.error("The exists wallpaper is wrong on the day: %s" % str(image_date))
        logger.error("image_chk_name := %s; image_name := %s" % (image_chk_name, image_name))
        return image_chk_name, image_date

    if image_chk_name != '':
        if check_download_image(image_chk_name):  # 检查是否存在手工下载的文件
            logger.warn("the wallpaper existed: %s" % image_chk_name)
            return '', ''

    if image_name_bing != '' and image_name != '' and image_name_bing == image_name:
        judge_down_from_bing = True
    else:
        logger.error("get name from bing and ioliu is different: %s" % image_name)
        judge_down_from_bing = False

    if image_name_bing != '' and judge_down_from_bing:  # 尝试从bing下载最近八日的图片
        download_one_image(image_name_bing, image_url_bing)
        if check_download_image(image_name):
            logger.warn("++==download image from bing success: %s" % image_name)
            return '', ''

    if image_name != '':
        download_one_image(image_name, image_url)
        if check_download_image(image_name):  # 从ioliu下载图片
            logger.warn("++==download image from ioliu success: %s" % image_name)
            return '', ''

    if get_wallpaper_from_prohui(wp_root_dir, idate_delta):
        if check_download_image(image_name):
            logger.warn("++==download image from prohui success: %s" % image_name)
            return '', ''

    return image_name, image_date  # 如果所有的方式都未能获得图片，则返回下载失败的图片信息


def check_leap_year(syear):
    """
    检查年份是否是闰年
    1、 字符串年份
    """

    if len(str(syear)) != 4:
        logger.error("the year format not correct, please modify!")
        return

    try:
        iyear = int(syear)
    except:
        logger.error("the year is not correct digit, please modify!")
        return

    if iyear % 400 == 0 or (iyear % 4 == 0 and iyear % 100 != 0):
        return True
    else:
        return False


def check_date_format(sdate):
    """
    检查日期是否符合要求
    1、 参数为字符串日期
    """

    if len(str(sdate)) != 8:
        logger.error("the date format not correct, please modify!")
        return False

    try:
        idate = int(sdate)
    except:
        logger.error("the date is not correct digit, please modify!")
        return False

    syear = str(sdate)[0:4]
    smonth = str(sdate)[4:6]
    sday = str(sdate)[6:8]

    now = datetime.datetime.now()

    if int(syear) < 2000 or int(syear) > int(now.year):
        logger.error("the year format not correct, please modify year!")
        return False

    if int(smonth) < 1 or int(smonth) > 12:
        logger.error("the month format not correct, please modify month!")
        return False

    if (int(sday) < 1 or int(sday) > 31) and int(smonth) in [1, 3, 5, 7, 8, 10, 12]:
        logger.error("the day format not correct, please modify day!")
        return False

    if (int(sday) < 1 or int(sday) > 30) and int(smonth) in [4, 6, 9, 11]:
        logger.error("the day format not correct, please modify day!")
        return False

    if (int(sday) < 1 or int(sday) > 29) and int(smonth) == 2 and check_leap_year(int(syear)):
        logger.error("the day format not correct, please modify day!")
        return False

    if (int(sday) < 1 or int(sday) > 28) and int(smonth) == 2 and not check_leap_year(int(syear)):
        logger.error("the day format not correct, please modify day!")
        return False

    return True


def download_assign_num_wallpaper(dw_count, wp_root_dir):
    """
    下载指定数量的图片
    1、 下载图片的数量
    2、 下载图片的路径
    """
    Fail_image = {}

    count = 0
    while (count < dw_count):
        image_date = get_date_from_today_by_delta(count)

        if str(image_date) == '20160304':
            break

        image_name, image_date = download_assign_one_wallpaper(count, wp_root_dir)
        if str(image_date) != '':
            Fail_image[image_date] = image_name

        count = count + 1
        logger.info('The ' + str(count) + ' wallpaper.')

    if len(Fail_image) > 0:
        logger.info('===========================================================')
        logger.info('The Wallpaper that download failed list below.')
        for key in Fail_image:
            if Fail_image[key] != '':
                (filepath, filename) = os.path.split(Fail_image[key])
            else:
                filename = ''

            logger.info('[' + str(key) + '] The image name is: ' + str(filename))


def download_assign_day_wallpaper(sdate, wp_root_dir):
    """
    下载指定某一日的图片
    1、 参数为日期，格式参考：20190101 长度为8已判定，年在2010--2020，月和日符合规格，
    2、 下载图片存在的位置
    """

    syear = str(sdate)[0:4]
    smonth = str(sdate)[4:6]
    sday = str(sdate)[6:8]

    now = datetime.datetime.now()

    d_now = datetime.datetime(int(now.year), int(now.month), int(now.day))
    d_old = datetime.datetime(int(syear), int(smonth), int(sday))

    date_delta = (d_now - d_old).days

    image_name, image_date = download_assign_one_wallpaper(date_delta, wp_root_dir)


def get_every_month_count(syear, wp_root_dir):
    """
    获取每个月下载图片的数量
    1、 指定的年份
    """

    for imonth in range(1, 13):
        if imonth < 10:
            smonth = '0' + str(imonth)
        else:
            smonth = str(imonth)

        sPattern = str(syear) + smonth + '*'

        icount, sname = chceck_image_exist_by_date(sPattern, wp_root_dir)
        logger.info("The number of images in %s is: %s" % (sPattern[0:6], str(icount)))


def download_prohui_wallpaper_main(iparam):
    """
    下载图片的主函数，覆盖所有参数情况
    1、 参数为空，默认下载最近30天
    2、 参数为数字，大于1小于3000, 最近X天以内，否则赋值为1
    3、 具体某一天，字符串长度为8，否则赋值为1
    4、 其他参数提示参数异常需要修改，且只校验第一个参数
    """

    sysstr = platform.system()
    if(sysstr == "Windows"):
        user_home = os.environ['HOMEPATH']
    else:
        user_home = os.environ['HOME']

    wp_root_dir = user_home + os.sep + "Pictures" + os.sep + "品汇壁纸"
    if not os.path.exists(wp_root_dir):
        os.mkdir(wp_root_dir)

    if iparam != "":
        if int(iparam) > 0:
            if len(iparam) != 8:
                if int(iparam) >= 1 and int(iparam) <= 3000:
                    dw_count = int(iparam)
                else:
                    dw_count = 1
            else:
                if check_date_format(iparam):
                    dw_count = 0
                else:
                    return
        else:
            dw_count = 1
    else:
        dw_count = 30

    # if dw_count == 0:
    #     download_assign_day_wallpaper(iparam, wp_root_dir)
    # else:
    #     download_assign_num_wallpaper(dw_count, wp_root_dir)

    get_all_prohui_wallpaper_url(wp_root_dir)

    now = datetime.datetime.now()
    get_every_month_count(now.year, wp_root_dir)
    # get_every_month_count('2016', wp_root_dir)
    # get_every_month_count('2017', wp_root_dir)
    # get_every_month_count('2018', wp_root_dir)
    # get_every_month_count('2019', wp_root_dir)


def get_all_prohui_wallpaper_url(wp_root_dir):
    """
    获取所有的prohui网站壁纸下载地址
    1、 参数为空
    """
    now = datetime.datetime.now()
    interval_dates = get_delta_from_today_by_date('20150512')
    # print(interval_dates)
    imax_page = (interval_dates // 14) + 1
    imax_page = 131
    # print(imax_page)
    for ipage in range(1, imax_page + 1):
        url_hui = URL_HUI_BASE % str(ipage)
        # print(url_hui)
        download_all_prohui_wallpaper(url_hui, wp_root_dir)


if __name__ == '__main__':
    """
    模块调试
    """

    sysstr = platform.system()
    if(sysstr == "Windows"):
        user_home = os.environ['HOMEPATH']
    else:
        user_home = os.environ['HOME']

    wp_root_dir = user_home + os.sep + "Pictures" + os.sep + "品汇壁纸"

    get_every_month_count('2015', wp_root_dir)
    get_every_month_count('2016', wp_root_dir)
    get_every_month_count('2017', wp_root_dir)
    get_every_month_count('2018', wp_root_dir)
    get_every_month_count('2019', wp_root_dir)

    sys.exit(0)

    get_prohui_wpurl_by_index(sys.argv[1])
    sys.exit(0)

    if len(sys.argv) > 1:
        dw_params = sys.argv[1]
        try:
            dw_params = int(dw_params)
        except Exception as e:
            logger.error("the parameters format not correct, please modify!")
            sys.exit(0)
    else:
        dw_params = ""

    download_prohui_wallpaper_main(str(dw_params))
