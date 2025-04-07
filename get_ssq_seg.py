import requests
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict


def get_ssq_result(days: int = 30, issue_count: int = None) -> Optional[List[Dict]]:
    """
    获取双色球开奖结果
    :param days: 获取最近多少天的结果，默认30天
    :param issue_count: 获取最近多少期结果，优先级高于days
    :return: 开奖结果列表
    """
    url = 'https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice'
    params = {'name': 'ssq'}

    if issue_count:
        params['issueCount'] = str(issue_count)
    else:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        params.update({
            'dayStart': start_date,
            'dayEnd': end_date
        })

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data['state'] != 0 or not data['result']:
            print("未获取到开奖数据")
            return None

        results = []
        for result in data['result']:
            print(f"双色球第{result['code']}期开奖结果：")
            print(f"开奖日期: {result['date']}")
            print(f"红球: {', '.join(result['red'].split(','))}")  # 优化红球显示
            print(f"蓝球: {result['blue']}")
            print(f"奖池: {result['poolmoney']}")
            print("-" * 30)
            results.append(result)

        return results

    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
    except json.JSONDecodeError:
        print("解析JSON数据失败")
    except Exception as e:
        print(f"获取开奖结果出错: {e}")
    return None


if __name__ == '__main__':
    # 示例1：获取最近30天的结果
    # get_ssq_result(days=30)

    # 示例2：获取最近50期结果
    get_ssq_result(days=365,issue_count=20)