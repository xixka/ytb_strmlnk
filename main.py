import re
import json
import requests
import os

def __extract_yt_initial_data(html_content):
    """从HTML中提取ytInitialData"""
    pattern = r'var\s+ytInitialData\s*=\s*({.*?});\s*</script>'
    match = re.search(pattern, html_content, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    raise ValueError("未找到ytInitialData")

def __parse_metadata_data(initial_data):
    """解析播放列表数据结构"""
    data = {}

    # 提取播放列表元数据
    metadata = initial_data['metadata']['playlistMetadataRenderer']
    data['title'] = metadata['title']
    # playlist_data['description'] = metadata.get('description', {}).get('simpleText', '')
    return data


def __parse_playlist_data(initial_data):

    # 提取视频列表
    videos = []
    # 提取播放列表项
    contents = initial_data['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer'][
        'contents'][0]['itemSectionRenderer']['contents'][0]['playlistVideoListRenderer']['contents']
    # 非法字符正则表达式（过滤Windows/Unix非法字符）
    ILLEGAL_CHARS = r'[\/:*?"<>|]'

    for item in contents:
        try:
            video = item['playlistVideoRenderer']
            video_id = video['videoId']
            index = int(video['index']['simpleText'])  # 获取集数序号
            # 提取原始标题
            raw_title = video['title']['runs'][0]['text']
            # 清理非法字符
            clean_title = re.sub(ILLEGAL_CHARS, '_', raw_title)
            # 生成文件名（保留前80个字符避免过长）
            safe_filename = clean_title.strip() + ".strmlnk"

            video_url = f"https://www.youtube.com/watch?v={video_id}"
            videos.append({
                'title':safe_filename,
                'url': video_url
            })
        except KeyError as e:
            print(f"跳过无效项，缺少关键字段：{e}")
        except Exception as e:
            print(f"处理时发生错误：{e}")
    return videos

def __generate_strm_files(videos, output_dir='playlist_strm'):
    """生成STRM文件"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for video in videos:
        # 写入文件
        with open(os.path.join(output_dir, video['title']), 'w', encoding='utf-8') as f:
            f.write(f"{video['url']}\n")



def makeSTRM(playlist_url,proxy):
    try:
        # 获取并解析数据
        html = __get_playlist_html(playlist_url,proxy)
        initial_data = __extract_yt_initial_data(html)
        playlist_data = __parse_playlist_data(initial_data)
        title = __parse_metadata_data(initial_data)['title']
        # 生成文件
        __generate_strm_files(playlist_data)
        # 输出统计信息
        print(f"视频数量：{len(playlist_data)}")
        print(f"STRM文件已生成到：playlist_strm 目录")

    except Exception as e:
        print(f"发生错误：{str(e)}")


def __get_playlist_html(url,proxy):
    """获取播放列表页面HTML"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    proxies = {}
    if  proxy:
        # 定义代理（替换为实际代理地址和端口）
        proxies = {
            'http': proxy,  # HTTP代理
            'https': proxy  # HTTPS代理
        }
    response = requests.get(url, headers=headers, proxies=proxies)
    response.raise_for_status()
    return response.text


if __name__ == "__main__":
    # 代理地址输入（自动补全协议头）
    proxy_input = input("请输入代理地址（默认 127.0.0.1:1071）: ").strip()
    if not proxy_input:
        proxy = "http://127.0.0.1:1071"
    else:
        # 自动添加 http:// 前缀如果用户没有输入协议
        if not proxy_input.startswith(('http://', 'https://', 'socks5://')):
            proxy = f"http://{proxy_input}"
        else:
            proxy = proxy_input

    # 播放列表URL输入（强制必须输入）
    playlist_url = input("请输入YouTube播放列表URL: ").strip()
    if not playlist_url:
        playlist_url = "https://www.youtube.com/playlist?list=PLNMQ7bxchKgcgy9xu_gCz1zg0HVSnTtuS"

    makeSTRM(playlist_url, proxy)
    
