"""
完整牌局模拟服务层
V1.1 新增
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import random
import hashlib

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.fullhand_session import FullHandSession, FullHandStats
from app.services.fullhand_engine import FullHandEngine, GameStatus, Street, HandEvaluator
from app.services.flop_strategy import FlopStrategyEngine
from app.services.gto_engine import get_gto_strategy

# 导入 treys 进行牌力评估
try:
    from treys import Card, Evaluator
    HAS_TREYS = True
except ImportError:
    HAS_TREYS = False


class FullHandService:
    """完整牌局服务"""
    
    # Free 用户每日额度
    FREE_DAILY_LIMIT = 10
    
    # 评级阈值
    GRADE_THRESHOLDS = {
        "PERFECT": 0.60,
        "ACCEPTABLE": 0.20,
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.flop_engine = FlopStrategyEngine()
    
    def can_start_session(self, user: User) -> tuple[bool, int]:
        """检查用户是否可以开始新局，返回 (是否可以, 剩余次数)"""
        if user.is_subscribed:
            return True, -1  # -1 表示无限
        
        # 检查今日已玩局数
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = self.db.query(FullHandSession).filter(
            FullHandSession.user_id == user.id,
            FullHandSession.created_at >= today
        ).count()
        
        remaining = max(0, self.FREE_DAILY_LIMIT - today_count)
        return remaining > 0, remaining
    
    def create_session(self, user: User, stack_bb: int = 100, 
                       replay_seed: Optional[str] = None) -> FullHandSession:
        """创建新牌局"""
        # 检查额度
        can_start, remaining = self.can_start_session(user)
        if not can_start:
            raise ValueError(f"Daily limit reached. Remaining: {remaining}")
        
        # 如果是重打，使用原 seed
        if replay_seed:
            seed = replay_seed
        else:
            seed = hashlib.sha256(
                f"{user.id}_{datetime.utcnow().timestamp()}_{random.getrandbits(32)}".encode()
            ).hexdigest()[:16]
        
        # 初始化引擎
        engine = FullHandEngine(stack_bb=stack_bb, seed=seed)
        engine.initialize_game()
        
        # 运行 AI 直到 Hero 的回合或翻牌
        self._run_ai_until_hero_turn(engine)
        
        # 创建会话
        session = FullHandSession(
            user_id=user.id,
            table_type="6max",
            stack_bb=stack_bb,
            ai_level="standard",
            hand_seed=seed,
            status=engine.status.value,
            current_street=engine.street.value,
            players=[p.to_dict() for p in engine.players],
            button_seat=engine.button_seat,
            sb_seat=engine.sb_seat,
            bb_seat=engine.bb_seat,
            pot=engine.pot,
            current_bet=engine.current_bet,
            community_cards=engine.community_cards,
            action_log=[a.to_dict() for a in engine.action_log],
            hero_seat=engine.hero_seat,
            hero_cards=engine.players[engine.hero_seat].hole_cards,
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def _run_ai_until_hero_turn(self, engine: FullHandEngine) -> None:
        """运行 AI 直到 Hero 的回合"""
        max_iterations = 50  # 防止无限循环
        
        for _ in range(max_iterations):
            if engine.status == GameStatus.ENDED:
                break
            
            if engine.is_hero_turn():
                break
            
            # AI 决策
            self._ai_act(engine)
            
            # 检查是否进入翻牌
            if engine.street == Street.FLOP and engine.status == GameStatus.FLOP_DECISION:
                break
        
        return
    
    def _ai_act(self, engine: FullHandEngine) -> None:
        """AI 执行动作"""
        seat = engine._to_act_seat
        if seat is None:
            return
        
        player = engine.players[seat]
        legal_actions = engine.get_legal_actions()
        
        if not legal_actions:
            return
        
        # 使用 GTO 策略决策 (简化版)
        action = self._ai_decision(engine, player, legal_actions)
        
        # 执行动作
        if action in ["bet", "raise"]:
            # AI 使用固定尺度
            if engine.street == Street.PREFLOP:
                if action == "raise":
                    engine.process_action(action, amount=2.5)
                else:
                    engine.process_action(action, amount=1.0)
            else:
                # 翻牌后使用 75% pot
                bet_sizes = engine.calculate_bet_sizes()
                engine.process_action(action, amount=bet_sizes.get("bet75", 1.0))
        else:
            engine.process_action(action)
    
    def _ai_decision(self, engine: FullHandEngine, player, legal_actions: List[str]) -> str:
        """AI 决策逻辑"""
        # 简化版：随机选择，但优先某些动作
        
        if engine.street == Street.PREFLOP:
            # 使用现有 GTO 策略
            gto = get_gto_strategy(engine.stack_bb)
            hand = HandEvaluator.format_hand(player.hole_cards)
            
            # 获取当前场景
            action_to_you = self._get_preflop_action_context(engine, player)
            
            # 获取策略
            try:
                strategy = gto.get_strategy(hand, player.position, action_to_you)
                # 选择最高频的动作
                best = max(strategy.items(), key=lambda x: x[1])[0]
                
                # 映射到合法动作
                action_map = {
                    "fold": "fold",
                    "call": "call",
                    "raise_2bb": "raise",
                    "raise_2.5bb": "raise",
                    "raise_3bb": "raise",
                    "limp": "call",
                    "check": "check",
                    "all_in": "allin",
                }
                
                mapped = action_map.get(best, "call")
                if mapped in legal_actions:
                    return mapped
            except Exception:
                pass
        
        # 默认策略
        if "check" in legal_actions:
            return "check"
        if "call" in legal_actions:
            return "call"
        if "fold" in legal_actions:
            return "fold"
        
        return legal_actions[0]
    
    def _get_preflop_action_context(self, engine: FullHandEngine, player) -> str:
        """获取翻前场景描述"""
        # 简化判断
        if engine.current_bet == 1.0:
            return "open"
        elif engine.current_bet <= 2.5:
            return "vs_raise_2.5bb"
        else:
            return "vs_raise_4bb"
    
    def process_hero_action(self, session_id: int, user: User, 
                           action: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """处理 Hero 行动"""
        session = self.db.query(FullHandSession).filter(
            FullHandSession.id == session_id,
            FullHandSession.user_id == user.id
        ).first()
        
        if not session:
            raise ValueError("Session not found")
        
        if session.status == "ENDED":
            raise ValueError("Game already ended")
        
        # 恢复引擎状态
        engine = self._restore_engine(session)
        
        # 检查是否是关键点
        is_key_spot = False
        key_spot_info = None
        
        if engine.is_hero_turn():
            # 记录关键点（如果是翻前或翻牌）
            if engine.street == Street.PREFLOP:
                pass  # 翻前关键点在行动后记录
            elif engine.street == Street.FLOP and engine.status == GameStatus.FLOP_DECISION:
                is_key_spot = True
                key_spot_info = self._prepare_flop_keyspot(engine)
        
        # 执行动作
        result = engine.process_action(action, amount)
        
        # 记录关键点结果
        if engine.street == Street.PREFLOP:
            self._record_preflop_keyspot(engine, action)
        elif engine.street == Street.FLOP and is_key_spot:
            self._record_flop_keyspot(engine, action, key_spot_info)
            # V1.1: Hero 完成翻牌决策后，进入快进
            engine.status = GameStatus.FAST_FORWARD
        
        # 继续运行 AI
        if not result.get("game_ended") and not result.get("street_advanced"):
            self._run_ai_until_hero_turn(engine)
        
        # 检查是否完成翻牌决策
        final_result = None
        review_payload = None
        
        if engine.status == GameStatus.FAST_FORWARD or engine.status == GameStatus.ENDED:
            # 执行快进
            self._fast_forward(engine)
            final_result = {
                "result_bb": round(engine.result_bb, 2),
                "ended_by": engine.ended_by,
            }
            review_payload = self._generate_review(engine, user)
            session.completed_at = datetime.utcnow()
        
        # 更新会话
        session.status = engine.status.value
        session.current_street = engine.street.value
        session.players = [p.to_dict() for p in engine.players]
        session.pot = engine.pot
        session.current_bet = engine.current_bet
        session.community_cards = engine.community_cards
        session.action_log = [a.to_dict() for a in engine.action_log]
        session.result_bb = engine.result_bb
        session.ended_by = engine.ended_by
        
        if engine.preflop_key_spot:
            session.preflop_key_spot = engine.preflop_key_spot.to_dict()
        if engine.flop_key_spot:
            session.flop_key_spot = engine.flop_key_spot.to_dict()
        
        self.db.commit()
        
        return {
            "state": engine.get_state(),
            "legal_actions": engine.get_legal_actions(),
            "is_key_spot": is_key_spot,
            "key_spot_info": key_spot_info,
            "final_result": final_result,
            "review_payload": review_payload,
        }
    
    def _restore_engine(self, session: FullHandSession) -> FullHandEngine:
        """从会话恢复引擎状态"""
        engine = FullHandEngine(stack_bb=session.stack_bb, seed=session.hand_seed)
        
        # 重新初始化
        engine.initialize_game()
        
        # 重放所有行动
        for action_dict in session.action_log:
            if action_dict["action"] in ["sb", "bb", "deal"]:
                continue
            
            seat = action_dict["seat"]
            engine._to_act_seat = seat
            
            action = action_dict["action"]
            amount = action_dict.get("amount")
            
            try:
                engine.process_action(action, amount)
            except ValueError:
                pass  # 可能已经结束了
        
        # 恢复关键点
        if session.preflop_key_spot:
            engine.preflop_key_spot = self._restore_keyspot(session.preflop_key_spot)
        if session.flop_key_spot:
            engine.flop_key_spot = self._restore_keyspot(session.flop_key_spot)
        
        return engine
    
    def _restore_keyspot(self, data: Dict) -> Any:
        """恢复关键点"""
        from app.services.fullhand_engine import KeySpot
        return KeySpot(**data)
    
    def _prepare_flop_keyspot(self, engine: FullHandEngine) -> Dict[str, Any]:
        """准备翻牌关键点信息"""
        hero = engine.players[engine.hero_seat]
        hero_hand = HandEvaluator.format_hand(hero.hole_cards)
        
        # 确定底池类型
        pot_type = self._determine_pot_type(engine)
        
        # 确定对手
        villain = self._get_villain(engine)
        villain_position = villain.position if villain else "BB"
        
        # 判断是否是 PFR
        is_pfr = self._is_pfr(engine, hero)
        
        # 判断 IP/OOP
        ip_oop = self._determine_ip_oop(hero.position, villain_position)
        
        # 计算 SPR
        spr = hero.stack / engine.pot if engine.pot > 0 else 10
        spr_bucket = self.flop_engine.calculate_spr_bucket(spr)
        
        # 分析牌面
        board_texture = self.flop_engine.analyze_board_texture(engine.community_cards)
        
        # 评估手牌桶
        hand_bucket = HandEvaluator.evaluate_hand_bucket(hero.hole_cards, engine.community_cards)
        
        # 生成 context_id
        context_id = self.flop_engine.get_context_id(
            pot_type, hero.position, villain_position, is_pfr
        )
        
        # 获取策略
        strategy = self.flop_engine.get_strategy(
            context_id, hand_bucket, spr_bucket, board_texture, is_pfr, ip_oop
        )
        
        # 确定合法动作
        legal_actions = engine.get_legal_actions()
        strategy_actions = list(strategy.keys())
        
        # 映射动作
        mapped_legal = self._map_legal_actions(legal_actions, engine)
        
        # 过滤策略只保留合法动作
        filtered_strategy = {k: v for k, v in strategy.items() if k in mapped_legal}
        if not filtered_strategy:
            filtered_strategy = {"check": 1.0} if "check" in mapped_legal else {"call": 1.0}
        
        # 归一化
        total = sum(filtered_strategy.values())
        filtered_strategy = {k: round(v/total, 2) for k, v in filtered_strategy.items()}
        
        return {
            "street": "flop",
            "context_id": context_id,
            "pot_type": pot_type,
            "ip_oop": ip_oop,
            "spr_bucket": spr_bucket,
            "board": engine.community_cards,
            "hero_hand": hero_hand,
            "hero_hand_bucket": hand_bucket,
            "legal_actions": mapped_legal,
            "strategy": filtered_strategy,
            "best_action": self.flop_engine.get_best_action(filtered_strategy),
        }
    
    def _map_legal_actions(self, legal_actions: List[str], engine: FullHandEngine) -> List[str]:
        """将引擎合法动作映射到策略动作"""
        mapped = []
        
        for action in legal_actions:
            if action == "fold":
                mapped.append("fold")
            elif action == "check":
                mapped.append("check")
            elif action == "call":
                mapped.append("call")
            elif action == "bet":
                bet_sizes = engine.calculate_bet_sizes()
                mapped.extend(["bet33", "bet75", "bet125"])
            elif action == "raise":
                mapped.extend(["raise75", "raise125"])
            elif action == "allin":
                mapped.append("allin")
        
        return list(set(mapped))
    
    def _determine_pot_type(self, engine: FullHandEngine) -> str:
        """确定底池类型"""
        # 简化：根据行动次数判断
        preflop_raises = sum(1 for a in engine.action_log 
                           if a.street == "preflop" and a.action in ["raise", "bet"])
        
        if preflop_raises >= 3:
            return "4BP"
        elif preflop_raises == 2:
            return "3BP"
        else:
            return "SRP"
    
    def _get_villain(self, engine: FullHandEngine) -> Optional[Any]:
        """获取对手"""
        for p in engine.players:
            if p.in_hand and not p.is_hero:
                return p
        return None
    
    def _is_pfr(self, engine: FullHandEngine, hero) -> bool:
        """判断 Hero 是否是翻前进攻方"""
        # 简化：检查 Hero 是否在翻前有加注
        hero_raises = [a for a in engine.action_log 
                      if a.street == "preflop" and a.seat == hero.seat 
                      and a.action in ["raise", "bet"]]
        return len(hero_raises) > 0
    
    def _determine_ip_oop(self, hero_pos: str, villain_pos: str) -> str:
        """判断 IP/OOP"""
        order = {"UTG": 0, "MP": 1, "CO": 2, "BTN": 3, "SB": 4, "BB": 5}
        return "IP" if order[hero_pos] < order[villain_pos] else "OOP"
    
    def _record_preflop_keyspot(self, engine: FullHandEngine, action: str) -> None:
        """记录翻前关键点"""
        # 简化版：只记录主要决策点
        hero = engine.players[engine.hero_seat]
        
        # 只有在 facing raise 时才记录
        facing_raise = any(a.action in ["raise", "bet"] and a.seat != hero.seat
                         for a in engine.action_log if a.street == "preflop")
        
        if facing_raise:
            from app.services.fullhand_engine import KeySpot
            
            gto = get_gto_strategy(engine.stack_bb)
            hand = HandEvaluator.format_hand(hero.hole_cards)
            action_to_you = self._get_preflop_action_context(engine, hero)
            
            strategy = gto.get_strategy(hand, hero.position, action_to_you)
            best = gto.get_best_action(hand, hero.position, action_to_you)
            
            # 映射用户动作
            action_map = {"fold": "fold", "call": "call", "raise": "raise"}
            user_action_mapped = action_map.get(action, "fold")
            
            prob = strategy.get(user_action_mapped, 0)
            grade = self._calculate_grade(prob)
            
            engine.preflop_key_spot = KeySpot(
                street="preflop",
                context_id=f"PREFLOP_{action_to_you}_{hero.position}",
                hero_hand=hand,
                legal_actions=["fold", "call", "raise"],
                strategy=strategy,
                user_action=user_action_mapped,
                user_action_prob=prob,
                best_action=best,
                grade=grade,
            )
    
    def _record_flop_keyspot(self, engine: FullHandEngine, action: str, 
                            key_spot_info: Dict) -> None:
        """记录翻牌关键点"""
        from app.services.fullhand_engine import KeySpot
        
        strategy = key_spot_info.get("strategy", {})
        
        # 映射用户动作到策略动作
        user_action_mapped = self._map_user_action(action)
        
        prob = strategy.get(user_action_mapped, 0)
        grade = self._calculate_grade(prob)
        
        # 获取解释
        explanation = self.flop_engine.get_explanation(
            key_spot_info.get("hero_hand_bucket", "air"),
            "CBET" in key_spot_info.get("context_id", ""),
            self.flop_engine.analyze_board_texture(key_spot_info.get("board", [])),
            key_spot_info.get("best_action", "check")
        )
        
        engine.flop_key_spot = KeySpot(
            street="flop",
            context_id=key_spot_info["context_id"],
            pot_type=key_spot_info.get("pot_type"),
            ip_oop=key_spot_info.get("ip_oop"),
            spr_bucket=key_spot_info.get("spr_bucket"),
            board=key_spot_info.get("board"),
            hero_hand=key_spot_info.get("hero_hand"),
            hero_hand_bucket=key_spot_info.get("hero_hand_bucket"),
            legal_actions=key_spot_info.get("legal_actions", []),
            strategy=strategy,
            user_action=user_action_mapped,
            user_action_prob=prob,
            best_action=key_spot_info.get("best_action"),
            grade=grade,
        )
        
        # 保存解释
        engine.flop_key_spot.explanation = explanation
    
    def _map_user_action(self, action: str, amount: Optional[float] = None) -> str:
        """映射用户动作到策略动作"""
        if action == "fold":
            return "fold"
        elif action == "check":
            return "check"
        elif action == "call":
            return "call"
        elif action == "bet":
            if amount:
                if amount <= 0.4:
                    return "bet33"
                elif amount <= 0.9:
                    return "bet75"
                else:
                    return "bet125"
            return "bet75"
        elif action == "raise":
            return "raise75"
        elif action == "allin":
            return "allin"
        return action
    
    def _calculate_grade(self, prob: float) -> str:
        """计算评级"""
        if prob >= self.GRADE_THRESHOLDS["PERFECT"]:
            return "PERFECT"
        elif prob >= self.GRADE_THRESHOLDS["ACCEPTABLE"]:
            return "ACCEPTABLE"
        else:
            return "WRONG"
    
    def _fast_forward(self, engine: FullHandEngine) -> None:
        """快进执行 Turn/River"""
        # 简化版：随机决定胜负
        hero = engine.players[engine.hero_seat]
        
        if not hero.in_hand:
            engine._end_game("fold")
            return
        
        # 发出转牌和河牌
        if engine.street == Street.FLOP:
            engine._advance_street()  # 到 Turn
        if engine.street == Street.TURN:
            engine._advance_street()  # 到 River
        
        # 摊牌
        engine._end_game("showdown")
    
    def _generate_review(self, engine: FullHandEngine, user: User) -> Dict[str, Any]:
        """生成复盘数据 - 包含摊牌分析"""
        review = {
            "result_bb": round(engine.result_bb, 2) if engine.result_bb is not None else 0.0,
            "ended_by": engine.ended_by or "in_progress",
            "preflop_spot": None,
            "flop_spot": None,
            "showdown_analysis": None,
        }
        
        # 翻前关键点
        if engine.preflop_key_spot:
            spot = engine.preflop_key_spot
            review["preflop_spot"] = {
                "context_id": spot.context_id,
                "strategy": spot.strategy if user.is_subscribed else None,
                "user_action": spot.user_action,
                "user_action_prob": spot.user_action_prob if user.is_subscribed else None,
                "best_action": spot.best_action,
                "grade": spot.grade,
            }
        
        # 翻牌关键点
        if engine.flop_key_spot:
            spot = engine.flop_key_spot
            review["flop_spot"] = {
                "context_id": spot.context_id,
                "pot_type": spot.pot_type,
                "ip_oop": spot.ip_oop,
                "spr_bucket": spot.spr_bucket,
                "board": spot.board,
                "hero_hand": spot.hero_hand,
                "hero_hand_bucket": spot.hero_hand_bucket,
                "strategy": spot.strategy if user.is_subscribed else None,
                "legal_actions": spot.legal_actions,
                "user_action": spot.user_action,
                "user_action_prob": spot.user_action_prob if user.is_subscribed else None,
                "best_action": spot.best_action,
                "grade": spot.grade,
                "explanation": getattr(spot, 'explanation', ''),
            }
        
        # 添加摊牌分析
        review["showdown_analysis"] = self._analyze_showdown_from_engine(engine)
        
        return review
    
    def _analyze_showdown_from_engine(self, engine: FullHandEngine) -> Dict[str, Any]:
        """从引擎状态分析摊牌结果"""
        analysis = {
            "community_cards": engine.community_cards or [],
            "pot": engine.pot or 0,
            "players": [],
            "winner_analysis": None,
            "explanation": "",
        }
        
        if not engine.players:
            return analysis
        
        # 使用 treys 评估牌力
        can_evaluate = (HAS_TREYS and 
                       engine.community_cards and 
                       len(engine.community_cards) == 5)
        
        if can_evaluate:
            try:
                evaluator = Evaluator()
                board_cards = [Card.new(c) for c in engine.community_cards if len(c) == 2]
                
                if len(board_cards) == 5:
                    player_results = []
                    for p in engine.players:
                        if not p.hole_cards:
                            continue
                        
                        hole_cards = [Card.new(c) for c in p.hole_cards if len(c) == 2]
                        if len(hole_cards) == 2:
                            score = evaluator.evaluate(board_cards, hole_cards)
                            hand_rank = evaluator.get_rank_class(score)
                            hand_name = evaluator.class_to_string(hand_rank)
                        else:
                            score = 9999
                            hand_name = "未知"
                        
                        player_result = {
                            "seat": p.seat,
                            "position": p.position,
                            "hole_cards": p.hole_cards,
                            "is_hero": p.is_hero,
                            "in_hand": p.in_hand,
                            "total_committed": p.total_committed,
                            "score": score,
                            "hand_name": hand_name,
                            "is_winner": False,
                        }
                        player_results.append(player_result)
                    
                    # 确定赢家
                    if player_results:
                        in_hand_results = [pr for pr in player_results if pr["in_hand"]]
                        if in_hand_results:
                            winner = min(in_hand_results, key=lambda x: x["score"])
                            winner["is_winner"] = True
                            
                            analysis["winner_analysis"] = {
                                "position": winner["position"],
                                "hand_name": winner["hand_name"],
                                "hole_cards": winner["hole_cards"],
                            }
                    
                    analysis["players"] = sorted(player_results, key=lambda x: (not x["in_hand"], x["score"]))
            except Exception as e:
                print(f"Error in showdown analysis: {e}")
        
        # 无法评估时的简化显示
        if not analysis["players"]:
            for p in engine.players:
                analysis["players"].append({
                    "seat": p.seat,
                    "position": p.position,
                    "hole_cards": p.hole_cards or [],
                    "is_hero": p.is_hero,
                    "in_hand": p.in_hand,
                    "total_committed": p.total_committed,
                    "score": 9999,
                    "hand_name": "未知" if p.in_hand else "弃牌",
                    "is_winner": False,
                })
        
        # 生成解释文字
        analysis["explanation"] = self._generate_explanation_from_engine(analysis, engine)
        
        return analysis
    
    def _generate_explanation_from_engine(self, analysis: Dict, engine: FullHandEngine) -> str:
        """从引擎生成解释文字"""
        players = analysis.get("players", [])
        hero = next((p for p in players if p.get("is_hero")), None)
        winner = next((p for p in players if p.get("is_winner")), None)
        
        if not hero:
            return "无法获取 Hero 信息"
        
        if engine.ended_by == "fold":
            return f"本局通过弃牌结束。你在本局投入了 {hero.get('total_committed', 0):.1f} BB。"
        
        if not hero.get("in_hand"):
            return f"你在摊牌前弃牌，失去了底池。本局投入了 {hero.get('total_committed', 0):.1f} BB。"
        
        hero_hand = hero.get("hand_name", "未知")
        
        if winner and winner.get("is_hero"):
            other_players = [p for p in players if p.get("in_hand") and not p.get("is_hero")]
            if other_players:
                best_opponent = min(other_players, key=lambda x: x.get("score", 9999))
                return f"🎉 恭喜你获胜！你的 {hero_hand} 击败了对手的 {best_opponent.get('hand_name', '未知')}。赢得 {engine.pot:.1f} BB！"
            return f"🎉 恭喜你获胜！你的 {hero_hand} 是最大牌。赢得 {engine.pot:.1f} BB！"
        elif winner:
            winner_hand = winner.get("hand_name", "未知")
            winner_pos = winner.get("position", "对手")
            
            explanation = f"😔 你输了。你的 {hero_hand} 不敌 {winner_pos} 的 {winner_hand}。\n\n"
            explanation += f"📊 详细对比:\n"
            explanation += f"  你: {hero.get('hole_cards', [])} → {hero_hand}\n"
            explanation += f"  {winner_pos}: {winner.get('hole_cards', [])} → {winner_hand}\n"
            explanation += f"  公共牌: {analysis.get('community_cards', [])}\n\n"
            explanation += f"💰 你投入了 {hero.get('total_committed', 0):.1f} BB，本局损失 {abs(engine.result_bb or 0):.1f} BB。"
            return explanation
        
        return "摊牌结果分析中..."
    
    def get_review(self, session_id: int, user: User) -> Dict[str, Any]:
        """获取复盘 - 增强版，包含详细牌局分析"""
        session = self.db.query(FullHandSession).filter(
            FullHandSession.id == session_id,
            FullHandSession.user_id == user.id
        ).first()
        
        if not session:
            raise ValueError("Session not found")
        
        # 生成复盘（直接使用数据库中的数据）
        review = {
            "hand_id": session_id,
            "result_bb": round(session.result_bb, 2) if session.result_bb is not None else 0.0,
            "ended_by": session.ended_by or "in_progress",
            "action_log": session.action_log,
            "can_replay": user.is_subscribed,
            "preflop_spot": None,
            "flop_spot": None,
        }
        
        # 添加详细牌局分析
        showdown_analysis = self._analyze_showdown(session)
        review["showdown_analysis"] = showdown_analysis
        
        # 翻前关键点
        if session.preflop_key_spot:
            spot = session.preflop_key_spot
            review["preflop_spot"] = {
                "context_id": spot.get("context_id"),
                "strategy": spot.get("strategy") if user.is_subscribed else None,
                "user_action": spot.get("user_action"),
                "user_action_prob": spot.get("user_action_prob") if user.is_subscribed else None,
                "best_action": spot.get("best_action"),
                "grade": spot.get("grade"),
            }
        
        # 翻牌关键点
        if session.flop_key_spot:
            spot = session.flop_key_spot
            review["flop_spot"] = {
                "context_id": spot.get("context_id"),
                "pot_type": spot.get("pot_type"),
                "ip_oop": spot.get("ip_oop"),
                "spr_bucket": spot.get("spr_bucket"),
                "board": spot.get("board"),
                "hero_hand": spot.get("hero_hand"),
                "hero_hand_bucket": spot.get("hero_hand_bucket"),
                "strategy": spot.get("strategy") if user.is_subscribed else None,
                "legal_actions": spot.get("legal_actions"),
                "user_action": spot.get("user_action"),
                "user_action_prob": spot.get("user_action_prob") if user.is_subscribed else None,
                "best_action": spot.get("best_action"),
                "grade": spot.get("grade"),
                "explanation": spot.get("explanation", ""),
            }
        
        return review
    
    def _analyze_showdown(self, session: FullHandSession) -> Dict[str, Any]:
        """分析摊牌结果，返回详细的牌局分析 - 使用 seed 重新生成完整游戏状态"""
        analysis = {
            "community_cards": session.community_cards or [],
            "pot": session.pot or 0,
            "players": [],
            "hero_analysis": None,
            "winner_analysis": None,
            "explanation": "",
        }
        
        if not session.players or not session.hand_seed:
            return analysis
        
        # 使用相同的 seed 重新初始化引擎来获取完整游戏状态
        try:
            engine = FullHandEngine(stack_bb=session.stack_bb, seed=session.hand_seed)
            engine.initialize_game()
            
            # 重放所有行动到结束
            for action_dict in session.action_log or []:
                if action_dict["action"] not in ["sb", "bb"]:
                    engine._to_act_seat = action_dict["seat"]
                    try:
                        engine.process_action(action_dict["action"], action_dict.get("amount"))
                    except:
                        pass
            
            # 如果 action log 不完整（游戏已结束但引擎还没结束），自动完成游戏
            if session.ended_by and not engine.ended_by:
                # 自动 check 到摊牌
                max_steps = 20
                step = 0
                while engine.street.value not in ["showdown", "ENDED"] and step < max_steps:
                    legal = engine.get_legal_actions(engine._to_act_seat)
                    if not legal:
                        break
                    if "check" in legal:
                        engine.process_action("check")
                    elif "call" in legal:
                        engine.process_action("call")
                    else:
                        engine.process_action("fold")
                    step += 1
            
            # 获取完整玩家信息（包括所有手牌）
            players_data = []
            for p in engine.players:
                players_data.append({
                    "seat": p.seat,
                    "position": p.position,
                    "hole_cards": p.hole_cards,
                    "is_hero": p.is_hero,
                    "in_hand": p.in_hand,
                    "total_committed": p.total_committed,
                })
            
            analysis["community_cards"] = engine.community_cards
            analysis["pot"] = engine.pot
        except Exception as e:
            print(f"Error replaying game: {e}")
            # 回退到数据库中的数据
            players_data = session.players if isinstance(session.players, list) else []
        
        # 使用 treys 评估牌力（需要完整 5 张公共牌）
        can_evaluate = (HAS_TREYS and 
                       analysis["community_cards"] and 
                       len(analysis["community_cards"]) == 5)
        
        if can_evaluate:
            try:
                evaluator = Evaluator()
                board_cards = [Card.new(c) for c in analysis["community_cards"] if len(c) == 2]
                
                if len(board_cards) == 5:
                    player_results = []
                    for p in players_data:
                        if not p.get("hole_cards"):
                            continue
                        
                        hole_cards = [Card.new(c) for c in p["hole_cards"] if len(c) == 2]
                        if len(hole_cards) == 2:
                            score = evaluator.evaluate(board_cards, hole_cards)
                            hand_rank = evaluator.get_rank_class(score)
                            hand_name = evaluator.class_to_string(hand_rank)
                        else:
                            score = 9999
                            hand_name = "未知"
                        
                        player_result = {
                            "seat": p.get("seat"),
                            "position": p.get("position"),
                            "hole_cards": p.get("hole_cards"),
                            "is_hero": p.get("is_hero", False),
                            "in_hand": p.get("in_hand", False),
                            "total_committed": p.get("total_committed", 0),
                            "score": score,
                            "hand_name": hand_name,
                            "is_winner": False,
                        }
                        player_results.append(player_result)
                    
                    # 确定赢家
                    if player_results:
                        in_hand_results = [pr for pr in player_results if pr["in_hand"]]
                        if in_hand_results:
                            winner = min(in_hand_results, key=lambda x: x["score"])
                            winner["is_winner"] = True
                            
                            analysis["winner_analysis"] = {
                                "position": winner["position"],
                                "hand_name": winner["hand_name"],
                                "hole_cards": winner["hole_cards"],
                            }
                    
                    analysis["players"] = sorted(player_results, key=lambda x: (not x["in_hand"], x["score"]))
                else:
                    can_evaluate = False
            except Exception as e:
                print(f"Error in showdown analysis: {e}")
                can_evaluate = False
        
        # 无法评估时的简化显示
        if not analysis["players"]:
            analysis["players"] = []
            for p in players_data:
                analysis["players"].append({
                    "seat": p.get("seat"),
                    "position": p.get("position"),
                    "hole_cards": p.get("hole_cards") or [],
                    "is_hero": p.get("is_hero", False),
                    "in_hand": p.get("in_hand", False),
                    "total_committed": p.get("total_committed", 0),
                    "score": 9999,
                    "hand_name": "未知" if p.get("in_hand") else "弃牌",
                    "is_winner": False,
                })
        
        # 生成解释文字
        analysis["explanation"] = self._generate_explanation(analysis, session)
        
        return analysis
    
    def _generate_explanation(self, analysis: Dict, session: FullHandSession) -> str:
        """生成输赢解释文字"""
        players = analysis.get("players", [])
        hero = next((p for p in players if p.get("is_hero")), None)
        winner = next((p for p in players if p.get("is_winner")), None)
        
        if not hero:
            return "无法获取 Hero 信息"
        
        if session.ended_by == "fold":
            return f"本局通过弃牌结束。你在本局投入了 {hero.get('total_committed', 0):.1f} BB。"
        
        if not hero.get("in_hand"):
            return f"你在摊牌前弃牌，失去了底池。本局投入了 {hero.get('total_committed', 0):.1f} BB。"
        
        hero_hand = hero.get("hand_name", "未知")
        
        if winner and winner.get("is_hero"):
            # Hero 获胜
            other_players = [p for p in players if p.get("in_hand") and not p.get("is_hero")]
            if other_players:
                best_opponent = min(other_players, key=lambda x: x.get("score", 9999))
                return f"🎉 恭喜你获胜！你的 {hero_hand} 击败了对手的 {best_opponent.get('hand_name', '未知')}。赢得 {session.pot:.1f} BB！"
            return f"🎉 恭喜你获胜！你的 {hero_hand} 是最大牌。赢得 {session.pot:.1f} BB！"
        elif winner:
            # Hero 输了
            winner_hand = winner.get("hand_name", "未知")
            winner_cards = winner.get("hole_cards", [])
            winner_pos = winner.get("position", "对手")
            
            explanation = f"😔 你输了。你的 {hero_hand} 不敌 {winner_pos} 的 {winner_hand}。\n\n"
            explanation += f"📊 详细对比:\n"
            explanation += f"  你: {hero.get('hole_cards', [])} → {hero_hand}\n"
            explanation += f"  {winner_pos}: {winner_cards} → {winner_hand}\n"
            explanation += f"  公共牌: {analysis.get('community_cards', [])}\n\n"
            explanation += f"💰 你投入了 {hero.get('total_committed', 0):.1f} BB，本局损失 {abs(session.result_bb or 0):.1f} BB。"
            return explanation
        
        return "摊牌结果分析中..."
    
    def replay_hand(self, session_id: int, user: User) -> FullHandSession:
        """重打同一手"""
        if not user.is_subscribed:
            raise ValueError("Replay is a Pro feature")
        
        session = self.db.query(FullHandSession).filter(
            FullHandSession.id == session_id,
            FullHandSession.user_id == user.id
        ).first()
        
        if not session:
            raise ValueError("Session not found")
        
        # 使用相同 seed 创建新会话
        return self.create_session(user, session.stack_bb, replay_seed=session.hand_seed)
    
    def get_stats(self, user: User) -> Dict[str, Any]:
        """获取统计"""
        # 总体统计
        total_hands = self.db.query(FullHandSession).filter(
            FullHandSession.user_id == user.id,
            FullHandSession.status == "ENDED"
        ).count()
        
        total_result = self.db.query(FullHandSession).filter(
            FullHandSession.user_id == user.id,
            FullHandSession.status == "ENDED"
        ).all()
        
        total_bb = sum(s.result_bb or 0 for s in total_result)
        avg_bb = total_bb / total_hands if total_hands > 0 else 0
        
        # 今日统计
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_hands = self.db.query(FullHandSession).filter(
            FullHandSession.user_id == user.id,
            FullHandSession.created_at >= today
        ).count()
        
        remaining = -1 if user.is_subscribed else max(0, self.FREE_DAILY_LIMIT - today_hands)
        
        return {
            "total_hands": total_hands,
            "total_result_bb": round(total_bb, 2),
            "avg_result_bb": round(avg_bb, 2),
            "preflop_accuracy": None,  # 可从数据库计算
            "flop_accuracy": None,
            "today_hands": today_hands,
            "today_remaining": remaining,
            "is_pro": user.is_subscribed,
        }
