import requests
from bs4 import BeautifulSoup




def get_ssq_result():
    # 使用中国福彩网API获取最新开奖结果
    url = 'https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice'
    params = {
        'name': 'ssq',
        'issueCount': '10'  # 获取最新一期
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data['state'] == 0 and data['result']:
            for result in data['result']:
                print(f"双色球第{result['code']}期开奖结果：")
                print(f"开奖日期: {result['date']}")
                print(f"红球: {result['red']}")
                print(f"蓝球: {result['blue']}")
                print(f"奖池: {result['poolmoney']}")
                print("-" * 30)  # 分隔线
            return data['result']
        else:
            print("未获取到开奖数据")
            return None

    except Exception as e:
        print(f"获取开奖结果出错: {e}")
        return None


if __name__ == '__main__':
    get_ssq_result()