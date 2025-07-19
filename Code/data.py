user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"

header = \
    {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://link.bilibili.com',
        'referer': 'https://link.bilibili.com/p/center/index',
        'sec-ch-ua': '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': user_agent
    }

start_data = \
    {
        'room_id': '',  # 填自己的room_id
        'platform': 'pc_link',
        'area_v2': '624',
        'backup_stream': '0',
        'csrf_token': '',  # 填csrf
        'csrf': '',  # 填csrf，这两个值一样的
        'build': '1234',
        'version': '1.0.0',
        # 'ts': '',
        # 'type': '2',
    }

stop_data = \
    {
        'room_id': '',  # 一样，改room_id
        'platform': 'pc_link',
        'csrf_token': '',  # 一样，改csrf，两个都改
        'csrf': '',
    }

title_data = \
    {
        'room_id': '',  # 填自己的room_id
        'platform': 'pc_link',
        'title': '',
        'csrf_token': '',  # 填csrf
        'csrf': '',  # 填csrf，这两个值一样的
    }

id_data = \
    {
        'room_id': '',  # 填自己的room_id
        'area_id': 642,
        'activity_id': 0,
        'platform': 'pc_link',
        'csrf_token': '',  # 填csrf
        'csrf': '',  # 填csrf，这两个值一样的
    }

bullet_data = \
    {
        "msg": "",
        "color": 16777215,
        "fontsize": 25,
        "rnd": 0,
        "roomid": 0,
        "csrf_token": '',
        "csrf": '',
    }

version_data = \
    {
        "system_version": 2,
        "ts": "",
    }