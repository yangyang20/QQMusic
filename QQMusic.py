import time
from concurrent.futures import ProcessPoolExecutor

import requests;
import json;
import redis
import pymysql
# from config import *
from requests import ReadTimeout, RequestException

headers = {'User-Agent':
               'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'
           }

session = requests.session()
# 歌曲详情
songDdetails = {}
# 歌手信息
singerInfor ={}
# 不同的歌手分类
singerClassify = {
    '200' : 'getUCGI27230219185676363',
    '2' : 'getUCGI016784581562988454',
    '5' : 'getUCGI5580211627006748',
    '4' : 'getUCGI3536188118037513',
    '3' : 'getUCGI9533971737223138',
    '6' : 'getUCGI09406099001281776'
}

# 将歌手信息存入数据库
def insert_mysql():
    # 数据库信息
    conn = pymysql.connect(host='127.0.0.1', user='root', password="393622951", db='qqmusic')
    cur = conn.cursor()
    sql ='INSERT IGNORE INTO `singerinformation`( `singer_name`,`singer_mid`,`country`,`singer_pic`) VALUES (%s,%s,%s,%s)'
    result = cur.execute(sql, (singerInfor['singerName'],singerInfor['singer_mid'],singerInfor['country'],singerInfor['singer_pic']))
    if result:
        conn.commit()
    cur.close()
    conn.close()
    return 1




# 将歌曲详情存入数据库
def insert_data():
    # host是redis主机，需要redis服务端和客户端都起着 redis默认端口是6379
    # pool = redis.ConnectionPool(host='localhost', port=6379,decode_responses=True)
    # r = redis.Redis(connection_pool=pool)
    # r.hmset(songDdetails['_id'], {'singerName': songDdetails['singerName'],
    #                          'singer_pic': songDdetails['singer_pic'],
    #                          'country':songDdetails['country'],
    #                          'songName':songDdetails['songName'],
    #                          'downloadUrl':songDdetails['downloadUrl'],
    #                           'singer_mid':songDdetails['singer_mid']})
    # 数据库信息
    conn = pymysql.connect(host='127.0.0.1', user='root', password="393622951", db='qqmusic')
    cur = conn.cursor()
    sql = 'INSERT IGNORE INTO `song_details`( `singer_name`,`song_name`,`song_id`,`album`,`download_url`) VALUES (%s,%s,%s,%s,%s)'
    result = cur.execute(sql, (
    songDdetails['singerName'], songDdetails['songName'], songDdetails['_id'], songDdetails['album'],songDdetails['downloadUrl']))
    if result:
        conn.commit()
    cur.close()
    conn.close()
    return 1



# 下载歌曲
def download(songmid):
    filename = 'C400' + songmid
    # 获取vkey
    url = 'https://c.y.qq.com/base/fcgi-bin/fcg_music_express_mobile3.fcg?loginUin=0&hostUin=0' \
        '&cid=205361747&uin=0&songmid=%s&filename=%s.m4a&guid=0' % (songmid, filename)
    try:
        r = session.get(url, headers=headers)
        vkey = r.json()['data']['items'][0]['vkey']
        # 下载歌曲
        url = 'http://dl.stream.qqmusic.qq.com/%s.m4a?vkey=%s&guid=0&uin=0&fromtag=66' % (
            filename, vkey)
        songDdetails['downloadUrl'] = url
        response = requests.get(url, headers=headers)
        if response.status_code ==200:
            insert_data()
            print(songDdetails)
        else:
            return None
    except Exception:
        return None


# 获取歌曲的songmid参数
def songInformation(singermid):
    url = 'https://u.y.qq.com/cgi-bin/musicu.fcg?callback=getUCGI07447276673576131&g_tk=866772855&jsonpCallback=getUCGI07447276673576131&loginUin=393622951&hostUin=0&'\
            'format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0&data={"comm":{"ct":24,"cv":0},"singer":{"method":"get_singer_detail_info",'\
    '"param":{"sort":5,"singermid":"%s","sin":0,"num":10},"module":"music.web_singer_info_svr"}}' % (singermid)
    while True:
        try:
            response=session.get(url=url,headers=headers)
            # 去掉多余的字符,将其转换为json
            details = response.text[25:-1]
            songlist=json.loads(details)['singer']['data']['songlist']
            print('----------------------------------------')
            for item in songlist:
                songmid = item['mid']
                songDdetails['songName'] = item['name']
                songDdetails['_id'] = songmid
                songDdetails['album'] = item['album']['name']
                # print(songDdetails)
                download(songmid)
                continue
            break
        except ReadTimeout:  # 访问超时的错误
            print(url)
            time.sleep(1)
            # return None
        except ConnectionError:  # 网络中断连接错误
            print(url)
            time.sleep(1)
            # return None
        except RequestException:  # 父类错误
            print(url)
            return None

# 获取所有歌手的singer_mid参数
def singerInformation(key,index):
    # 假设每个页面都有5个分页
    for page in range(1,5):
        url = 'https://u.y.qq.com/cgi-bin/musicu.fcg?callback=%s&g_tk=197257997&jsonpCallback=%s&loginUin=393622951&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0&data={"comm":{"ct":24,"cv":0},"singerList":{"module":"Music.SingerListServer","method":"get_singer_list",' \
            '"param":{"area":%s,"sex":-100,"genre":-100,"index":-100,"sin":%s,"cur_page":%s}}}' % (index,index,key,page*80-80,page)
        while True:
            try:
                response = session.get(url=url,headers=headers)
                details = json.loads(response.text[len(index)+1:-1])
                singerlist = details['singerList']['data']['singerlist']
                for singer in singerlist:
                    singer_mid = singer['singer_mid']
                    singerInfor['singerName'] = singer['singer_name']
                    songDdetails['singerName'] = singer['singer_name']
                    singerInfor['singer_pic'] = singer['singer_pic']
                    singerInfor['country'] = singer['country']
                    singerInfor['singer_mid'] = singer_mid
                    insert_mysql()
                    songInformation(singer_mid)
                    continue
                        # print(singerInfor)
                break
            except ReadTimeout:  # 访问超时的错误
                print(url)
                time.sleep(1)
                # return None
            except ConnectionError:  # 网络中断连接错误
                print(url)
                time.sleep(1)
                # return None
            except RequestException:  # 父类错误
                print(url)
                return None


# 多进程爬取
def myProcess():
    with ProcessPoolExecutor(max_workers=len(singerClassify)) as executor:
        for key, value in singerClassify.items():
            # 创建26个进程，分别执行A-Z分类
            # executor.submit(singerInformation, value)
            singerInformation(key,value)


if __name__ == '__main__':
     myProcess()
