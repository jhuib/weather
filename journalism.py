import requests
from bs4 import BeautifulSoup
import csv
import sqlite3
import time
import schedule

# ====================== 配置 ======================
MAX_PAGE = 3
SAVE_CSV = "cctv_world.csv"
DB_FILE = "news.db"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


# ==================================================

# ---------------------- 数据库初始化 ----------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
              CREATE TABLE IF NOT EXISTS cctv_world
              (
                  id
                  INTEGER
                  PRIMARY
                  KEY
                  AUTOINCREMENT,
                  title
                  TEXT
                  UNIQUE,
                  news_time
                  TEXT,
                  link
                  TEXT
                  UNIQUE,
                  content
                  TEXT,
                  crawl_time
                  TIMESTAMP
                  DEFAULT
                  CURRENT_TIMESTAMP
              )
              ''')
    conn.commit()
    conn.close()


# ---------------------- 判断是否已存在（去重） ----------------------
def is_duplicate(link):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM cctv_world WHERE link = ?", (link,))
    res = c.fetchone()
    conn.close()
    return res is not None


# ---------------------- 插入数据库 ----------------------
def insert_news(news):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
                  INSERT INTO cctv_world (title, news_time, link, content)
                  VALUES (?, ?, ?, ?)
                  ''', (news["title"], news["time"], news["link"], news["content"]))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


# ---------------------- 保存到 CSV ----------------------
def save_csv(news_list):
    with open(SAVE_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["序号", "标题", "时间", "链接", "正文"])
        writer.writeheader()
        for i, news in enumerate(news_list, 1):
            writer.writerow({
                "序号": i,
                "标题": news["title"],
                "时间": news["time"],
                "链接": news["link"],
                "正文": news["content"]
            })


# ---------------------- 获取正文 ----------------------
def get_content(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        content_div = soup.find("div", class_="content_area") or soup.find("div", class_="article-body")
        if not content_div:
            return ""
        paragraphs = content_div.find_all("p")
        return "\n".join(p.get_text(strip=True) for p in paragraphs)[:1200]
    except:
        return "获取正文失败"


# ---------------------- 爬取多页 ----------------------
def crawl():
    init_db()
    all_news = []
    new_count = 0

    print("开始爬取央视国际新闻...")
    for page in range(1, MAX_PAGE + 1):
        url = f"https://news.cctv.com/world/index_{page}.shtml" if page > 1 else "https://news.cctv.com/world/"
        print(f"第 {page} 页：{url}")

        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")

            # 第1页：爬取所有新闻
            # 第2、3页：只爬取"列表浏览"的前2个链接
            if page == 1:
                items = soup.find_all("div", class_="title-box")
                print(f"  模式：爬取全部新闻")
            else:
                # 查找"列表浏览"区域
                list_section = soup.find("div", class_="list") or soup.find("div", class_="mod_list") or soup
                items = list_section.find_all("a", href=True)[:2]  # 只取前2个链接
                print(f"  模式：爬取列表浏览前2个链接")

            for idx, item in enumerate(items, 1):
                try:
                    # 处理不同类型的item（第1页是div，第2/3页可能是a标签）
                    if page == 1:
                        a = item.find("a")
                        if not a:
                            continue
                        title = a.get_text(strip=True)
                        link = a["href"]

                        time_tag = item.find_next_sibling("div", class_="date")
                        news_time = time_tag.get_text(strip=True) if time_tag else "无时间"
                    else:
                        # 第2/3页：item本身就是a标签
                        a = item
                        title = a.get_text(strip=True)
                        link = a["href"]
                        news_time = "无时间"  # 列表浏览可能没有时间标签

                    if not link.startswith("http"):
                        link = "https://news.cctv.com" + link

                    if len(title) < 4 or is_duplicate(link):
                        continue

                    print(f"  [{idx}] 正在获取: {title[:40]}...")
                    content = get_content(link)
                    news = {
                        "title": title,
                        "time": news_time,
                        "link": link,
                        "content": content
                    }
                    if insert_news(news):
                        new_count += 1
                    all_news.append(news)
                    time.sleep(0.8)
                except Exception as e:
                    print(f"    处理失败: {e}")
                    continue
        except Exception as e:
            print(f"页{page}出错：{e}")
        time.sleep(1)

    save_csv(all_news)
    print(f"✅ 本次新增新闻：{new_count} 条")
    print(f"✅ 已保存到 {SAVE_CSV} 和 {DB_FILE}")


# ---------------------- 定时任务 ----------------------
def run_schedule():
    print("=" * 60)
    print("定时爬虫已启动：每天 08:00 自动爬取央视国际新闻")
    print("按 Ctrl + C 停止")
    print("=" * 60)
    schedule.every().day.at("08:00").do(crawl)
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n⏹️  定时任务已停止")


# ====================== 启动 ======================
if __name__ == "__main__":
    import sys

    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--schedule":
        # 启动定时模式
        crawl()  # 先爬一次
        run_schedule()  # 再启动定时
    else:
        # 仅单次爬取模式(默认)
        print("提示: 使用 --schedule 参数可启动定时任务")
        print("例如: python cctv_news_crawler.py --schedule\n")
        crawl()  # 只爬一次