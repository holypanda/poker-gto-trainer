"""
高级训练服务 - 完整牌局模拟
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.services.poker_simulator import PokerSimulator, PokerScenario
from app.services.gto_engine import get_hand_type


class AdvancedTrainingService:
    """高级训练服务"""
    
    def __init__(self, stack_size: int = 100):
        self.simulator = PokerSimulator(stack_size)
    
    def create_simulation_session(self, count: int = 10, 
                                   hero_position: Optional[str] = None) -> List[Dict]:
        """创建模拟训练会话"""
        scenarios = self.simulator.generate_scenarios(count, hero_position)
        
        # 转换为前端友好的格式
        result = []
        for s in scenarios:
            result.append({
                "id": s.id,
                "description": s.description,
                "hero_position": s.hero_position,
                "hero_hand": s.hero_hand,
                "hand_type": self._get_hand_type_name(s.hero_hand),
                "stack_size": s.stack_size,
                "actions_before": [
                    {
                        "position": a.position,
                        "action": a.action,
                        "amount": a.amount,
                        "display": self._format_action(a)
                    }
                    for a in s.actions_before
                ],
                "current_bet": s.current_bet,
                "pot_size": s.pot_size,
                "options": s.options,
                "correct_action": s.correct_action,
                "gto_frequency": s.gto_frequency,
                "explanation": s.explanation
            })
        
        return result
    
    def _get_hand_type_name(self, hand: str) -> str:
        """获取手牌类型名称"""
        if len(hand) == 2:
            return "对子"
        elif hand.endswith('s'):
            return "同花"
        else:
            return "不同花"
    
    def _format_action(self, action) -> str:
        """格式化行动显示"""
        if action.action == "fold":
            return f"{action.position} 弃牌"
        elif action.action == "call":
            return f"{action.position} 跟注 {action.amount}BB"
        elif action.action == "raise":
            return f"{action.position} 加注到 {action.amount}BB"
        elif action.action == "all_in":
            return f"{action.position} All-in {action.amount}BB"
        elif action.action == "check":
            return f"{action.position} 过牌"
        else:
            return f"{action.position} {action.action}"
    
    def evaluate_decision(self, scenario_id: int, user_action: str, 
                          scenario_data: Dict) -> Dict:
        """评估用户决策"""
        
        correct_action = scenario_data.get("correct_action", "")
        gto_frequency = scenario_data.get("gto_frequency", {})
        
        # 判断是否接近正确（如果在 GTO 混合策略范围内）
        is_correct = user_action == correct_action
        
        # 如果用户选择了一个有高频率的行动，也可以算对
        if not is_correct:
            freq = gto_frequency.get(user_action.replace(f"raise_{scenario_data.get('pot_size', 0)}bb", "raise"), 0)
            if freq >= 0.2:  # 20% 以上频率
                is_correct = True
        
        # 生成详细反馈
        feedback = self._generate_feedback(
            scenario_data.get("hero_hand", ""),
            user_action,
            correct_action,
            scenario_data.get("actions_before", []),
            is_correct
        )
        
        return {
            "is_correct": is_correct,
            "user_action": user_action,
            "correct_action": correct_action,
            "gto_frequency": gto_frequency,
            "feedback": feedback,
            "explanation": scenario_data.get("explanation", "")
        }
    
    def _generate_feedback(self, hand: str, user_action: str, 
                          correct: str, actions: List, is_correct: bool) -> str:
        """生成反馈"""
        if is_correct:
            return "正确！这是一个符合 GTO 的决策。"
        
        # 根据具体情况给出建议
        if user_action == "fold" and correct != "fold":
            return f"{hand} 在这里其实可以玩，建议跟注或加注。"
        elif user_action in ["raise", "all_in"] and correct == "fold":
            return f"{hand} 太弱了，面对这个行动建议弃牌。"
        elif user_action == "call" and correct == "fold":
            return f"{hand} 在这个位置面对这个下注太边缘了，建议弃牌。"
        else:
            return "这个决策需要改进，建议查看 GTO 频率分布。"
