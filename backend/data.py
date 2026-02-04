user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
header = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'user-agent': user_agent
}

# 发送弹幕数据模板
bullet_data = {
    "color": 16777215,  # 颜色
    "fontsize": 25,     # 字体大小
    "mode": 1,          # 弹幕模式 (1: 滚动)
    "bubble": 0,
}
