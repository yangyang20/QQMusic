from concurrent.futures import ProcessPoolExecutor

import requests;
import json;
import redis
import pymysql
from config import *
headers = {'User-Agent':
               'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'
           }

session = requests.session()
# 歌曲详情
songDdetails = {}


# 将歌手信息存入数据库
def insert_mysql():
    conn = pymysql.connect(host='127.0.0.1',user='root',passwd='393622951',db='QQMusic')
    cur = conn.cursor()
    sql = 'INSERT IGNORE INTO `singerClassify`( `country`) VALUES (%s)'
    result = cur.execute(sql,songDdetails['country'])
    if result:
        conn.commit()
    sql = 'INSERT IGNORE INTO `singerDetails`( `singer_mid`,`singerName`,`country`) VALUES (%(singer_mid)s,%(singerName)s,%(country)s)'
    result = cur.execute(sql, songDdetails)
    if result:
        conn.commit()
    sql ='INSERT IGNORE INTO `songName`( `singer_mid`,`singerName`,`song_mid`) VALUES (%s,%s,%s)'
    result = cur.execute(sql, (songDdetails['singer_mid'],songDdetails['singerName'],songDdetails['_id']))
    if result:
        conn.commit()
    cur.close()
    conn.close()
    return 1


# 将歌曲详情存入数据库
def insert_data():
    # host是redis主机，需要redis服务端和客户端都起着 redis默认端口是6379
    pool = redis.ConnectionPool(host='localhost', port=6379,decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    r.hmset(songDdetails['_id'], {'singerName': songDdetails['singerName'],
                             'singer_pic': songDdetails['singer_pic'],
                             'country':songDdetails['country'],
                             'songName':songDdetails['songName'],
                             'downloadUrl':songDdetails['downloadUrl'],
                              'singer_mid':songDdetails['singer_mid']})



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
            print(songDdetails)
            # insert_data()
            f = open( "/home/yang/Music/"+songDdetails['songName'] + '.m4a', 'wb')
            f.write(response.content)
            f.close()
        else:
            return None
    except Exception:
        return None


# 获取歌曲的songmid参数
def songInformation(singermid):
    url = 'https://u.y.qq.com/cgi-bin/musicu.fcg?callback=getUCGI07447276673576131&g_tk=866772855&jsonpCallback=getUCGI07447276673576131&loginUin=393622951&hostUin=0&'\
            'format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0&data={"comm":{"ct":24,"cv":0},"singer":{"method":"get_singer_detail_info",'\
    '"param":{"sort":5,"singermid":"%s","sin":0,"num":10},"module":"music.web_singer_info_svr"}}' % (singermid)
    try:
        response=session.get(url=url,headers=headers)
        # 去掉多余的字符,将其转换为json
        details = response.text[25:-1]
        songlist=json.loads(details)['singer']['data']['songlist']
        for item in songlist:
            songmid = item['mid']
            songDdetails['songName'] = item['name']
            songDdetails['_id'] = songmid
            # insert_mysql()
            print(songDdetails)
            download(songmid)
    except Exception:
        return None

# 获取所有歌手的singer_mid参数
def singerInformation(index):
    # 假设每个页面都有15个分页
    for page in range(1,15):
        url = 'https://u.y.qq.com/cgi-bin/musicu.fcg?callback=getUCGI19272782514046893&g_tk=866772855&jsonpCallback=getUCGI19272782514046893&loginUin=393622951&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0&data={"comm":{"ct":24,"cv":0},"singerList":{"module":"Music.SingerListServer","method":"get_singer_list",' \
            '"param":{"area":-100,"sex":-100,"genre":-100,"index":%s,"sin":0,"cur_page":%s}}}' % (index,page)
        try:
            response = session.get(url=url,headers=headers)
            # print(response.text)
            details = json.loads(response.text[25:-1])
            singerlist = details['singerList']['data']['singerlist']
            # print(singerlist)
            for singer in singerlist:
                singer_mid = singer['singer_mid']
                songDdetails['singerName'] = singer['singer_name']
                songDdetails['singer_pic'] = singer['singer_pic']
                songDdetails['country'] = singer['country']
                songDdetails['singer_mid'] = singer_mid
                songInformation(singer_mid)
        except Exception:
            print(url)
            return None


# 多进程爬取
def myProcess():
    with ProcessPoolExecutor(max_workers=26) as executor:
        for i in range(1, 26):
            # 创建26个进程，分别执行A-Z分类
            executor.submit(singerInformation, i)


if __name__ == '__main__':
     myProcess()
     # singerInformation(3)
    # download('0021rBlZ1gQiLy')