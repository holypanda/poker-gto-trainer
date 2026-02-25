"""
完整牌局模拟器
模拟 6max 桌的真实牌局场景
"""

import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"

@dataclass
class PlayerAction:
    position: str
    action: str
    amount: Optional[float] = None  # 加注金额（BB）
    is_hero: bool = False  # 是否是用户

@dataclass
class PokerScenario:
    id: int
    description: str  # 场景描述
    hero_position: str  # 用户位置
    hero_hand: str  # 用户手牌
    stack_size: int  # 筹码深度（BB）
    actions_before: List[PlayerAction]  # 前面的行动
    current_bet: float  # 当前需要跟注的金额
    pot_size: float  # 底池大小
    options: List[str]  # 可用选项
    correct_action: str  # GTO 建议行动
    gto_frequency: Dict[str, float]  # GTO 频率
    explanation: str  # 解释


class PokerSimulator:
    """6max 扑克牌局模拟器"""
    
    POSITIONS = ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB']
    
    def __init__(self, stack_size: int = 100):
        self.stack_size = stack_size
        self.all_hands = self._generate_all_hands()
    
    def _generate_all_hands(self) -> List[str]:
        """生成所有起手牌"""
        ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        hands = []
        for i, r1 in enumerate(ranks):
            for j, r2 in enumerate(ranks):
                if i == j:
                    hands.append(f"{r1}{r2}")  # 对子
                elif i < j:
                    hands.append(f"{r1}{r2}s")  # 同花
                else:
                    hands.append(f"{r2}{r1}o")  # 不同花
        return hands
    
    def get_hand_strength(self, hand: str) -> int:
        """评估手牌强度 (1-169)"""
        # 简化版：基于牌力排序
        premium = ['AA', 'KK', 'QQ', 'JJ', 'AKs', 'AKo', 'AQs', 'AJs', 'ATs', 'KQs']
        strong = ['TT', '99', '88', 'AQo', 'A9s', 'A8s', 'KJs', 'KTs', 'QJs', 'JTs']
        
        if hand in premium:
            return random.randint(1, 20)
        elif hand in strong:
            return random.randint(21, 50)
        elif 's' in hand and ('A' in hand or 'K' in hand or 'Q' in hand):
            return random.randint(51, 80)
        elif len(hand) == 2:  # 中小对子
            return random.randint(40, 90)
        else:
            return random.randint(81, 169)
    
    def generate_random_scenario(self, hero_position: Optional[str] = None) -> PokerScenario:
        """生成随机牌局场景"""
        
        # 随机选择用户位置
        if hero_position is None:
            hero_position = random.choice(self.POSITIONS)
        
        # 随机手牌
        hero_hand = random.choice(self.all_hands)
        hand_strength = self.get_hand_strength(hero_hand)
        
        # 构建行动链
        actions_before = []
        pot_size = 1.5  # 盲注 0.5 + 1
        current_bet = 1.0  # 大盲
        
        # 根据位置构建前面的行动
        position_idx = self.POSITIONS.index(hero_position)
        
        # 场景类型
        scenario_type = random.choice([
            "open",           # 前面都弃牌，用户开牌
            "vs_raise",       # 有人加注
            "vs_3bet",        # 有人 3bet
            "vs_all_in",      # 有人 all-in
            "multi_caller",   # 多人跟注
            "squeeze"         # 挤压局面
        ])
        
        description = ""
        
        if scenario_type == "open":
            # 前面都弃牌
            description = f"前面位置都弃牌到{hero_position}"
            
        elif scenario_type == "vs_raise":
            # 有人加注
            raiser_pos = random.choice(self.POSITIONS[:position_idx]) if position_idx > 0 else "UTG"
            raise_size = random.choice([2.0, 2.5, 3.0, 4.0])
            actions_before.append(PlayerAction(raiser_pos, "raise", raise_size))
            pot_size += raise_size + 0.5  # 小盲弃牌，大盲防守
            current_bet = raise_size
            description = f"{raiser_pos} 加注到 {raise_size}BB"
            
        elif scenario_type == "vs_3bet":
            # 有人 3bet
            open_pos = random.choice(self.POSITIONS[:position_idx]) if position_idx > 0 else "UTG"
            actions_before.append(PlayerAction(open_pos, "raise", 2.5))
            
            # 有人跟注
            if random.random() > 0.5:
                caller_pos = random.choice([p for p in self.POSITIONS if p != open_pos and p != hero_position])
                actions_before.append(PlayerAction(caller_pos, "call", 2.5))
                pot_size += 2.5
            
            # 3bet
            three_bet_pos = random.choice([p for p in self.POSITIONS[position_idx+1:] if p != 'BB'])
            three_bet_size = random.choice([8.0, 9.0, 10.0, 12.0])
            actions_before.append(PlayerAction(three_bet_pos, "raise", three_bet_size))
            pot_size += three_bet_size + sum([a.amount or 0 for a in actions_before])
            current_bet = three_bet_size
            description = f"{open_pos} 开牌，{three_bet_pos} 3bet 到 {three_bet_size}BB"
            
        elif scenario_type == "vs_all_in":
            # 有人 all-in
            allin_pos = random.choice([p for p in self.POSITIONS if p != hero_position])
            allin_amount = random.randint(20, self.stack_size)
            actions_before.append(PlayerAction(allin_pos, "all_in", float(allin_amount)))
            pot_size += allin_amount
            current_bet = float(allin_amount)
            description = f"{allin_pos} All-in {allin_amount}BB"
            
        elif scenario_type == "multi_caller":
            # 多人跟注
            open_pos = random.choice(self.POSITIONS[:position_idx]) if position_idx > 0 else "UTG"
            actions_before.append(PlayerAction(open_pos, "raise", 3.0))
            
            # 1-2 个跟注
            num_callers = random.randint(1, 2)
            available_callers = [p for p in self.POSITIONS if p != open_pos and p != hero_position and self.POSITIONS.index(p) > self.POSITIONS.index(open_pos)]
            
            for i in range(min(num_callers, len(available_callers))):
                if available_callers:
                    caller = available_callers.pop(0)
                    actions_before.append(PlayerAction(caller, "call", 3.0))
                    pot_size += 3.0
            
            pot_size += 3.0
            current_bet = 3.0
            description = f"{open_pos} 加注到 3BB，{num_callers}人跟注"
            
        else:  # squeeze
            # 挤压局面：加注 + 跟注，用户可以做挤压加注
            open_pos = random.choice(self.POSITIONS[:position_idx]) if position_idx > 0 else "UTG"
            actions_before.append(PlayerAction(open_pos, "raise", 2.5))
            
            caller_pos = random.choice([p for p in self.POSITIONS if p != open_pos and p != hero_position and self.POSITIONS.index(p) > self.POSITIONS.index(open_pos)])
            actions_before.append(PlayerAction(caller_pos, "call", 2.5))
            
            pot_size = 2.5 + 2.5 + 0.5 + 1  # 加注 + 跟注 + 盲注
            current_bet = 2.5
            description = f"{open_pos} 加注到 2.5BB，{caller_pos} 跟注，底池挤压机会"
        
        # 根据场景计算 GTO 建议
        options, correct_action, gto_freq = self._calculate_gto_decision(
            hero_hand, hero_position, actions_before, current_bet, pot_size, hand_strength
        )
        
        return PokerScenario(
            id=random.randint(1, 10000),
            description=description,
            hero_position=hero_position,
            hero_hand=hero_hand,
            stack_size=self.stack_size,
            actions_before=actions_before,
            current_bet=current_bet,
            pot_size=round(pot_size, 1),
            options=options,
            correct_action=correct_action,
            gto_frequency=gto_freq,
            explanation=self._generate_explanation(hero_hand, hero_position, actions_before, correct_action, hand_strength)
        )
    
    def _calculate_gto_decision(self, hand: str, position: str, 
                                 actions: List[PlayerAction], current_bet: float,
                                 pot_size: float, hand_strength: int) -> Tuple[List[str], str, Dict[str, float]]:
        """计算 GTO 决策"""
        
        # 根据手牌强度和局面生成选项
        options = []
        gto_freq = {}
        
        # 总是有弃牌选项
        options.append("fold")
        
        # 如果不需要跟注（前面都弃牌），可以过牌
        if current_bet <= 1.0 and not actions:
            options.append("check")
        
        # 如果有下注，可以加注或跟注
        if actions:
            # 跟注选项
            if current_bet < self.stack_size:
                options.append("call")
            
            # 加注选项
            if hand_strength < 100:  # 不是所有牌都能加注
                # 3bet 或 4bet
                if any(a.action == "raise" for a in actions):
                    raise_amount = current_bet * 3
                    if raise_amount < self.stack_size:
                        options.append(f"raise_{raise_amount:.0f}bb")
                        
                # 挤压加注
                if len([a for a in actions if a.action in ["call", "raise"]]) >= 2:
                    squeeze_amount = current_bet * 4 + pot_size
                    if squeeze_amount < self.stack_size:
                        options.append(f"raise_{squeeze_amount:.0f}bb")
                
                # 标准加注
                standard_raise = pot_size + current_bet
                if standard_raise < self.stack_size and f"raise_{standard_raise:.0f}bb" not in options:
                    options.append(f"raise_{standard_raise:.0f}bb")
        else:
            # 开牌
            options.extend(["raise_2.5bb", "raise_3bb", "limp"])
        
        # All-in 选项（总是可选）
        options.append("all_in")
        
        # 计算 GTO 频率
        if hand_strength <= 20:  # 强牌
            gto_freq = {"fold": 0.1, "call": 0.2, "raise": 0.5, "all_in": 0.2}
        elif hand_strength <= 50:  # 中等牌
            gto_freq = {"fold": 0.3, "call": 0.4, "raise": 0.2, "all_in": 0.1}
        elif hand_strength <= 100:  # 弱牌
            gto_freq = {"fold": 0.6, "call": 0.3, "raise": 0.05, "all_in": 0.05}
        else:  # 非常弱的牌
            gto_freq = {"fold": 0.9, "call": 0.08, "raise": 0.01, "all_in": 0.01}
        
        # 确定最佳行动
        if hand_strength <= 20:
            correct_action = "raise" if any(a.action == "raise" for a in actions) else "raise_2.5bb"
        elif hand_strength <= 50:
            correct_action = "call" if any(a.action == "raise" for a in actions) else "raise_2.5bb"
        elif hand_strength <= 80:
            correct_action = "call" if current_bet <= 5 else "fold"
        else:
            correct_action = "fold"
        
        # 确保正确行动在选项中
        if correct_action not in options and options:
            correct_action = options[1] if len(options) > 1 else options[0]
        
        return options, correct_action, gto_freq
    
    def _generate_explanation(self, hand: str, position: str, 
                              actions: List[PlayerAction], correct: str, strength: int) -> str:
        """生成解释"""
        if strength <= 20:
            return f"{hand} 是强牌，建议积极下注建立底池或做价值加注。"
        elif strength <= 50:
            return f"{hand} 是中等强度牌，在有位置优势时可以跟注或加注，没有位置时谨慎行事。"
        elif strength <= 80:
            return f"{hand} 是边缘牌，面对小注可以跟注看翻牌，大注建议弃牌。"
        else:
            return f"{hand} 是弱牌，建议弃牌等待更好的机会。"
    
    def generate_scenarios(self, count: int = 10, hero_position: Optional[str] = None) -> List[PokerScenario]:
        """生成多个训练场景"""
        scenarios = []
        for i in range(count):
            scenario = self.generate_random_scenario(hero_position)
            scenario.id = i + 1
            scenarios.append(scenario)
        return scenarios
