from random import sample, choice
import requests
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple

# 常量定义
API_URL = 'https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice'
DEFAULT_DAYS = 365
TIMEOUT = 10
RED_BALL_RANGE = (1, 34)
BLUE_BALL_RANGE = (1, 17)


class LotteryAnalyzer:
    """双色球数据分析器"""

    @staticmethod
    def fetch_data(params: Dict) -> Optional[Dict]:
        """获取API数据"""
        try:
            response = requests.get(API_URL, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求出错: {e}")
            return None

    @staticmethod
    def get_results(days: int = DEFAULT_DAYS, issue_count: int = None) -> Optional[List[Dict]]:
        """获取开奖结果"""
        params = {'name': 'ssq'}
        if issue_count:
            params['issueCount'] = str(issue_count)
        else:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            params.update({'dayStart': start_date, 'dayEnd': end_date})

        data = LotteryAnalyzer.fetch_data(params)
        if not data or data['state'] != 0 or not data['result']:
            print("未获取到开奖数据")
            return None

        #print(data['result'][1:] )
        #return data['result'][1:] if len(data['result']) > 1 else []

        return data['result']

    @staticmethod
    def format_result(result: Dict) -> Dict:
        """格式化单期结果"""
        return {
            '期号': result['code'],
            '日期': result['date'],
            '红球': [int(ball) for ball in result['red'].split(',')],
            '蓝球': int(result['blue']),
            '奖池': result['poolmoney']
        }

    @staticmethod
    def analyze_frequency(results: List[Dict], top_n: int = 10) -> Dict[str, Dict[int, int]]:
        """频率分析"""
        red_counts = {ball: 0 for ball in range(*RED_BALL_RANGE)}
        blue_counts = {ball: 0 for ball in range(*BLUE_BALL_RANGE)}

        for result in results:
            for ball in result['红球']:
                red_counts[ball] += 1
            blue_counts[result['蓝球']] += 1

        sorted_red = sorted(red_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        sorted_blue = sorted(blue_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

        return {
            '红球': dict(sorted_red),
            '蓝球': dict(sorted_blue)
        }

    @staticmethod
    def analyze_omission(results: List[Dict]) -> Dict[str, Dict[int, int]]:
        """遗漏值分析"""
        red_omission = {ball: 0 for ball in range(*RED_BALL_RANGE)}
        blue_omission = {ball: 0 for ball in range(*BLUE_BALL_RANGE)}

        for result in results:
            # 更新红球遗漏
            for ball in red_omission:
                red_omission[ball] = 0 if ball in result['红球'] else red_omission[ball] + 1
            # 更新蓝球遗漏
            for ball in blue_omission:
                blue_omission[ball] = 0 if ball == result['蓝球'] else blue_omission[ball] + 1

        return {
            '红球': red_omission,
            '蓝球': blue_omission
        }

    @staticmethod
    def analyze_distribution(results: List[Dict]) -> Dict[str, Dict[str, float]]:
        """区间分布分析"""
        red_zones = {
            '1-11': 0,
            '12-22': 0,
            '23-33': 0
        }
        blue_zones = {
            '1-8': 0,
            '9-16': 0
        }

        for result in results:
            # 红球区间
            for ball in result['红球']:
                if 1 <= ball <= 11:
                    red_zones['1-11'] += 1
                elif 12 <= ball <= 22:
                    red_zones['12-22'] += 1
                else:
                    red_zones['23-33'] += 1
            # 蓝球区间
            ball = result['蓝球']
            blue_zones['1-8' if ball <= 8 else '9-16'] += 1

        return {
            '红球': {zone: count / sum(red_zones.values()) for zone, count in red_zones.items()},
            '蓝球': {zone: count / sum(blue_zones.values()) for zone, count in blue_zones.items()}
        }

    @staticmethod
    def analyze_ratio(results: List[Dict]) -> Dict[str, Dict[str, float]]:
        """奇偶和大小比例分析"""
        stats = {
            '红球': {'奇数': 0, '偶数': 0, '大号': 0, '小号': 0},
            '蓝球': {'奇数': 0, '偶数': 0, '大号': 0, '小号': 0}
        }

        for result in results:
            # 红球统计
            for ball in result['红球']:
                stats['红球']['奇数' if ball % 2 else '偶数'] += 1
                stats['红球']['大号' if ball >= 17 else '小号'] += 1
            # 蓝球统计
            ball = result['蓝球']
            stats['蓝球']['奇数' if ball % 2 else '偶数'] += 1
            stats['蓝球']['大号' if ball >= 9 else '小号'] += 1

        # 计算比例
        for ball_type in stats:
            total = sum(stats[ball_type].values()) / 2  # 因为统计了两个维度
            for key in stats[ball_type]:
                stats[ball_type][key] /= total

        return stats

    @staticmethod
    def predict_next_result(results: List[Dict]) -> Dict[str, List[int]]:
        """综合预测下期结果（学术研究用）"""
        if not results or len(results) < 30:
            raise ValueError("需要至少30期数据进行分析")

        # 获取各项分析结果
        freq = LotteryAnalyzer.analyze_frequency(results)
        omission = LotteryAnalyzer.analyze_omission(results)
        ratios = LotteryAnalyzer.analyze_ratio(results)
        zones = LotteryAnalyzer.analyze_distribution(results)

        # 红球预测逻辑
        red_candidates = []

        # 1. 考虑高频号码（权重40%）
        top_red = list(freq['红球'].keys())[:15]
        red_candidates.extend(top_red)

        # 2. 考虑大遗漏号码（权重30%）
        sorted_omission = sorted(omission['红球'].items(), key=lambda x: x[1], reverse=True)
        red_candidates.extend([x[0] for x in sorted_omission[:10]])

        # 3. 考虑区间分布（权重20%）
        max_zone = max(zones['红球'].items(), key=lambda x: x[1])[0]
        start, end = map(int, max_zone.split('-'))
        red_candidates.extend([x for x in range(start, end + 1) if x in freq['红球']])

        # 4. 考虑奇偶比例
        odd_even = '奇数' if ratios['红球']['奇数'] > 0.5 else '偶数'
        red_candidates.extend([x for x in range(1, 34) if x % 2 == (1 if odd_even == '奇数' else 0)])

        # 蓝球预测逻辑
        blue_candidates = []

        # 1. 高频蓝球（权重50%）
        blue_candidates.extend(list(freq['蓝球'].keys())[:5])

        # 2. 大遗漏蓝球（权重30%）
        sorted_blue_omission = sorted(omission['蓝球'].items(), key=lambda x: x[1], reverse=True)
        blue_candidates.extend([x[0] for x in sorted_blue_omission[:3]])

        # 3. 奇偶选择
        blue_odd_even = '奇数' if ratios['蓝球']['奇数'] > 0.5 else '偶数'
        blue_candidates.extend([x for x in range(1, 17) if x % 2 == (1 if blue_odd_even == '奇数' else 0)])

        # 去重并排序
        red_candidates = sorted(list(set(red_candidates)))
        blue_candidates = sorted(list(set(blue_candidates)))

        # 计算每个号码的综合得分
        red_scores = {ball: 0 for ball in red_candidates}
        blue_scores = {ball: 0 for ball in blue_candidates}

        # 红球评分
        for ball in red_candidates:
            # 频率得分
            red_scores[ball] += freq['红球'].get(ball, 0) * 0.4
            # 遗漏得分
            red_scores[ball] += (1 / (omission['红球'].get(ball, 0) + 1)) * 0.3
            # 区间得分
            zone_score = 0
            if 1 <= ball <= 11:
                zone_score = zones['红球']['1-11']
            elif 12 <= ball <= 22:
                zone_score = zones['红球']['12-22']
            else:
                zone_score = zones['红球']['23-33']
            red_scores[ball] += zone_score * 0.2
            # 奇偶得分
            if (ball % 2 == 1 and ratios['红球']['奇数'] > 0.5) or (ball % 2 == 0 and ratios['红球']['偶数'] > 0.5):
                red_scores[ball] += 0.1

        # 蓝球评分
        for ball in blue_candidates:
            # 频率得分
            blue_scores[ball] += freq['蓝球'].get(ball, 0) * 0.5
            # 遗漏得分
            blue_scores[ball] += (1 / (omission['蓝球'].get(ball, 0) + 1)) * 0.3
            # 区间得分
            zone_score = zones['蓝球']['1-8'] if ball <= 8 else zones['蓝球']['9-16']
            blue_scores[ball] += zone_score * 0.2

        # 选择得分最高的6个红球和1个蓝球
        top_red_balls = sorted(red_scores.items(), key=lambda x: x[1], reverse=True)[:6]
        top_blue_ball = sorted(blue_scores.items(), key=lambda x: x[1], reverse=True)[0]

        return {
            '红球候选': red_candidates,
            '蓝球候选': blue_candidates,
            '建议组合': {
                '红球': sorted([ball[0] for ball in top_red_balls]),
                '蓝球': top_blue_ball[0]
            },
            '得分详情': {
                '红球得分': red_scores,
                '蓝球得分': blue_scores
            }
        }

def main():
    """主程序"""
    # 获取数据
    raw_results = LotteryAnalyzer.get_results(issue_count=101)
    if not raw_results:
        return

    results = [LotteryAnalyzer.format_result(r) for r in raw_results]

    # 执行各项分析
    print("\n=== 频率分析 ===")
    freq = LotteryAnalyzer.analyze_frequency(results)
    print("高频红球:", freq['红球'])
    print("高频蓝球:", freq['蓝球'])

    print("\n=== 遗漏分析 ===")
    omission = LotteryAnalyzer.analyze_omission(results)
    max_red = max(omission['红球'].items(), key=lambda x: x[1])
    max_blue = max(omission['蓝球'].items(), key=lambda x: x[1])
    print(f"最大遗漏红球: {max_red[0]} (已{max_red[1]}期未出)")
    print(f"最大遗漏蓝球: {max_blue[0]} (已{max_blue[1]}期未出)")

    print("\n=== 区间分布 ===")
    zones = LotteryAnalyzer.analyze_distribution(results)
    for ball_type in zones:
        print(f"{ball_type}分布:")
        for zone, ratio in zones[ball_type].items():
            print(f"  {zone}: {ratio:.1%}")

    print("\n=== 比例分析 ===")
    ratios = LotteryAnalyzer.analyze_ratio(results)
    for ball_type in ratios:
        print(f"{ball_type}比例:")
        print(f"  奇偶: 奇数{ratios[ball_type]['奇数']:.1%} 偶数{ratios[ball_type]['偶数']:.1%}")
        print(f"  大小: 大号{ratios[ball_type]['大号']:.1%} 小号{ratios[ball_type]['小号']:.1%}")

    print("\n=== 预测分析 ===")
    try:
        prediction = LotteryAnalyzer.predict_next_result(results)
        print("红球候选号码:", prediction['红球候选'])
        print("蓝球候选号码:", prediction['蓝球候选'])
        print("建议组合（概率最高）:", prediction['建议组合'])
        # 可以添加得分详情输出
        print("\n得分详情:")
        print("红球得分:", {k: round(v, 2) for k, v in prediction['得分详情']['红球得分'].items()})
        print("蓝球得分:", {k: round(v, 2) for k, v in prediction['得分详情']['蓝球得分'].items()})
    except ValueError as e:
        print(f"预测失败: {e}")

if __name__ == '__main__':
    main()