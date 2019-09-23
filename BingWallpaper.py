#!/bin/python

import os
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
from common_logger import Logger

"""
https://bing.ioliu.cn/v1/?type=json&d=1&w=1920&h=1080
https://bing.ioliu.cn/photo/SakuraFes_ZH-CN1341601988?force=download
http://www.prohui.com/wallpaper/OHR.SpringBadlands_ZH-CN8280871661_1920x1080.jpg
1、优先从bing官网下载
2、增加从ioliu网站下载
3、从本地保存里面拷贝
4、从壁纸网站prohui下载
5、少量手工从第三方下载
"""

logger = Logger('BING_WP')


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


def get_url_content(url):
    '''
    获取403禁止访问的网页
    1、获取内容的链接地址
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
    return content


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


def get_wallpaper_url_ioliu(image_dir, idate_delta):
    """
    获取ioliu下载指定的某一张图片的地址，
    1、图片存放地址
    2、日期间隔
    """

    URL_API = "https://bing.ioliu.cn/v1/"

    image_date = get_date_from_today_by_delta(idate_delta)

    payload = {'type': 'json',
               'd': idate_delta,  # 距离今天第delta天壁纸
               'w': 1920,
               'h': 1080}
    try:
        response = requests.get(URL_API, params=payload)

        if response.status_code != 200:
            time.sleep(3)
            response = requests.get(URL_API, params=payload)
            if response.status_code != 200:
                time.sleep(3)
                response = requests.get(URL_API, params=payload)
                if response.status_code != 200:
                    logger.error("network error,can not get the wallpaper download url")
                    return '', '', image_date
        else:
            if response.json()["status"]["code"] != 200:
                logger.error("can not find the wallpaper in the website")
                return '', '', image_date

    except:
        logger.error("network error,can not connect the website")
        return '', '', image_date

    image_data = response.json()
    image_url = image_data["data"]["url"]
    end_date = image_data["data"]["enddate"]    
    logger.info("get_image: %s %s" % (end_date, image_url))
    str_pic_url = image_url.split("/")
    str_pic_name = str_pic_url[len(str_pic_url) - 1].replace('_1920x1080.jpg', '')
    image_new_url = 'https://bing.ioliu.cn/photo/' + str_pic_name + '?force=download'
    image_path_new_name = image_dir + os.sep + end_date + '_' + str_pic_name + ".jpg"
    #image_path_old_name = image_dir + os.sep + str_pic_name + ".jpg"
    return image_path_new_name, image_new_url, end_date


def get_wallpaper_url_bing(image_dir, idate_delta):
    """
    获取必应官方下载指定的某一张图片的地址，
    1、图片存放地址
    2、日期间隔
    """

    if idate_delta >= 8:
        return '', '', ''

    URL_BING = "http://cn.bing.com"
    URL_API = "http://cn.bing.com/HPImageArchive.aspx"

    image_date = get_date_from_today_by_delta(idate_delta)

    payload = {'format': 'js',
               'idx': 0,
               'n': 10,
               'mkt': 'zh-CN'}
    try:
        response = requests.get(URL_API, params=payload)

        if response.status_code != 200:
            time.sleep(3)
            response = requests.get(URL_API, params=payload)
            if response.status_code != 200:
                time.sleep(3)
                response = requests.get(URL_API, params=payload)
                if response.status_code != 200:
                    logger.error("network error,can not get the wallpaper download url")
                    return '', '', image_date
    except:
        logger.error("network error,can not connect the website")
        return '', '', image_date

    images = response.json()
    icount = 0
    image_path_new_name = ''
    image_new_url = ''
    image_enddate = ''
    while icount < len(images["images"]):
        image_new_url = URL_BING + images["images"][icount]["url"]
        image_enddate = images["images"][icount]["enddate"]
        icount = icount + 1

        if image_enddate == image_date:
            arr_pic_url = image_new_url.split("/")
            str_pic_url = arr_pic_url[len(arr_pic_url) - 1]
            name_index_start = len("th?id=OHR.")
            name_index_endin = str_pic_url.index("_1920x1080.jpg&rf")
            str_pic_name = str_pic_url[name_index_start:name_index_endin]
            image_path_new_name = image_dir + os.sep + image_enddate + '_' + str_pic_name + ".jpg"
            break

    return image_path_new_name, image_new_url, image_enddate


def check_and_copy_exist_image(image_name):
    """
    检查壁纸工具保存的壁纸是否存在已经下载的图片并拷贝到目标目录
    1、图片名称--用于名称比对，确认是否一致
    """

    if image_name == "":
        return False

    local_save_path = "C:\\Users\\Test\\Pictures\\Saved Pictures"

    mini_image_name = image_name.split("\\")
    mini_image_name = mini_image_name[len(mini_image_name) - 1]
    mini_image_name = mini_image_name[9:-4]

    local_image_name_old = local_save_path + os.sep + mini_image_name + '_1920x1080.jpg'
    local_image_name_ohr = local_save_path + os.sep + 'OHR.' + mini_image_name + '_1920x1080.jpg'

    if os.path.exists(local_image_name_old):
        shutil.copyfile(local_image_name_old, image_name)
        return True

    if os.path.exists(local_image_name_ohr):
        shutil.copyfile(local_image_name_ohr, image_name)
        return True

    return False


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

    if check_and_copy_exist_image(image_name):  # 尝试从本地保存的文件中拷贝
        if check_download_image(image_name):
            logger.warn("++==download image from local success: %s" % image_name)
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

    download_assign_one_wallpaper(date_delta, wp_root_dir)


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


def download_bing_wallpaper_main(iparam):
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

    wp_root_dir = user_home + os.sep + "Pictures" + os.sep + "必应壁纸"
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
        dw_count = 15

    if dw_count == 0:
        download_assign_day_wallpaper(iparam, wp_root_dir)
    else:
        download_assign_num_wallpaper(dw_count, wp_root_dir)

    now = datetime.datetime.now()
    get_every_month_count(now.year, wp_root_dir)
    # get_every_month_count('2016', wp_root_dir)
    # get_every_month_count('2017', wp_root_dir)
    # get_every_month_count('2018', wp_root_dir)
    # get_every_month_count('2019', wp_root_dir)


if __name__ == '__main__':
    """
    模块调试
    """

    if len(sys.argv) > 1:
        dw_params = sys.argv[1]
        try:
            dw_params = int(dw_params)
        except Exception as e:
            logger.error("the parameters format not correct, please modify!")
            sys.exit(0)
    else:
        dw_params = ""

    download_bing_wallpaper_main(str(dw_params))
