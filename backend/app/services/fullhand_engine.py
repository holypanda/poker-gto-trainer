"""
完整牌局模拟引擎
V1.1 核心模块
"""
import random
import hashlib
import math
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

# 导入 treys 进行牌力评估
try:
    from treys import Card, Evaluator
    HAS_TREYS = True
except ImportError:
    HAS_TREYS = False
    Card = None
    Evaluator = None


class Street(Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


class ActionType(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALLIN = "allin"
    SB = "sb"
    BB = "bb"
    ANTE = "ante"


class GameStatus(Enum):
    INIT = "INIT"
    PREFLOP = "PREFLOP"
    FLOP_DECISION = "FLOP_DECISION"
    FAST_FORWARD = "FAST_FORWARD"
    ENDED = "ENDED"


@dataclass
class Player:
    seat: int
    position: str  # UTG, MP, CO, BTN, SB, BB
    stack: float
    in_hand: bool = True
    committed_this_street: float = 0.0
    total_committed: float = 0.0
    hole_cards: Optional[List[str]] = None
    is_hero: bool = False
    is_active: bool = True  # 本轮还能行动（未弃牌且未allin）
    
    def to_dict(self) -> Dict:
        return {
            "seat": self.seat,
            "position": self.position,
            "stack": round(self.stack, 2),
            "in_hand": self.in_hand,
            "committed_this_street": round(self.committed_this_street, 2),
            "total_committed": round(self.total_committed, 2),
            "hole_cards": self.hole_cards if self.is_hero else None,
            "is_hero": self.is_hero,
            "is_active": self.is_active,
        }


@dataclass
class Action:
    street: str
    seat: int
    position: str
    action: str
    amount: Optional[float] = None
    pot_after: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "street": self.street,
            "seat": self.seat,
            "position": self.position,
            "action": self.action,
            "amount": round(self.amount, 2) if self.amount else None,
            "pot_after": round(self.pot_after, 2),
            "timestamp": self.timestamp,
        }


@dataclass
class KeySpot:
    """关键点记录"""
    street: str
    context_id: str
    pot_type: Optional[str] = None
    ip_oop: Optional[str] = None
    spr_bucket: Optional[str] = None
    board: Optional[List[str]] = None
    hero_hand: Optional[str] = None
    hero_hand_bucket: Optional[str] = None
    legal_actions: List[str] = field(default_factory=list)
    strategy: Dict[str, float] = field(default_factory=dict)
    user_action: Optional[str] = None
    user_action_prob: Optional[float] = None
    best_action: Optional[str] = None
    grade: Optional[str] = None
    explanation: str = ""  # 新增解释字段
    
    def to_dict(self) -> Dict:
        return {
            "street": self.street,
            "context_id": self.context_id,
            "pot_type": self.pot_type,
            "ip_oop": self.ip_oop,
            "spr_bucket": self.spr_bucket,
            "board": self.board,
            "hero_hand": self.hero_hand,
            "hero_hand_bucket": self.hero_hand_bucket,
            "legal_actions": self.legal_actions,
            "strategy": self.strategy,
            "user_action": self.user_action,
            "user_action_prob": self.user_action_prob,
            "best_action": self.best_action,
            "grade": self.grade,
            "explanation": getattr(self, 'explanation', ''),
        }


class PokerDeck:
    """扑克牌组"""
    SUITS = ['s', 'h', 'd', 'c']  # 黑桃、红桃、方块、梅花
    RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
    
    def __init__(self, seed: Optional[str] = None):
        self.cards = [r + s for s in self.SUITS for r in self.RANKS]
        self.rng = random.Random(seed)
        self.rng.shuffle(self.cards)
    
    def deal(self, n: int = 1) -> List[str]:
        dealt = self.cards[:n]
        self.cards = self.cards[n:]
        return dealt


class HandEvaluator:
    """手牌评估器"""
    
    RANK_VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
                   '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    
    @classmethod
    def evaluate_hand_bucket(cls, hand: List[str], board: List[str]) -> str:
        """
        评估手牌 bucket，用于策略决策
        返回: made_strong, made_medium, made_weak, draw_strong, draw_weak, air
        """
        all_cards = hand + board
        
        # 检查成牌
        made_rank = cls._get_made_hand_rank(hand, board)
        
        # 强成牌：两对及以上
        if made_rank >= 3:  # 两对、三条、顺子、同花、葫芦、四条、同花顺
            return "made_strong"
        
        # 中等成牌：一对顶对或强踢脚
        if made_rank == 2:  # 一对
            pair_rank = cls._get_pair_rank(hand, board)
            if pair_rank >= 12:  # Q 及以上
                return "made_medium"
        
        # 检查听牌
        flush_draw = cls._has_flush_draw(hand, board)
        straight_draw = cls._has_straight_draw(hand, board)
        
        if flush_draw and straight_draw:
            return "draw_strong"
        if flush_draw or (straight_draw == "open"):
            return "draw_strong"
        if straight_draw == "gutshot":
            return "draw_weak"
        
        # 弱成牌
        if made_rank == 2:
            return "made_weak"
        if made_rank == 1:  # 高牌
            high_card = max(cls.RANK_VALUES[h[0]] for h in hand)
            if high_card >= 13:  # K 或 A 高
                return "made_weak"
        
        return "air"
    
    @classmethod
    def _get_made_hand_rank(cls, hand: List[str], board: List[str]) -> int:
        """获取成牌等级 (1=高牌, 2=一对, 3=两对... 9=同花顺)"""
        # 简化版：返回近似等级
        ranks = [cls.RANK_VALUES[c[0]] for c in hand + board]
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        
        pairs = sum(1 for c in rank_counts.values() if c == 2)
        trips = sum(1 for c in rank_counts.values() if c == 3)
        quads = sum(1 for c in rank_counts.values() if c == 4)
        
        if quads:
            return 8
        if trips and pairs:
            return 7  # 葫芦
        if cls._has_flush(hand, board):
            return 6
        if cls._has_straight(hand, board):
            return 5
        if trips:
            return 4
        if pairs >= 2:
            return 3
        if pairs == 1:
            return 2
        return 1
    
    @classmethod
    def _has_flush(cls, hand: List[str], board: List[str]) -> bool:
        suits = [c[1] for c in hand + board]
        for suit in set(suits):
            if suits.count(suit) >= 5:
                return True
        return False
    
    @classmethod
    def _has_straight(cls, hand: List[str], board: List[str]) -> bool:
        ranks = sorted(set([cls.RANK_VALUES[c[0]] for c in hand + board]), reverse=True)
        if len(ranks) < 5:
            return False
        for i in range(len(ranks) - 4):
            if ranks[i] - ranks[i+4] == 4:
                return True
        # A-5 顺子
        if set([14, 5, 4, 3, 2]).issubset(set(ranks)):
            return True
        return False
    
    @classmethod
    def _has_flush_draw(cls, hand: List[str], board: List[str]) -> bool:
        suits = [c[1] for c in hand + board]
        for suit in set(suits):
            if suits.count(suit) == 4:
                return True
        return False
    
    @classmethod
    def _has_straight_draw(cls, hand: List[str], board: List[str]) -> Optional[str]:
        """返回: open, gutshot, None"""
        ranks = sorted(set([cls.RANK_VALUES[c[0]] for c in hand + board]), reverse=True)
        if len(ranks) < 4:
            return None
        
        # 检查两头顺听牌
        for i in range(len(ranks) - 3):
            gap = ranks[i] - ranks[i+3]
            if gap == 3:  # 连续4张
                return "open"
        
        # 检查卡顺听牌
        for i in range(len(ranks) - 3):
            gap = ranks[i] - ranks[i+3]
            if gap == 4:  # 中间缺一张
                return "gutshot"
        
        return None
    
    @classmethod
    def _get_pair_rank(cls, hand: List[str], board: List[str]) -> int:
        """获取对子的牌力等级"""
        all_ranks = [cls.RANK_VALUES[c[0]] for c in hand + board]
        rank_counts = {}
        for r in all_ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        
        pairs = [r for r, c in rank_counts.items() if c >= 2]
        return max(pairs) if pairs else 0
    
    @classmethod
    def format_hand(cls, cards: List[str]) -> str:
        """将两张手牌格式化为标准形式 (e.g., 'AKs', '72o', 'TT')"""
        if len(cards) != 2:
            return ""
        
        r1, r2 = cards[0][0], cards[1][0]
        s1, s2 = cards[0][1], cards[1][1]
        
        # 对子
        if r1 == r2:
            return r1 + r2
        
        # 按大小排序
        ranks = sorted([r1, r2], key=lambda x: cls.RANK_VALUES[x], reverse=True)
        
        # 同花
        if s1 == s2:
            return ranks[0] + ranks[1] + 's'
        else:
            return ranks[0] + ranks[1] + 'o'


class FullHandEngine:
    """完整牌局引擎"""
    
    POSITIONS_6MAX = ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB']
    
    def __init__(self, stack_bb: int = 100, seed: Optional[str] = None):
        self.stack_bb = stack_bb
        self.seed = seed or self._generate_seed()
        self.rng = random.Random(self.seed)
        
        # 游戏状态
        self.status = GameStatus.INIT
        self.street = Street.PREFLOP
        self.players: List[Player] = []
        self.button_seat = 0
        self.sb_seat = 1
        self.bb_seat = 2
        self.pot = 0.0
        self.current_bet = 0.0
        self.community_cards: List[str] = []
        self.action_log: List[Action] = []
        
        # Hero
        self.hero_seat: Optional[int] = None
        
        # 关键点
        self.preflop_key_spot: Optional[KeySpot] = None
        self.flop_key_spot: Optional[KeySpot] = None
        
        # 结果
        self.result_bb: Optional[float] = None
        self.ended_by: Optional[str] = None
        
        # 内部状态
        self._deck: Optional[PokerDeck] = None
        self._to_act_seat: Optional[int] = None
        self._last_raise_size: float = 1.0
        self._street_actions: int = 0  # 当前街行动次数
    
    def _generate_seed(self) -> str:
        """生成随机种子"""
        return hashlib.sha256(str(random.getrandbits(256)).encode()).hexdigest()[:16]
    
    def initialize_game(self) -> None:
        """初始化游戏 - 严格按照德州扑克规则"""
        # 首先确定庄家位置
        self.hero_seat = self.rng.randint(0, 5)
        
        # 庄家在 Hero 后面 0-2 个位置（模拟真实体验）
        btn_offset = self.rng.choices([0, 1, 2], weights=[0.5, 0.3, 0.2])[0]
        self.button_seat = (self.hero_seat - btn_offset) % 6
        self.sb_seat = (self.button_seat + 1) % 6
        self.bb_seat = (self.button_seat + 2) % 6
        
        # 根据庄家位置计算每个座位的位置名称
        # 6人桌顺序：UTG, MP, CO, BTN, SB, BB
        position_map = {}
        position_map[self.button_seat] = "BTN"
        position_map[self.sb_seat] = "SB"
        position_map[self.bb_seat] = "BB"
        
        # 其他位置：UTG 是 BB 的下一位，然后是 MP, CO
        utg_seat = (self.bb_seat + 1) % 6
        mp_seat = (self.bb_seat + 2) % 6
        co_seat = (self.bb_seat + 3) % 6
        position_map[utg_seat] = "UTG"
        position_map[mp_seat] = "MP"
        position_map[co_seat] = "CO"
        
        # 创建玩家
        self.players = []
        for seat in range(6):
            self.players.append(Player(
                seat=seat,
                position=position_map[seat],
                stack=float(self.stack_bb),
                is_hero=(seat == self.hero_seat),
            ))
        
        # 发牌（从 SB 的下一位开始发）
        self._deck = PokerDeck(self.seed)
        deal_start = (self.sb_seat + 1) % 6
        for i in range(6):
            seat = (deal_start + i) % 6
            self.players[seat].hole_cards = self._deck.deal(1)
        for i in range(6):
            seat = (deal_start + i) % 6
            self.players[seat].hole_cards.extend(self._deck.deal(1))
        
        # 放置盲注
        self._post_blinds()
        
        # 设置状态
        self.status = GameStatus.PREFLOP
        self.street = Street.PREFLOP
        self._to_act_seat = (self.bb_seat + 1) % 6  # UTG（BB 的下一位）
        self._update_active_players()
    
    def _post_blinds(self) -> None:
        """放置盲注"""
        sb_player = self.players[self.sb_seat]
        bb_player = self.players[self.bb_seat]
        
        # SB = 0.5 BB
        sb_amount = min(0.5, sb_player.stack)
        sb_player.stack -= sb_amount
        sb_player.committed_this_street = sb_amount
        sb_player.total_committed = sb_amount
        self.pot += sb_amount
        
        # BB = 1 BB
        bb_amount = min(1.0, bb_player.stack)
        bb_player.stack -= bb_amount
        bb_player.committed_this_street = bb_amount
        bb_player.total_committed = bb_amount
        self.pot += bb_amount
        
        self.current_bet = 1.0
        self._last_raise_size = 0.5
        
        # 记录行动
        self.action_log.append(Action(
            street="preflop",
            seat=self.sb_seat,
            position=self.players[self.sb_seat].position,
            action="sb",
            amount=sb_amount,
            pot_after=self.pot,
        ))
        self.action_log.append(Action(
            street="preflop",
            seat=self.bb_seat,
            position=self.players[self.bb_seat].position,
            action="bb",
            amount=bb_amount,
            pot_after=self.pot,
        ))
    
    def _update_active_players(self) -> None:
        """更新活跃玩家"""
        for p in self.players:
            p.is_active = p.in_hand and p.stack > 0
    
    def get_legal_actions(self, seat: Optional[int] = None) -> List[str]:
        """获取合法行动列表"""
        if seat is None:
            seat = self._to_act_seat
        
        if seat is None:
            return []
        
        player = self.players[seat]
        if not player.in_hand or not player.is_active:
            return []
        
        actions = []
        to_call = self.current_bet - player.committed_this_street
        
        # Fold: 有下注时可以弃牌
        if to_call > 0:
            actions.append("fold")
        
        # Check: 不需要跟注时可以过牌
        if to_call == 0:
            actions.append("check")
        
        # Call: 需要跟注且筹码足够
        if to_call > 0 and player.stack >= to_call:
            actions.append("call")
        
        # Bet: 没有下注时可以下注 (翻牌后)
        if to_call == 0 and self.street != Street.PREFLOP:
            actions.append("bet")
        
        # Raise: 有下注时可以加注
        if to_call > 0:
            # 最小加注
            min_raise = self.current_bet + self._last_raise_size
            if player.stack + player.committed_this_street >= min_raise:
                actions.append("raise")
        
        # All-in: 任何情况下都可以 all-in
        if player.stack > 0:
            actions.append("allin")
        
        return actions
    
    def calculate_bet_sizes(self) -> Dict[str, float]:
        """计算下注尺度 (33%, 75%, 125% pot)"""
        sizes = {}
        hero = self.players[self.hero_seat]
        
        # 计算底池大小
        pot_size = self.pot
        
        # 33% pot
        amount_33 = max(0.5, math.floor(pot_size * 0.33 * 2) / 2)
        # 75% pot
        amount_75 = max(0.5, math.floor(pot_size * 0.75 * 2) / 2)
        # 125% pot
        amount_125 = max(0.5, math.floor(pot_size * 1.25 * 2) / 2)
        
        # 如果是加注，需要计算到多少
        if self.current_bet > 0:
            to_call = self.current_bet - hero.committed_this_street
            amount_33 += to_call
            amount_75 += to_call
            amount_125 += to_call
        
        # 检查是否超过 stack
        if amount_33 >= hero.stack:
            sizes["bet33"] = hero.stack
        else:
            sizes["bet33"] = amount_33
            
        if amount_75 >= hero.stack:
            sizes["bet75"] = hero.stack
        else:
            sizes["bet75"] = amount_75
            
        if amount_125 >= hero.stack:
            sizes["bet125"] = hero.stack
        else:
            sizes["bet125"] = amount_125
        
        return sizes
    
    def is_hero_turn(self) -> bool:
        """是否轮到 Hero"""
        return self._to_act_seat == self.hero_seat
    
    def process_action(self, action: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """处理行动"""
        if self._to_act_seat is None:
            raise ValueError("No player to act")
        
        player = self.players[self._to_act_seat]
        legal = self.get_legal_actions()
        
        if action not in legal:
            raise ValueError(f"Illegal action: {action}. Legal: {legal}")
        
        to_call = self.current_bet - player.committed_this_street
        
        # 执行行动
        if action == "fold":
            player.in_hand = False
            player.is_active = False
        
        elif action == "check":
            pass  # 什么都不做
        
        elif action == "call":
            call_amount = min(to_call, player.stack)
            player.stack -= call_amount
            player.committed_this_street += call_amount
            player.total_committed += call_amount
            self.pot += call_amount
        
        elif action == "bet":
            if amount is None:
                raise ValueError("Bet requires amount")
            bet_amount = min(amount, player.stack)
            player.stack -= bet_amount
            player.committed_this_street += bet_amount
            player.total_committed += bet_amount
            self.pot += bet_amount
            self.current_bet = player.committed_this_street
            self._last_raise_size = bet_amount
        
        elif action == "raise":
            if amount is None:
                raise ValueError("Raise requires amount")
            raise_amount = min(amount, player.stack + player.committed_this_street)
            actual_raise = raise_amount - player.committed_this_street
            player.stack -= actual_raise
            player.committed_this_street = raise_amount
            player.total_committed += actual_raise
            self.pot += actual_raise
            self._last_raise_size = raise_amount - self.current_bet
            self.current_bet = raise_amount
        
        elif action == "allin":
            allin_amount = player.stack
            player.stack = 0
            player.committed_this_street += allin_amount
            player.total_committed += allin_amount
            self.pot += allin_amount
            if player.committed_this_street > self.current_bet:
                self._last_raise_size = player.committed_this_street - self.current_bet
                self.current_bet = player.committed_this_street
            player.is_active = False  # allin 后不能再行动
        
        # 记录行动
        self.action_log.append(Action(
            street=self.street.value,
            seat=self._to_act_seat,
            position=player.position,
            action=action,
            amount=amount if action in ["bet", "raise", "allin"] else None,
            pot_after=self.pot,
        ))
        
        self._street_actions += 1
        
        # 检查是否结束当前街
        result = self._check_street_end()
        
        return {
            "action_executed": True,
            "street_advanced": result.get("advanced", False),
            "game_ended": result.get("ended", False),
        }
    
    def _check_street_end(self) -> Dict[str, Any]:
        """检查是否结束当前街 - 严格按照德州扑克规则"""
        in_hand_players = [p for p in self.players if p.in_hand]
        active_players = [p for p in in_hand_players if p.is_active]
        
        # 如果只剩一个玩家，结束游戏
        if len(in_hand_players) == 1:
            self._end_game("fold")
            return {"ended": True}
        
        # 如果所有在游戏的玩家都已 ALL-IN，直接发完所有牌并摊牌
        if len(in_hand_players) > 0 and len(active_players) == 0:
            # 所有剩余玩家都 ALL-IN，快速进入摊牌
            self._fast_forward_to_showdown()
            return {"ended": True}
        
        # 检查是否所有活跃玩家都已匹配当前最高投注
        if active_players:
            all_matched = all(
                p.committed_this_street == self.current_bet 
                for p in active_players
            )
            
            # 所有人都跟注或 check 后，进入下一街
            if all_matched:
                # 确保每个人都至少有一次行动机会（除了已经 ALL-IN 的）
                acted_players = len([a for a in self.action_log if a.street == self.street.value])
                if acted_players >= len([p for p in in_hand_players if p.is_active or p.committed_this_street == self.current_bet]):
                    self._advance_street()
                    return {"advanced": True}
            
            # 找到下一个要行动的玩家
            next_seat = (self._to_act_seat + 1) % 6
            loop_count = 0
            while loop_count < 6:
                next_player = self.players[next_seat]
                if next_player.in_hand and next_player.is_active:
                    self._to_act_seat = next_seat
                    break
                next_seat = (next_seat + 1) % 6
                loop_count += 1
            else:
                # 没有下一个活跃玩家，结束当前街
                self._advance_street()
                return {"advanced": True}
        else:
            # 没有活跃玩家（都 allin 了），进入下一街
            self._advance_street()
            return {"advanced": True}
        
        return {"advanced": False}
    
    def _fast_forward_to_showdown(self) -> None:
        """所有玩家 ALL-IN，快速发完剩余公共牌并进入摊牌"""
        # 发完 flop（如果还没发）
        if self.street == Street.PREFLOP:
            self.street = Street.FLOP
            self.community_cards = self._deck.deal(3)
        
        # 发完 turn（如果还没发）
        if self.street == Street.FLOP:
            self.street = Street.TURN
            self.community_cards.extend(self._deck.deal(1))
        
        # 发完 river（如果还没发）
        if self.street == Street.TURN:
            self.street = Street.RIVER
            self.community_cards.extend(self._deck.deal(1))
        
        # 进入摊牌
        self.street = Street.SHOWDOWN
        self._end_game("showdown")
    
    def _advance_street(self) -> None:
        """进入下一街"""
        # 重置本街投入
        for p in self.players:
            p.committed_this_street = 0.0
        self.current_bet = 0.0
        self._street_actions = 0
        
        if self.street == Street.PREFLOP:
            self.street = Street.FLOP
            self.community_cards = self._deck.deal(3)
            self.status = GameStatus.FLOP_DECISION
            self._to_act_seat = self._get_first_to_act_flop()
        
        elif self.street == Street.FLOP:
            self.street = Street.TURN
            self.community_cards.extend(self._deck.deal(1))
            self._to_act_seat = self._get_first_to_act_postflop()
        
        elif self.street == Street.TURN:
            self.street = Street.RIVER
            self.community_cards.extend(self._deck.deal(1))
            self._to_act_seat = self._get_first_to_act_postflop()
        
        elif self.street == Street.RIVER:
            self.street = Street.SHOWDOWN
            self._end_game("showdown")
        
        self._update_active_players()
    
    def _get_first_to_act_flop(self) -> int:
        """翻牌后首先行动的玩家 (SB 或第一个未弃牌的玩家)"""
        # 简化：从 SB 开始
        for offset in range(6):
            seat = (self.sb_seat + offset) % 6
            if self.players[seat].in_hand:
                return seat
        return self.sb_seat
    
    def _get_first_to_act_postflop(self) -> int:
        """转牌/河牌后首先行动的玩家"""
        return self._get_first_to_act_flop()
    
    def _end_game(self, ended_by: str) -> None:
        """结束游戏"""
        self.ended_by = ended_by
        self.status = GameStatus.ENDED
        
        if ended_by == "fold":
            # 找到唯一的赢家
            winner = [p for p in self.players if p.in_hand][0]
            self.result_bb = winner.total_committed - self.players[self.hero_seat].total_committed
        else:
            # 摊牌 - 使用 treys 进行牌力比较
            hero = self.players[self.hero_seat]
            
            if not hero.in_hand:
                self.result_bb = -hero.total_committed
            elif not HAS_TREYS:
                # 没有 treys 库时使用简化逻辑
                self.result_bb = -hero.total_committed
            else:
                # 使用 treys 进行牌力评估
                evaluator = Evaluator()
                community_cards = [Card.new(c) for c in self.community_cards]
                
                # 评估每个玩家的牌力
                player_scores = {}
                for p in self.players:
                    if p.in_hand and p.hole_cards:
                        hole_cards = [Card.new(c) for c in p.hole_cards]
                        score = evaluator.evaluate(community_cards, hole_cards)
                        player_scores[p.seat] = score
                
                # 找到最佳牌力（分数越低越好）
                if player_scores:
                    best_score = min(player_scores.values())
                    winners = [seat for seat, score in player_scores.items() if score == best_score]
                    
                    hero_score = player_scores.get(self.hero_seat)
                    if hero_score is not None and hero_score == best_score:
                        # Hero 获胜
                        self.result_bb = self.pot - hero.total_committed
                    else:
                        # Hero 输了
                        self.result_bb = -hero.total_committed
                else:
                    self.result_bb = -hero.total_committed
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        hero = self.players[self.hero_seat]
        
        return {
            "status": self.status.value,
            "street": self.street.value,
            "players": [p.to_dict() for p in self.players],
            "button_seat": self.button_seat,
            "sb_seat": self.sb_seat,
            "bb_seat": self.bb_seat,
            "pot": round(self.pot, 2),
            "current_bet": round(self.current_bet, 2),
            "community_cards": self.community_cards,
            "to_act_seat": self._to_act_seat,
            "hero_seat": self.hero_seat,
            "hero_cards": hero.hole_cards or [],
            "min_raise_to": round(self.current_bet + self._last_raise_size, 2) if self.current_bet > 0 else 1.0,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "seed": self.seed,
            "status": self.status.value,
            "street": self.street.value,
            "players": [p.to_dict() for p in self.players],
            "button_seat": self.button_seat,
            "sb_seat": self.sb_seat,
            "bb_seat": self.bb_seat,
            "pot": self.pot,
            "current_bet": self.current_bet,
            "community_cards": self.community_cards,
            "action_log": [a.to_dict() for a in self.action_log],
            "hero_seat": self.hero_seat,
            "hero_cards": self.players[self.hero_seat].hole_cards if self.hero_seat is not None else None,
            "preflop_key_spot": self.preflop_key_spot.to_dict() if self.preflop_key_spot else None,
            "flop_key_spot": self.flop_key_spot.to_dict() if self.flop_key_spot else None,
            "result_bb": self.result_bb,
            "ended_by": self.ended_by,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FullHandEngine":
        """从字典反序列化"""
        engine = cls(stack_bb=data.get("stack_bb", 100), seed=data.get("seed"))
        engine.status = GameStatus(data.get("status", "INIT"))
        engine.street = Street(data.get("street", "preflop"))
        # ... 更多反序列化逻辑
        return engine
