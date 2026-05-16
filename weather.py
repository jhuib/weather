import requests

key = "0dfc46503d204650be58ff0e8ed224ba"
location = "101010100"

# 定义两个可能的域名
domains = [
    "https://devapi.qweather.com",  # 免费版
]

for domain in domains:
    url = f"{domain}/v7/weather/now?location={location}&key={key}"
    print(f"正在测试: {domain} ...")

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "200":
                print(f"✅ 成功！该 Key 属于: {domain}")
                print(f"天气: {data['now']['text']}")
                break
            else:
                print(f"❌ 域名正确但 Key 有误: {data}")
        else:
            print(f"❌ 状态码: {response.status_code}")
    except Exception as e:
        print(f"⚠️ 连接失败: {e}")