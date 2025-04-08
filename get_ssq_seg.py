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


def frequency_analysis(results: List[Dict], top_n: int = 10):
    """
    统计号码出现频率
    :param results: 历史开奖结果列表
    :param top_n: 返回前N个高频号码
    :return: 排序后的频率字典
    """
    red_counts = {}
    blue_counts = {}

    for result in results:
        # 统计红球
        for red in result['red'].split(','):
            red_counts[red] = red_counts.get(red, 0) + 1
        # 统计蓝球
        blue = result['blue']
        blue_counts[blue] = blue_counts.get(blue, 0) + 1

    # 按频率排序
    sorted_red = sorted(red_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    sorted_blue = sorted(blue_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return {
        'red': dict(sorted_red),
        'blue': dict(sorted_blue)
    }


def cold_hot_analysis(results: List[Dict], recent_n: int = 30):
    """
    冷热号分析(最近N期)
    :param results: 历史开奖结果
    :param recent_n: 分析的最近期数
    :return: 冷热号字典
    """
    recent_results = results[:recent_n]
    return frequency_analysis(recent_results)


def omission_analysis(results: List[Dict]) -> Dict[str, Dict[str, int]]:
    """
    完善后的遗漏值分析(分别统计红球和蓝球)
    :param results: 历史开奖结果列表
    :return: 包含红球和蓝球遗漏值的字典
    """
    # 初始化所有红球(01-33)和蓝球(01-16)
    red_omission = {str(i).zfill(2): 0 for i in range(1, 34)}
    blue_omission = {str(i).zfill(2): 0 for i in range(1, 17)}

    for result in results:
        current_reds = set(result['red'].split(','))
        current_blue = result['blue']

        # 更新红球遗漏值
        for red in red_omission:
            if red in current_reds:
                red_omission[red] = 0  # 本期出现的红球重置为0
            else:
                red_omission[red] += 1  # 未出现的红球遗漏值+1

        # 更新蓝球遗漏值
        for blue in blue_omission:
            if blue == current_blue:
                blue_omission[blue] = 0  # 本期出现的蓝球重置为0
            else:
                blue_omission[blue] += 1  # 未出现的蓝球遗漏值+1

    return {
        'red': red_omission,
        'blue': blue_omission
    }


def zone_distribution(results: List[Dict]):
    """
    红球区间分布分析
    将33个红球分为3个区间(1-11,12-22,23-33)
    :param results: 历史开奖结果
    :return: 各区间的出现频率
    """
    zone_counts = {'1-11': 0, '12-22': 0, '23-33': 0}

    for result in results:
        reds = [int(red) for red in result['red'].split(',')]
        for red in reds:
            if 1 <= red <= 11:
                zone_counts['1-11'] += 1
            elif 12 <= red <= 22:
                zone_counts['12-22'] += 1
            else:
                zone_counts['23-33'] += 1

    total = sum(zone_counts.values())
    return {zone: count / total for zone, count in zone_counts.items()}


def odd_even_ratio(results: List[Dict]):
    """
    红球奇偶比例分析
    :param results: 历史开奖结果
    :return: 奇数和偶数的比例
    """
    odd = 0
    even = 0

    for result in results:
        reds = [int(red) for red in result['red'].split(',')]
        for red in reds:
            if red % 2 == 1:
                odd += 1
            else:
                even += 1

    total = odd + even
    return {'奇数': odd / total, '偶数': even / total}


def big_small_analysis(results: List[Dict]):
    """
    红球大小号分析(以17为分界线)
    :param results: 历史开奖结果
    :return: 大号和小号的比例
    """
    big = 0
    small = 0

    for result in results:
        reds = [int(red) for red in result['red'].split(',')]
        for red in reds:
            if red >= 17:
                big += 1
            else:
                small += 1

    total = big + small
    return {'大号': big / total, '小号': small / total}

if __name__ == '__main__':
    # 示例1：获取最近30天的结果
    # get_ssq_result(days=30)

    # 示例2：获取最近50期结果
    # get_ssq_result(days=365,issue_count=20)

    if __name__ == '__main__':
        # 获取历史数据
        history = get_ssq_result(issue_count=100)

        # 频率分析
        freq = frequency_analysis(history)
        print("高频红球:", freq['red'])
        print("高频蓝球:", freq['blue'])

        # 冷热号分析
        hot = cold_hot_analysis(history)
        print("近期红球热号:", hot['red'])
        print("近期蓝球热号:", hot['blue'])

        # 遗漏值分析
        if history:
            # 遗漏值分析
            omission = omission_analysis(history)

            print("\n红球遗漏情况:")
            for num, count in sorted(omission['red'].items(), key=lambda x: int(x[0])):
                print(f"红球 {num}: {count}期未出")

            print("\n蓝球遗漏情况:")
            for num, count in sorted(omission['blue'].items(), key=lambda x: int(x[0])):
                print(f"蓝球 {num}: {count}期未出")

            # 找出遗漏最大的号码
            max_red = max(omission['red'].items(), key=lambda x: x[1])
            max_blue = max(omission['blue'].items(), key=lambda x: x[1])
            print(f"\n最大遗漏红球: {max_red[0]} (已{max_red[1]}期未出)")
            print(f"最大遗漏蓝球: {max_blue[0]} (已{max_blue[1]}期未出)")

            if history:
                # 区间分布分析
                zones = zone_distribution(history)
                print("\n红球区间分布:")
                for zone, ratio in zones.items():
                    print(f"{zone}区: {ratio:.1%}")

                # 奇偶比例分析
                oe_ratio = odd_even_ratio(history)
                print("\n红球奇偶比例:")
                print(f"奇数: {oe_ratio['奇数']:.1%}")
                print(f"偶数: {oe_ratio['偶数']:.1%}")

                # 大小号分析
                bs_ratio = big_small_analysis(history)
                print("\n红球大小比例(以17为界):")
                print(f"大号: {bs_ratio['大号']:.1%}")
                print(f"小号: {bs_ratio['小号']:.1%}")