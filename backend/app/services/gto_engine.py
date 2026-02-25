"""
GTO (Game Theory Optimal) 翻前策略引擎
基于 Monker Solver 和 PioSolver 的近似 GTO 策略
支持 6max 50bb 和 100bb
"""

from typing import Dict, List, Optional, Tuple
import random


# 扑克牌定义
SUITS = ['s', 'h', 'd', 'c']  # 黑桃、红桃、方块、梅花
RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']

# 生成所有起手牌组合
def generate_all_hands() -> List[str]:
    hands = []
    for i, r1 in enumerate(RANKS):
        for j, r2 in enumerate(RANKS):
            if i == j:
                hands.append(f"{r1}{r2}")  # 对子
            elif i < j:
                hands.append(f"{r1}{r2}s")  # 同花
            else:
                hands.append(f"{r2}{r1}o")  # 不同花
    return hands

ALL_HANDS = generate_all_hands()

# 手牌强度分类
def get_hand_type(hand: str) -> str:
    """分类手牌类型"""
    if len(hand) == 2:
        return "pair"
    elif hand.endswith('s'):
        return "suited"
    else:
        return "offsuit"


def get_hand_rank(hand: str) -> int:
    """获取手牌强度等级 (1-169, 1是AA最强)"""
    hand_type = get_hand_type(hand)
    r1, r2 = hand[0], hand[1]
    idx1 = RANKS.index(r1)
    idx2 = RANKS.index(r2)
    
    if hand_type == "pair":
        # 对子: AA=1, KK=2, ... 22=13
        return idx1 + 1
    else:
        # 非对子
        base = 13
        if hand_type == "suited":
            # 同花比不同花强
            base = 13 + (12 * 13)  # 对子 + 同花部分
            pair_idx = min(idx1, idx2) * 13 + max(idx1, idx2)
            return base + pair_idx
        else:
            # 不同花
            base = 13 + (12 * 13) + (12 * 13)  # 对子 + 同花 + 不同花
            pair_idx = min(idx1, idx2) * 13 + max(idx1, idx2)
            return base + pair_idx


# ==================== GTO 策略数据 ====================

class GTOStrategy:
    """
    6max GTO 近似策略
    基于标准 GTO 解决方案的简化版本
    """
    
    POSITIONS = ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB']
    
    # 位置相对于 BTN 的顺序 (用于判断谁在行动)
    POSITION_ORDER = {'BTN': 0, 'CO': 1, 'MP': 2, 'UTG': 3, 'BB': 4, 'SB': 5}
    
    # 行动类型
    ACTIONS_TO_YOU = {
        'open': '所有人都弃牌到你',
        'vs_limp': '前面有人溜入 (Limp)',
        'vs_raise_2bb': '前面有人加注到 2BB',
        'vs_raise_2.5bb': '前面有人加注到 2.5BB',
        'vs_raise_3bb': '前面有人加注到 3BB',
        'vs_raise_4bb': '前面有人加注到 4BB',
        'vs_3bet': '前面有人 3bet',
        'vs_all_in': '前面有人 All-in',
    }
    
    def __init__(self, stack_size: int = 100):
        self.stack_size = stack_size
        self._load_strategy()
    
    def _load_strategy(self):
        """加载 GTO 策略数据"""
        # 简化版 GTO 策略矩阵
        # 在实际应用中，这些数据应该从数据库或外部文件加载
        self.strategy = self._build_simplified_strategy()
    
    def _build_simplified_strategy(self) -> Dict:
        """
        构建简化的 GTO 策略
        基于常见的 GTO 开牌范围和跟注/3bet 范围
        """
        strategy = {}
        
        for pos in self.POSITIONS:
            strategy[pos] = {}
            for action in self.ACTIONS_TO_YOU.keys():
                strategy[pos][action] = self._get_position_strategy(pos, action)
        
        return strategy
    
    def _get_position_strategy(self, position: str, action_to_you: str) -> Dict[str, Dict]:
        """
        获取特定位置和行动的 GTO 策略
        返回格式: {hand: {action: frequency}}
        """
        strategy = {}
        
        # 根据筹码深度调整
        if self.stack_size <= 50:
            open_raise_size = "all_in" if position in ['SB', 'BB'] else "raise_2.5bb"
        else:
            open_raise_size = "raise_2.5bb"
        
        for hand in ALL_HANDS:
            strategy[hand] = self._calculate_hand_strategy(
                hand, position, action_to_you, open_raise_size
            )
        
        return strategy
    
    def _calculate_hand_strategy(self, hand: str, position: str, 
                                  action_to_you: str, open_raise_size: str) -> Dict[str, float]:
        """计算单手牌的 GTO 策略"""
        
        hand_rank = get_hand_rank(hand)
        hand_type = get_hand_type(hand)
        
        # 基于位置和行动的简化策略
        if action_to_you == 'open':
            return self._open_strategy(hand, hand_rank, hand_type, position)
        elif action_to_you.startswith('vs_raise'):
            # 修正解析逻辑，从 'vs_raise_2.5bb' 中提取 2.5
            raise_size_str = action_to_you.split('_')[-1].replace('bb', '')
            try:
                raise_size = float(raise_size_str)
            except ValueError:
                raise_size = 2.5  # 默认值
            return self._vs_raise_strategy(hand, hand_rank, hand_type, position, raise_size)
        elif action_to_you == 'vs_limp':
            return self._vs_limp_strategy(hand, hand_rank, hand_type, position)
        elif action_to_you == 'vs_3bet':
            return self._vs_3bet_strategy(hand, hand_rank, hand_type, position)
        elif action_to_you == 'vs_all_in':
            return self._vs_all_in_strategy(hand, hand_rank, hand_type, position)
        
        return {'fold': 1.0}
    
    def _open_strategy(self, hand: str, hand_rank: int, hand_type: str, position: str) -> Dict[str, float]:
        """开牌策略 (前面都弃牌)"""
        
        # 根据位置定义开牌范围
        open_ranges = {
            'UTG': 169 - 55,   # 约 33% 最强牌
            'MP': 169 - 70,    # 约 42% 最强牌
            'CO': 169 - 90,    # 约 53% 最强牌
            'BTN': 169 - 120,  # 约 71% 最强牌
            'SB': 169 - 80,    # 约 47% 最强牌 (SB 位置较差)
            'BB': 169 - 50,    # 通常 BB 不会开牌，因为已经在大盲
        }
        
        # 小盲特殊处理 (limp 或 raise)
        if position == 'SB':
            if hand_rank <= 40:  # 强牌
                return {f'raise_{self.stack_size}bb' if self.stack_size <= 20 else 'raise_3bb': 0.8, 'fold': 0.2}
            elif hand_rank <= 80:
                return {'raise_3bb': 0.4, 'limp': 0.4, 'fold': 0.2}
            elif hand_rank <= 120:
                return {'limp': 0.6, 'fold': 0.4}
            else:
                return {'fold': 1.0}
        
        threshold = open_ranges.get(position, 169 - 50)
        
        if hand_rank <= threshold * 0.3:  # 顶级牌力
            if position == 'BB':
                return {'check': 1.0}
            return {'raise_2.5bb': 0.7, 'raise_3bb': 0.2, 'limp': 0.1}
        elif hand_rank <= threshold * 0.6:  # 强牌
            if position == 'BB':
                return {'check': 1.0}
            return {'raise_2.5bb': 0.5, 'limp': 0.3, 'fold': 0.2}
        elif hand_rank <= threshold:  # 中等牌
            if position == 'BB':
                return {'check': 0.9, 'raise_3bb': 0.1}
            return {'limp': 0.5, 'fold': 0.5}
        else:  # 弱牌
            if position == 'BB':
                return {'check': 1.0}
            return {'fold': 1.0}
    
    def _vs_raise_strategy(self, hand: str, hand_rank: int, hand_type: str, 
                           position: str, raise_size: float) -> Dict[str, float]:
        """面对加注的策略"""
        
        # 3bet 范围 (强牌)
        three_bet_threshold = 169 - 25  # 约 15% 最强牌
        
        # 跟注范围
        call_threshold = 169 - 70  # 约 42% 最强牌
        
        if hand_rank <= three_bet_threshold * 0.4:  # 顶级牌 3bet
            return {'raise_3x': 0.6, 'raise_all_in': 0.2, 'call': 0.2}
        elif hand_rank <= three_bet_threshold:  # 强牌 3bet
            return {'raise_3x': 0.4, 'call': 0.4, 'fold': 0.2}
        elif hand_rank <= call_threshold:  # 中等牌跟注
            # 根据位置调整
            if position in ['BB', 'SB']:
                return {'call': 0.6, 'fold': 0.4}  # 盲注位置有赔率
            else:
                return {'call': 0.4, 'fold': 0.6}
        else:
            return {'fold': 1.0}
    
    def _vs_limp_strategy(self, hand: str, hand_rank: int, hand_type: str, position: str) -> Dict[str, float]:
        """面对溜入的策略 (通常隔离加注)"""
        
        if hand_rank <= 169 - 60:  # 强牌隔离
            return {'raise_4bb': 0.7, 'limp': 0.2, 'fold': 0.1}
        elif hand_rank <= 169 - 100:  # 中等牌
            return {'raise_4bb': 0.3, 'limp': 0.5, 'fold': 0.2}
        else:  # 弱牌
            return {'limp': 0.3, 'fold': 0.7}
    
    def _vs_3bet_strategy(self, hand: str, hand_rank: int, hand_type: str, position: str) -> Dict[str, float]:
        """面对 3bet 的策略"""
        
        if hand_rank <= 169 - 20:  # 超强牌
            return {'raise_all_in': 0.5, 'call': 0.5}
        elif hand_rank <= 169 - 40:  # 强牌
            return {'raise_all_in': 0.2, 'call': 0.5, 'fold': 0.3}
        elif hand_rank <= 169 - 70:  # 中等牌
            if position == 'BB' or self.stack_size <= 30:
                return {'call': 0.4, 'fold': 0.6}
            return {'call': 0.2, 'fold': 0.8}
        else:
            return {'fold': 1.0}
    
    def _vs_all_in_strategy(self, hand: str, hand_rank: int, hand_type: str, position: str) -> Dict[str, float]:
        """面对 All-in 的策略"""
        
        # 根据筹码深度调整跟注范围
        if self.stack_size <= 20:  # 短筹码
            call_threshold = 169 - 80  # 较宽范围
        elif self.stack_size <= 50:
            call_threshold = 169 - 50  # 中等范围
        else:
            call_threshold = 169 - 35  # 紧范围
        
        if hand_rank <= call_threshold:
            return {'call': 1.0}
        else:
            return {'fold': 1.0}
    
    def get_strategy(self, hand: str, position: str, action_to_you: str) -> Dict[str, float]:
        """获取特定手牌的 GTO 策略"""
        hand_key = hand if hand in self.strategy.get(position, {}).get(action_to_you, {}) else None
        
        if hand_key is None:
            # 返回默认策略
            return self._calculate_hand_strategy(hand, position, action_to_you, "raise_2.5bb")
        
        return self.strategy[position][action_to_you].get(hand, {'fold': 1.0})
    
    def get_best_action(self, hand: str, position: str, action_to_you: str) -> str:
        """获取最佳行动 (频率最高的)"""
        strategy = self.get_strategy(hand, position, action_to_you)
        return max(strategy.items(), key=lambda x: x[1])[0]
    
    def sample_action(self, hand: str, position: str, action_to_you: str) -> str:
        """根据 GTO 频率采样行动"""
        strategy = self.get_strategy(hand, position, action_to_you)
        actions = list(strategy.keys())
        frequencies = list(strategy.values())
        
        return random.choices(actions, weights=frequencies, k=1)[0]
    
    def is_action_correct(self, hand: str, position: str, action_to_you: str, 
                          user_action: str, tolerance: float = 0.1) -> bool:
        """
        判断用户行动是否正确
        tolerance: 容差，如果用户选择了一个有显著频率 (> tolerance) 的行动，则认为是正确的
        """
        strategy = self.get_strategy(hand, position, action_to_you)
        
        # 如果该行动在 GTO 策略中有超过容差的频率，则认为是正确的
        return strategy.get(user_action, 0) >= tolerance
    
    def get_advice(self, hand: str, position: str, action_to_you: str) -> Dict:
        """获取建议"""
        strategy = self.get_strategy(hand, position, action_to_you)
        best_action = self.get_best_action(hand, position, action_to_you)
        
        # 生成解释
        explanation = self._generate_explanation(hand, position, action_to_you, strategy)
        
        return {
            'hand': hand,
            'position': position,
            'action_to_you': action_to_you,
            'best_action': best_action,
            'strategy': strategy,
            'explanation': explanation
        }
    
    def _generate_explanation(self, hand: str, position: str, 
                              action_to_you: str, strategy: Dict[str, float]) -> str:
        """生成策略解释"""
        explanations = []
        
        hand_type = get_hand_type(hand)
        best_action = max(strategy.items(), key=lambda x: x[1])
        
        if best_action[0] == 'fold':
            explanations.append(f"{hand} 在当前位置和面对的行动下不够强，建议弃牌。")
        elif best_action[0].startswith('raise'):
            if hand_type == 'pair' and hand[0] in ['A', 'K', 'Q']:
                explanations.append(f"{hand} 是强对子，建议加注建立底池。")
            elif hand_type == 'suited' and 'A' in hand:
                explanations.append(f"{hand} 是同花Ax牌，有坚果同花潜力，建议加注。")
            else:
                explanations.append(f"{hand} 在当前位置足够强，建议加注。")
        elif best_action[0] == 'call':
            explanations.append(f"{hand} 有不错的赔率，建议跟注看翻牌。")
        elif best_action[0] == 'limp':
            explanations.append(f"{hand} 适合溜入看便宜的翻牌。")
        
        # 添加混合策略说明
        mixed_actions = [a for a, f in strategy.items() if 0.1 <= f < 0.9]
        if len(mixed_actions) > 1:
            explanations.append(f"注意：这是一个混合策略场景，GTO 建议在不同频率下采取不同行动以避免被剥削。")
        
        return " ".join(explanations)


# 全局策略实例缓存
_strategy_cache: Dict[int, GTOStrategy] = {}


def get_gto_strategy(stack_size: int) -> GTOStrategy:
    """获取 GTO 策略实例 (带缓存)"""
    if stack_size not in _strategy_cache:
        _strategy_cache[stack_size] = GTOStrategy(stack_size)
    return _strategy_cache[stack_size]


def generate_training_scenarios(stack_size: int, position: str, action_to_you: str, 
                                 count: int = 10, difficulty: str = "normal") -> List[Dict]:
    """
    生成训练场景（增强版）
    difficulty: easy, normal, hard
    """
    strategy = get_gto_strategy(stack_size)
    scenarios = []
    
    # 根据难度选择手牌策略
    if difficulty == "easy":
        # 简单模式：更多边缘手牌（决策更明确）
        hand_pool = [h for h in ALL_HANDS if _get_decision_clarity(strategy, h, position, action_to_you) > 0.7]
        if len(hand_pool) < count * 2:
            hand_pool = ALL_HANDS
    elif difficulty == "hard":
        # 困难模式：更多混合策略手牌
        hand_pool = [h for h in ALL_HANDS if _get_decision_clarity(strategy, h, position, action_to_you) < 0.5]
        if len(hand_pool) < count * 2:
            hand_pool = ALL_HANDS
    else:
        hand_pool = ALL_HANDS
    
    # 随机选择手牌
    selected_hands = random.sample(hand_pool, min(count * 2, len(hand_pool)))
    
    # 打乱顺序，确保不同强度手牌混合
    random.shuffle(selected_hands)
    
    for i, hand in enumerate(selected_hands[:count]):
        hand_strategy = strategy.get_strategy(hand, position, action_to_you)
        best_action = strategy.get_best_action(hand, position, action_to_you)
        
        # 获取所有可能的行动（用于生成干扰项）
        all_possible_actions = ['fold', 'call', 'raise_2.5bb', 'raise_3bb', 'limp', 'all_in']
        valid_actions = [a for a, f in hand_strategy.items() if f > 0.05]
        
        if not valid_actions:
            valid_actions = ['fold']
        
        # 生成选项（带干扰项）
        options = _generate_options_with_distractors(
            valid_actions, best_action, hand_strategy, difficulty
        )
        
        # 随机打乱选项顺序（关键！）
        random.shuffle(options)
        
        scenarios.append({
            'id': i + 1,
            'hand': hand,
            'position': position,
            'action_to_you': action_to_you,
            'options': options,
            'correct_action': best_action,
            'gto_frequency': hand_strategy,
            'difficulty': _calculate_difficulty(hand_strategy),
            'time_limit': _get_time_limit(difficulty)
        })
    
    return scenarios


def _get_decision_clarity(strategy, hand: str, position: str, action_to_you: str) -> float:
    """
    获取决策清晰度（0-1，越高说明决策越明确）
    """
    hand_strategy = strategy.get_strategy(hand, position, action_to_you)
    if not hand_strategy:
        return 0.5
    
    # 计算最高频率和次高频率的差距
    sorted_freqs = sorted(hand_strategy.values(), reverse=True)
    if len(sorted_freqs) < 2:
        return 1.0
    
    # 差距越大，决策越清晰
    clarity = sorted_freqs[0] - sorted_freqs[1]
    return clarity


def _generate_options_with_distractors(valid_actions: list, best_action: str, 
                                        strategy: dict, difficulty: str) -> list:
    """
    生成带干扰项的选项
    """
    options = valid_actions.copy()
    
    # 根据难度添加干扰项
    if difficulty == "hard":
        # 困难模式：添加更多干扰项
        distractors = {
            'fold': 'limp',
            'call': 'raise_2bb',
            'raise_2.5bb': 'raise_4bb',
            'limp': 'call'
        }
        
        for action in valid_actions[:2]:  # 只为部分动作添加干扰
            if action in distractors and distractors[action] not in options:
                options.append(distractors[action])
    
    # 确保最佳动作在选项中
    if best_action not in options:
        options.append(best_action)
    
    # 限制选项数量（避免过多）
    if len(options) > 4:
        # 保留最佳动作，其他随机选择
        other_options = [o for o in options if o != best_action]
        random.shuffle(other_options)
        options = [best_action] + other_options[:3]
    
    return options


def _calculate_difficulty(strategy: dict) -> str:
    """计算难度等级"""
    if not strategy:
        return "normal"
    
    sorted_freqs = sorted(strategy.values(), reverse=True)
    if len(sorted_freqs) < 2:
        return "easy"
    
    clarity = sorted_freqs[0] - sorted_freqs[1]
    
    if clarity > 0.6:
        return "easy"
    elif clarity < 0.3:
        return "hard"
    else:
        return "normal"


def _get_time_limit(difficulty: str) -> int:
    """获取答题时间限制（秒）"""
    time_limits = {
        "easy": 15,
        "normal": 10,
        "hard": 8
    }
    return time_limits.get(difficulty, 10)
