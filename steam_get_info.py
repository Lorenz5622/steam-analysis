import requests
from bs4 import BeautifulSoup
import re
import os
import pandas as pd


game_links_path = 'test.csv'
game_info_path = 'game_info.csv'


proxies = { "http": None, "https": None}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-cn,zh;q=0.9,en;q=0.8,en-gb;q=0.7,en-us;q=0.6',
    'cache-control': 'max-age=0',
    'connection': 'keep-alive',
    'host': 'store.steampowered.com',
    'referer': 'https://store.steampowered.com/',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'Cookie': 'birthtime=1070208001',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'mozilla/5.0 (windows nt 10.0; win64; x64) applewebkit/537.36 (khtml, like gecko) chrome/119.0.0.0 safari/537.36 edg/119.0.0.0',

    'sec-ch-ua-platform': "windows"
}

def gamename(soup):   #游戏名字
    try:
        a = soup.find(class_="apphub_AppName")
        game_name = str(a.string)
    except:
        a = soup.find(class_="apphub_AppName")
        game_name  = str(a.text)
    return game_name    

def clean_price(price):
    try:
        price_cleaned = float(price.replace('¥',''))
    except:
        price_cleaned = 0
    return price_cleaned

def gameprice(soup):#价格
    try:
        a = soup.find_all(class_="discount_original_price")
        for i in a:
            if re.search('¥|free|免费', str(i),re.IGNORECASE):
                a = i
        price = str(a.string).replace('	', '').replace('\n', '').replace('\r', '').replace(' ', '')
    except:
        try:
            a = soup.find_all(class_="game_purchase_price price")
            for i in a:
                if re.search('¥|free|免费', str(i),re.IGNORECASE):
                    a = i
            price = str(a.string).replace('	', '').replace('\n', '').replace('\r', '').replace(' ', '')
        except:
            price = 0

    price_cleaned = clean_price(price)
    return price_cleaned

def taglist(soup):#标签列表
    list1=[]
    a = soup.find_all(class_="app_tag")
    for i in a:
        k = str(i.string).replace('	', '').replace('\n', '').replace('\r', '')
        if k == '+':
            pass
        else:
            list1.append(k)
    list1 = str('\n'.join(list1))
    return list1

def description(soup):  #游戏描述
    a = soup.find(class_="game_description_snippet")
    k = str(a.string).replace('	', '').replace('\n', '').replace('\r', '')
    return k


# 获取近期与总体评价、好评率 
def review_all(soup):

    # 定位到user_reviews区域
    user_reviews_section = soup.find('div', {'id': 'userReviews'})

    # 提取近期评价
    recent_review_row = user_reviews_section.find('div', {'class': 'user_reviews_summary_row'})
    recent_evaluation = recent_review_row.find('span', {'class': 'game_review_summary'}).text.strip()
    recent_count = int(recent_review_row.select_one('.responsive_hidden').text.replace("(", "").replace(")", "").replace(",", ""))  # 去除逗号并转为整数
    recent_positive_percentage = recent_review_row.find('span', {'class': 'nonresponsive_hidden responsive_reviewdesc'}).text.split(' ')[-2].replace('%', '')

    # 提取总体评价
    overall_review_row = user_reviews_section.find('div', {'class': 'user_reviews_summary_row', 'itemprop': 'aggregateRating'})
    overall_evaluation = overall_review_row.find('span', {'class': 'game_review_summary'}).text.strip()
    overall_count = int(overall_review_row.select_one('.responsive_hidden').text.replace("(", "").replace(")", "").replace(",", ""))
    overall_positive_percentage = overall_review_row.find('span', {'class': 'nonresponsive_hidden responsive_reviewdesc'}).text.split(' ')[-2].replace('%','')
    
    return (recent_evaluation,
        recent_count,
        float(recent_positive_percentage),
        overall_evaluation,
        overall_count,
        float(overall_positive_percentage)
    )

def getdate(soup):   #发行日期
    a = soup.find(class_="date")
    k = str(a.string)
    return k

def developer(soup):   #开发商
    a = soup.find(id="developers_list")
    k = str(a.a.string)
    return k

def getreviews(ID):#获取评论
    r1 = requests.get(
        'https://store.steampowered.com/appreviews/%s?cursor=*&day_range=30&start_date=-1&end_date=-1&date_range_type=all&filter=summary&language=schinese&l=schinese&review_type=all&purchase_type=all&playtime_filter_min=0&playtime_filter_max=0&filter_offtopic_activity=1'%str(ID), proxies=proxies, headers=headers,timeout=10)
    soup = BeautifulSoup(r1.json()['html'], 'lxml')
    a = soup.findAll(class_="content")
    list1 = []
    for i in a:
        list1.append(i.text.replace('	', '').replace('\n', '').replace('\r', '').replace(' ', ','))
    k=str('\n'.join(list1))
    return k

def get_peak(ID):
    link = 'https://steamcharts.com/app/'+str(ID)

    headers_steamcharts = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cache-Control': 'max-age=0',
        'Cookie': 'dnsDisplayed=undefined; ccpaApplies=false; signedLspa=undefined; _sp_su=false; idw-fe-id=2b382a1e-4113-4039-96e8-5ba7bd0a4c27; ccpaUUID=77fbbc90-83d2-48c5-9397-e7a0d61efa67; _pbjs_userid_consent_data=6683316680106290; _sharedid=4c1bfa4e-a0e4-4c98-8042-e913281b2134; _gid=GA1.2.2065889914.1712652779; _ga=GA1.2.573694605.1712559411; _ga_QE2L64H640=GS1.2.1712737796.3.1.1712737983.0.0.0; _ga_0CPE0JFSCT=GS1.1.1712737795.3.1.1712737987.0.0.0',
        'If-Modified-Since': 'Wed, 10 Apr 2024 08:39:30 GMT',
        'Sec-Ch-Ua': '"Microsoft Edge";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    }

    try:
        r = requests.get(link, proxies=proxies, headers=headers_steamcharts, timeout=2)
        soup = BeautifulSoup(r.text, 'lxml')
        soup = soup.find('div', id='app-heading')
        peak_span = soup.find_all('span', class_='num')
        all_time_peak_num = peak_span[2].text
        all_time_peak_num = int(all_time_peak_num.replace(',', ''))

        return all_time_peak_num 
    except:
        print('获取peak信息失败')
        return 0

def getdetail(Link, ID):
    tag, des,  date, dev, review,name,price,peak = ' ', ' ', ' ', ' ', ' ',' ',' ',' '
    recent_evaluation, recent_count, recent_positive_percentage, overall_evaluation, overall_count, overall_positive_percentage = ' ',' ',' ',' ',' ',' '
    new_row_dict = {
            'Link':'',
            'ID': '',
            'name': '',
            'tag': '',
            'description': '',
            'date': '',
            'developer': '',
            'price': '',
            #review_all
            'Recent_Description':'',
            'Recent_Count':'',   
            'Recent_Percentage':'',
            'Overall_Description':'',
            'Overall_Count':'',
            'Overall_Percentage':'',
            'peak': '',

            # 'review': ''
        }
    
    try:
        r = requests.get(Link, proxies=proxies,headers=headers,timeout=2)
        print('响应成功')
    except:
        print('服务器无响应1')
        try:
            r = requests.get(Link, proxies=proxies, headers=headers,timeout=3)
        except:
            print('服务器无响应2')
            try:
                r = requests.get(Link, proxies=proxies, headers=headers,timeout=5)
            except:
                print('服务器无响应3')

    try:
        soup = BeautifulSoup(r.text, 'lxml')
        name = gamename(soup)
        tag = taglist(soup)
        des = description(soup)
        # reviews = reviewsummary(soup)
        date = getdate(soup)
        # rate = userreviewsrate(soup)
        dev = developer(soup)
        # review = getreviews(str(ID))
        price = gameprice(soup)
        recent_evaluation, recent_count, recent_positive_percentage, overall_evaluation, overall_count, overall_positive_percentage = review_all(soup)
        peak = get_peak(ID)

        new_row_dict = {
            'Link': Link,
            'ID': ID,
            'name': name,
            'tag': tag,
            'description': des,
            'date': date,
            'developer': dev,
            'price': price,
            #review_all
            'Recent_Description': recent_evaluation,
            'Recent_Count':  recent_count,   
            'Recent_Percentage': recent_positive_percentage,
            'Overall_Description': overall_evaluation,
            'Overall_Count': overall_count,
            'Overall_Percentage': overall_positive_percentage,
            'peak': peak,

            # 'review':review
        }

        print('已完成: '+name+str(ID))
        getError = False

    except:
        print('未完成:  '+str(ID))
        price = 'error'
        getError = True

    return new_row_dict, getError


if __name__ == "__main__":
    game_links = pd.read_csv(game_links_path)
    count = 1

    column_names = [
    'Link',
    'ID',
    'name',
    'tag',
    'description',
    'date',
    'developer',
    'price',
    'Recent_Description',
    'Recent_Count',
    'Recent_Percentage',
    'Overall_Description',
    'Overall_Count',
    'Overall_Percentage',
    'review',
    'peak'
]
    game_info = pd.DataFrame(columns=column_names)
    if not os.path.exists(game_info_path):
        game_info.to_csv(game_info_path, index=False)

    error_count = 0
    for index,row in game_links.iterrows():
        link = row['Link']
        ID = row['ID']
        digged = row['digged']
        if digged == True:
            continue

        new_row_dict, getError = getdetail(link, ID)
        print("第%d个"%count)
        count += 1
        # 将新的行插入df的末尾
        if getError == False :
            new_row_df = pd.DataFrame([new_row_dict])
            # 直接写入.csv
            game_info = pd.concat([game_info,new_row_df], ignore_index=True)
            new_row_df.to_csv(game_info_path, mode='a', header=False, index=False)
            # 标记已挖掘
            game_links.at[index, 'digged'] = True
            # 写入标记
            game_links.to_csv(game_links_path, index=False)
            error_count = 0
        else :
            error_count += 1
            if error_count >= 5 :
                print('已连续错误多次，退出程序')
                break 
            
    # 写入数据
    # if not os.path.exists(game_info_path):
    #     game_info.to_csv(game_info_path, index=False)
    # else:
    #     game_info.to_csv(game_info_path, mode='a', header=False, index=False)   

    # game_links.to_csv(game_links_path, index=False)
    # print('已保存数据')
