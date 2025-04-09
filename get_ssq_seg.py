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
    完善后的区间分布分析(包含红球和蓝球)
    红球分3个区间(1-11,12-22,23-33)
    蓝球分2个区间(1-8,9-16)
    """
    red_zones = {'1-11': 0, '12-22': 0, '23-33': 0}
    blue_zones = {'1-8': 0, '9-16': 0}

    for result in results:
        # 红球区间统计
        reds = [int(red) for red in result['red'].split(',')]
        for red in reds:
            if 1 <= red <= 11:
                red_zones['1-11'] += 1
            elif 12 <= red <= 22:
                red_zones['12-22'] += 1
            else:
                red_zones['23-33'] += 1

        # 蓝球区间统计
        blue = int(result['blue'])
        if 1 <= blue <= 8:
            blue_zones['1-8'] += 1
        else:
            blue_zones['9-16'] += 1

    red_total = sum(red_zones.values())
    blue_total = sum(blue_zones.values())

    return {
        'red': {zone: count / red_total for zone, count in red_zones.items()},
        'blue': {zone: count / blue_total for zone, count in blue_zones.items()}
    }


def odd_even_ratio(results: List[Dict]):
    """
    完善后的奇偶比例分析(包含红球和蓝球)
    """
    red_odd = red_even = 0
    blue_odd = blue_even = 0

    for result in results:
        # 红球奇偶统计
        reds = [int(red) for red in result['red'].split(',')]
        for red in reds:
            if red % 2 == 1:
                red_odd += 1
            else:
                red_even += 1

        # 蓝球奇偶统计
        blue = int(result['blue'])
        if blue % 2 == 1:
            blue_odd += 1
        else:
            blue_even += 1

    red_total = red_odd + red_even
    blue_total = blue_odd + blue_even

    return {
        'red': {'奇数': red_odd / red_total, '偶数': red_even / red_total},
        'blue': {'奇数': blue_odd / blue_total, '偶数': blue_even / blue_total}
    }


def big_small_analysis(results: List[Dict]):
    """
    完善后的大小号分析(包含红球和蓝球)
    红球以17为分界线(1-16为小号,17-33为大号)
    蓝球以9为分界线(1-8为小号,9-16为大号)
    """
    red_big = red_small = 0
    blue_big = blue_small = 0

    for result in results:
        # 红球大小统计
        reds = [int(red) for red in result['red'].split(',')]
        for red in reds:
            if red >= 17:
                red_big += 1
            else:
                red_small += 1

        # 蓝球大小统计
        blue = int(result['blue'])
        if blue >= 9:
            blue_big += 1
        else:
            blue_small += 1

    red_total = red_big + red_small
    blue_total = blue_big + blue_small

    return {
        'red': {'大号': red_big / red_total, '小号': red_small / red_total},
        'blue': {'大号': blue_big / blue_total, '小号': blue_small / blue_total}
    }

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
                for zone, ratio in zones['red'].items():
                    print(f"{zone}区: {ratio:.1%}")
                print("\n蓝球区间分布:")
                for zone, ratio in zones['blue'].items():
                    print(f"{zone}区: {ratio:.1%}")

                # 奇偶比例分析
                oe_ratio = odd_even_ratio(history)
                print("\n红球奇偶比例:")
                print(f"奇数: {oe_ratio['red']['奇数']:.1%}")
                print(f"偶数: {oe_ratio['red']['偶数']:.1%}")
                print("\n蓝球奇偶比例:")
                print(f"奇数: {oe_ratio['blue']['奇数']:.1%}")
                print(f"偶数: {oe_ratio['blue']['偶数']:.1%}")

                # 大小号分析
                bs_ratio = big_small_analysis(history)
                print("\n红球大小比例(以17为界):")
                print(f"大号: {bs_ratio['red']['大号']:.1%}")
                print(f"小号: {bs_ratio['red']['小号']:.1%}")
                print("\n蓝球大小比例(以9为界):")
                print(f"大号: {bs_ratio['blue']['大号']:.1%}")
                print(f"小号: {bs_ratio['blue']['小号']:.1%}")