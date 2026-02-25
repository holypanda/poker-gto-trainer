"""
翻牌策略引擎
V1.1 新增 - 简化版策略，基于规则的 GTO 近似
"""
from typing import Dict, List, Optional, Tuple
import random


class FlopStrategyEngine:
    """
    翻牌策略引擎
    基于规则的简化 GTO 策略，输出概率分布
    """
    
    # 底池类型
    POT_TYPES = ["SRP", "3BP", "4BP"]  # Single Raised Pot, 3-Bet Pot, 4-Bet Pot
    
    # 位置关系
    POSITION_ORDER = {"UTG": 0, "MP": 1, "CO": 2, "BTN": 3, "SB": 4, "BB": 5}
    
    # SPR 桶
    SPR_BUCKETS = {
        "LOW": (0, 3),
        "MED": (3, 6),
        "HIGH": (6, float('inf'))
    }
    
    # 牌面纹理
    BOARD_TEXTURES = ["dry", "wet", "paired", "monotone", "two_tone"]
    
    # 手牌桶
    HAND_BUCKETS = ["made_strong", "made_medium", "made_weak", "draw_strong", "draw_weak", "air"]
    
    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()
    
    def get_context_id(self, pot_type: str, hero_position: str, 
                       villain_position: str, is_pfr: bool) -> str:
        """
        生成 context_id
        格式: FLOP_{pot_type}_{hero_pos}v{villain_pos}_{IP/OOP}_{PFR/ Defender}_{CBET/vsCBET}
        """
        # 判断 IP/OOP
        hero_order = self.POSITION_ORDER[hero_position]
        villain_order = self.POSITION_ORDER[villain_position]
        ip_oop = "IP" if hero_order < villain_order else "OOP"
        
        # 判断是 PFR 还是 Defender
        role = "PFR" if is_pfr else "DEF"
        
        # 决策类型
        decision = "CBET" if is_pfr else "vsCBET"
        
        return f"FLOP_{pot_type}_{hero_position}v{villain_position}_{ip_oop}_{role}_{decision}"
    
    def calculate_spr_bucket(self, spr: float) -> str:
        """计算 SPR 桶"""
        for bucket, (low, high) in self.SPR_BUCKETS.items():
            if low <= spr < high:
                return bucket
        return "HIGH"
    
    def analyze_board_texture(self, board: List[str]) -> List[str]:
        """
        分析牌面纹理
        返回标签列表
        """
        textures = []
        
        ranks = [c[0] for c in board]
        suits = [c[1] for c in board]
        
        # 检查对子
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        if any(c >= 2 for c in rank_counts.values()):
            textures.append("paired")
        
        # 检查单色
        if len(set(suits)) == 1:
            textures.append("monotone")
        elif len(set(suits)) == 2:
            textures.append("two_tone")
        
        # 检查湿润度 (简化版)
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
                       '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        values = sorted([rank_values[r] for r in ranks], reverse=True)
        
        # 连张判断
        gaps = [values[i] - values[i+1] for i in range(len(values)-1)]
        if max(gaps) <= 2:  # 紧密的牌面
            textures.append("wet")
        else:
            textures.append("dry")
        
        return textures if textures else ["dry"]
    
    def get_strategy(self, context_id: str, hand_bucket: str, 
                     spr_bucket: str, board_texture: List[str],
                     is_pfr: bool, ip_oop: str) -> Dict[str, float]:
        """
        获取策略分布
        返回: {action: probability}
        """
        # 基于规则的策略矩阵
        # 这不是 solver，是基于经验的简化策略
        
        if is_pfr:
            # PFR (翻前进攻方) - C-bet 决策
            return self._pfr_strategy(hand_bucket, spr_bucket, board_texture, ip_oop)
        else:
            # Defender (翻前防守方) - vs C-bet 决策
            return self._defender_strategy(hand_bucket, spr_bucket, board_texture, ip_oop)
    
    def _pfr_strategy(self, hand_bucket: str, spr_bucket: str, 
                      board_texture: List[str], ip_oop: str) -> Dict[str, float]:
        """翻前进攻方策略 (C-bet)"""
        
        # 基础策略
        strategy = {"check": 0.5, "bet33": 0.3, "bet75": 0.15, "bet125": 0.05}
        
        # 根据手牌桶调整
        if hand_bucket == "made_strong":
            # 强牌：大尺度下注
            strategy = {"check": 0.2, "bet33": 0.3, "bet75": 0.35, "bet125": 0.15}
        
        elif hand_bucket == "made_medium":
            # 中等牌：中等尺度
            strategy = {"check": 0.3, "bet33": 0.45, "bet75": 0.2, "bet125": 0.05}
        
        elif hand_bucket == "made_weak":
            # 弱牌：小尺度或 check
            strategy = {"check": 0.5, "bet33": 0.4, "bet75": 0.08, "bet125": 0.02}
        
        elif hand_bucket == "draw_strong":
            # 强听牌：混合策略
            strategy = {"check": 0.35, "bet33": 0.35, "bet75": 0.25, "bet125": 0.05}
        
        elif hand_bucket == "draw_weak":
            # 弱听牌：check 为主
            strategy = {"check": 0.6, "bet33": 0.3, "bet75": 0.08, "bet125": 0.02}
        
        else:  # air
            # 空气牌：小尺度诈唬或 check
            strategy = {"check": 0.55, "bet33": 0.35, "bet75": 0.08, "bet125": 0.02}
        
        # 根据牌面纹理调整
        if "wet" in board_texture:
            # 湿润牌面：更多 check
            strategy["check"] += 0.15
            strategy["bet33"] -= 0.05
            strategy["bet75"] -= 0.05
            strategy["bet125"] -= 0.05
        
        if "monotone" in board_texture:
            # 单色牌面：减少大尺度
            strategy["bet125"] *= 0.5
            strategy["check"] += 0.05
        
        if "paired" in board_texture:
            # 对子牌面：取决于具体对子
            pass
        
        # 根据 SPR 调整
        if spr_bucket == "LOW":
            # 低 SPR：减少诈唬，更多 allin
            if hand_bucket in ["air", "draw_weak"]:
                strategy["check"] += 0.2
                strategy["bet33"] -= 0.1
                strategy["bet75"] -= 0.1
        
        elif spr_bucket == "HIGH":
            # 高 SPR：更多小尺度
            strategy["bet33"] += 0.05
            strategy["bet75"] -= 0.03
            strategy["bet125"] -= 0.02
        
        # 根据位置调整
        if ip_oop == "OOP":
            # OOP：更多 check
            strategy["check"] += 0.1
            strategy["bet33"] -= 0.05
            strategy["bet75"] -= 0.03
            strategy["bet125"] -= 0.02
        
        # 归一化
        total = sum(strategy.values())
        return {k: round(v / total, 2) for k, v in strategy.items()}
    
    def _defender_strategy(self, hand_bucket: str, spr_bucket: str,
                           board_texture: List[str], ip_oop: str) -> Dict[str, float]:
        """翻前防守方策略 (vs C-bet)"""
        
        # 基础策略
        strategy = {"fold": 0.3, "call": 0.55, "raise75": 0.1, "raise125": 0.05}
        
        # 根据手牌桶调整
        if hand_bucket == "made_strong":
            # 强牌：加注
            strategy = {"fold": 0, "call": 0.3, "raise75": 0.45, "raise125": 0.25}
        
        elif hand_bucket == "made_medium":
            # 中等牌：跟注
            strategy = {"fold": 0.05, "call": 0.75, "raise75": 0.15, "raise125": 0.05}
        
        elif hand_bucket == "made_weak":
            # 弱牌：有时跟注
            strategy = {"fold": 0.35, "call": 0.55, "raise75": 0.08, "raise125": 0.02}
        
        elif hand_bucket == "draw_strong":
            # 强听牌：加注或跟注
            strategy = {"fold": 0.1, "call": 0.5, "raise75": 0.3, "raise125": 0.1}
        
        elif hand_bucket == "draw_weak":
            # 弱听牌：偶尔跟注
            strategy = {"fold": 0.45, "call": 0.45, "raise75": 0.08, "raise125": 0.02}
        
        else:  # air
            # 空气牌：弃牌
            strategy = {"fold": 0.8, "call": 0.15, "raise75": 0.04, "raise125": 0.01}
        
        # 根据牌面纹理调整
        if "wet" in board_texture:
            # 湿润牌面：更多跟注（听牌多）
            strategy["fold"] -= 0.1
            strategy["call"] += 0.1
        
        if "monotone" in board_texture:
            # 单色牌面：收紧
            strategy["fold"] += 0.1
            strategy["call"] -= 0.05
            strategy["raise75"] -= 0.03
            strategy["raise125"] -= 0.02
        
        # 根据 SPR 调整
        if spr_bucket == "LOW":
            # 低 SPR：收紧
            strategy["fold"] += 0.1
            strategy["call"] -= 0.05
            strategy["raise75"] -= 0.03
            strategy["raise125"] -= 0.02
        
        # 根据位置调整
        if ip_oop == "IP":
            # IP：更多跟注
            strategy["fold"] -= 0.05
            strategy["call"] += 0.05
        
        # 归一化
        total = sum(strategy.values())
        return {k: round(v / total, 2) for k, v in strategy.items()}
    
    def get_best_action(self, strategy: Dict[str, float]) -> str:
        """获取最佳动作"""
        return max(strategy.items(), key=lambda x: x[1])[0]
    
    def sample_action(self, strategy: Dict[str, float]) -> str:
        """根据策略采样动作"""
        actions = list(strategy.keys())
        weights = list(strategy.values())
        return self.rng.choices(actions, weights=weights, k=1)[0]
    
    def calculate_grade(self, user_action: str, strategy: Dict[str, float]) -> Tuple[str, float]:
        """
        计算用户动作的评级
        返回: (grade, probability)
        """
        prob = strategy.get(user_action, 0)
        
        if prob >= 0.60:
            return ("PERFECT", prob)
        elif prob >= 0.20:
            return ("ACCEPTABLE", prob)
        else:
            return ("WRONG", prob)
    
    def get_explanation(self, hand_bucket: str, is_pfr: bool, 
                        board_texture: List[str], best_action: str) -> str:
        """获取策略解释"""
        explanations = []
        
        if is_pfr:
            if hand_bucket == "made_strong":
                explanations.append("你持有强成牌，建议主动建立底池。")
            elif hand_bucket == "draw_strong":
                explanations.append("你持有强听牌，可通过下注获取弃牌率或建立底池。")
            elif hand_bucket == "air":
                explanations.append("当前牌面与你的范围关联度较低，适度诈唬或放弃。")
            
            if "wet" in board_texture:
                explanations.append("湿润牌面听牌多，控制底池大小。")
            elif "dry" in board_texture:
                explanations.append("干燥牌面，可频繁小尺度下注。")
        else:
            if hand_bucket == "made_strong":
                explanations.append("面对下注，你持有强牌可考虑加注。")
            elif hand_bucket in ["draw_strong", "draw_weak"]:
                explanations.append("你持有听牌，根据赔率决定是否跟注。")
            
            if "monotone" in board_texture:
                explanations.append("单色牌面需谨慎，听牌未完成时收紧范围。")
        
        return " ".join(explanations) if explanations else "根据 GTO 策略执行。"
