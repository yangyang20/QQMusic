from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from pydub import AudioSegment
import pymysql
import requests
import redis
import os
import os.path
import sys
import subprocess
import os
session =requests.session()
headers = {'User-Agent':
               'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'
           }
# 歌曲详情
songDdetails ={}
# 先选择标签
def classIfication():
    label = '内地'
    conn = pymysql.connect(host='127.0.0.1',user='root',password='393622951',db='QQMusic')
    cur = conn.cursor()
    sql = "SELECT song_mid from singerDetails left join songName ON singerDetails.singer_mid = songName.singer_mid WHERE singerDetails.country = '%s' " % label
    # 查询所有内地的歌手的mid\
    result = cur.execute(sql)
    if result:
        tuple = cur.fetchall()
        for item in tuple:
            song_mid = str(item)[2:-3]
            readSongInformation(song_mid)
            # print(song_mid)
    cur.close()
    conn.close()

# 读取出歌曲详情
def readSongInformation(name):
    global songDdetails
    # decode_responses=True 自动解码
    pool = redis.ConnectionPool(host='127.0.0.1',port=6379,db=0,decode_responses=True)
    r = redis.Redis(connection_pool=pool)
    songDdetails = r.hgetall(name)
    # print(songDdetails)
    download(name)

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
            f = open( "/home/yang/Music/"+songDdetails['songName'] + '.m4a', 'wb')
            f.write(response.content)
            f.close()
            fileWrite()

        else:
            return None
    except Exception:
        return None

# 文件写入
def fileWrite():
    path = '/home/yang/Music/'
    OUTPUT_DIR = '/home/yang/Music/music'
    # path = os.getcwd()
    filenames = [
        filename
        for filename
        in os.listdir(path)
        if filename.endswith('.m4a')
    ]

    for filename in filenames:
        subprocess.call([
            "ffmpeg", "-i",
            os.path.join(path, filename),
             "-ab", "256k",
            os.path.join(OUTPUT_DIR, '%s.mp3' % filename[:-4])
        ])



if __name__ == '__main__':
    # readSongInformation()
    # classIfication()
    fileWrite()