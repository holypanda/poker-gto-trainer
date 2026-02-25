import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { fullhandApi } from '../services/fullhandApi';
import { useAuthStore } from '../store/authStore';
import { useMobile } from '../hooks/useMobile';
import {
  FullHandSession,
  FullHandActResponse,
  FullHandReview,
  FullHandStats,
  GameState,
  PlayerState,
  KeySpotInfo,
  ACTION_LABELS,
  POSITION_COLORS,
  GRADE_COLORS,
  GRADE_ICONS,
  BetSizes,
  Grade,
} from '../types/fullhand';
import toast from 'react-hot-toast';

// 牌桌座位配置 (6max)
const SEAT_POSITIONS = [
  { seat: 0, top: '10%', left: '50%', label: 'top' },    // UTG
  { seat: 1, top: '30%', left: '85%', label: 'right' },  // MP
  { seat: 2, top: '70%', left: '85%', label: 'right' },  // CO
  { seat: 3, top: '90%', left: '50%', label: 'bottom' }, // BTN
  { seat: 4, top: '70%', left: '15%', label: 'left' },   // SB
  { seat: 5, top: '30%', left: '15%', label: 'left' },   // BB
];

const FullHand: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { isMobile } = useMobile();

  // 配置状态
  const [config, setConfig] = useState({
    stackBB: 100,
    tableType: '6max',
    aiLevel: 'standard',
  });

  // 游戏状态
  const [session, setSession] = useState<FullHandSession | null>(null);
  const [review, setReview] = useState<FullHandReview | null>(null);
  const [stats, setStats] = useState<FullHandStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [betSizes, setBetSizes] = useState<BetSizes | null>(null);
  const [showBetPanel, setShowBetPanel] = useState(false);
  const [pendingAction, setPendingAction] = useState<string | null>(null);

  // 加载统计
  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await fullhandApi.getStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  // 开始新局
  const startGame = async () => {
    if (!user) {
      toast.error('请先登录');
      return;
    }

    // 检查额度
    if (stats && !stats.is_pro && stats.today_remaining <= 0) {
      toast.error('今日免费局数已用完，请订阅 VIP');
      return;
    }

    setLoading(true);
    setReview(null);

    try {
      const session = await fullhandApi.start({
        table_type: config.tableType,
        stack_bb: config.stackBB,
        ai_level: config.aiLevel,
      });

      setSession(session);

      // 如果已经是关键点，显示提示
      if (session.is_key_spot && session.key_spot_info) {
        toast.success('进入翻牌关键点！');
      }

      // 检查是否需要自动行动（AI 回合）
      checkAndRunAI(session);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '开始游戏失败');
    } finally {
      setLoading(false);
    }
  };

  // 检查并运行 AI
  const checkAndRunAI = async (currentSession: FullHandSession) => {
    const state = currentSession.state;
    if (state.to_act_seat !== state.hero_seat) {
      // AI 回合，自动执行
      setTimeout(async () => {
        try {
          const result = await fullhandApi.act({
            hand_id: currentSession.hand_id,
            action: 'check', // AI 会自动决定
          });
          handleActionResult(result);
        } catch (error: any) {
          toast.error(error.response?.data?.detail || 'AI 行动失败');
        }
      }, 500);
    }
  };

  // 执行动作
  const executeAction = async (action: string, amount?: number) => {
    if (!session) return;

    setLoading(true);
    setShowBetPanel(false);
    setPendingAction(null);

    try {
      const result = await fullhandApi.act({
        hand_id: session.hand_id,
        action,
        amount,
      });

      handleActionResult(result);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '执行动作失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理动作结果
  const handleActionResult = (result: FullHandActResponse) => {
    if (!session) return;

    // 更新状态
    const newSession: FullHandSession = {
      ...session,
      state: result.state,
      legal_actions: result.legal_actions,
      is_key_spot: result.is_key_spot,
      key_spot_info: result.key_spot_info,
    };

    setSession(newSession);

    // 检查游戏是否结束
    if (result.final_result) {
      // 显示结果
      const bb = result.final_result.result_bb;
      if (bb > 0) {
        toast.success(`赢得 ${bb.toFixed(1)} BB!`);
      } else if (bb < 0) {
        toast.error(`失去 ${Math.abs(bb).toFixed(1)} BB`);
      } else {
        toast('平局');
      }

      // 加载复盘
      if (result.review_payload) {
        setReview(result.review_payload);
        loadStats(); // 刷新统计
      }
      return;
    }

    // 如果进入关键点，提示
    if (result.is_key_spot && result.key_spot_info) {
      toast.success('进入翻牌关键点！');
    }

    // 如果不是 Hero 回合，自动运行 AI
    if (result.state.to_act_seat !== result.state.hero_seat) {
      checkAndRunAI(newSession);
    }
  };

  // 计算下注尺度
  useEffect(() => {
    if (session && session.state.pot > 0) {
      const pot = session.state.pot;
      const toCall = session.state.current_bet - 
        (session.state.players.find(p => p.is_hero)?.committed_this_street || 0);

      const calcSize = (scale: number) => {
        let amount = pot * scale;
        amount = Math.floor(amount * 2) / 2; // 取整到 0.5
        return Math.max(0.5, amount + (toCall > 0 ? toCall : 0));
      };

      setBetSizes({
        bet33: calcSize(0.33),
        bet75: calcSize(0.75),
        bet125: calcSize(1.25),
      });
    }
  }, [session?.state.pot, session?.state.current_bet]);

  // 重打同一手
  const replayHand = async () => {
    if (!review || !review.can_replay) {
      toast.error('重打功能需要 Pro 订阅');
      return;
    }

    setLoading(true);
    try {
      const newSession = await fullhandApi.replay(review.hand_id);
      setReview(null);
      setSession(newSession);
      toast.success('开始重打同一手！');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '重打失败');
    } finally {
      setLoading(false);
    }
  };

  // 格式化手牌显示
  const formatCard = (card: string) => {
    const rank = card[0];
    const suit = card[1];
    const suitColors: Record<string, string> = {
      's': 'text-gray-400', // 黑桃
      'h': 'text-red-400',  // 红桃
      'd': 'text-blue-400', // 方块
      'c': 'text-green-400', // 梅花
    };
    const suitSymbols: Record<string, string> = {
      's': '♠',
      'h': '♥',
      'd': '♦',
      'c': '♣',
    };
    return (
      <span className={`font-bold ${suitColors[suit]}`}>
        {rank}{suitSymbols[suit]}
      </span>
    );
  };

  // 获取玩家位置样式
  const getPlayerPosition = (seat: number) => {
    const pos = SEAT_POSITIONS.find(p => p.seat === seat);
    return pos || { top: '50%', left: '50%' };
  };

  // 渲染配置界面
  if (!session && !review) {
    return (
      <div className={`max-w-2xl mx-auto ${isMobile ? 'px-2' : ''}`}>
        <h1 className={`font-bold text-white mb-4 md:mb-6 ${isMobile ? 'text-xl' : 'text-2xl'}`}>
          完整牌局模拟
        </h1>

        {/* 统计卡片 */}
        {stats && (
          <div className="bg-gray-800 rounded-xl p-4 mb-4">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-blue-400">{stats.total_hands}</div>
                <div className="text-xs text-gray-400">总局数</div>
              </div>
              <div>
                <div className={`text-2xl font-bold ${stats.total_result_bb >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {stats.total_result_bb >= 0 ? '+' : ''}{stats.total_result_bb.toFixed(1)}
                </div>
                <div className="text-xs text-gray-400">总盈亏 (BB)</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-yellow-400">
                  {stats.is_pro ? '∞' : stats.today_remaining}
                </div>
                <div className="text-xs text-gray-400">今日剩余</div>
              </div>
            </div>
          </div>
        )}

        {/* 配置面板 */}
        <div className="bg-gray-800 rounded-xl p-4 md:p-6 space-y-4 md:space-y-6">
          {/* 筹码深度 */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2 md:mb-3">
              筹码深度 (BB)
            </label>
            <div className="grid grid-cols-2 gap-2 md:gap-3">
              {[50, 100].map((size) => (
                <button
                  key={size}
                  onClick={() => setConfig({ ...config, stackBB: size })}
                  className={`py-2 md:py-3 px-3 md:px-4 rounded-lg font-medium transition-colors ${
                    config.stackBB === size
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {size} BB
                </button>
              ))}
            </div>
          </div>

          {/* AI 难度 */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2 md:mb-3">
              AI 难度
            </label>
            <select
              value={config.aiLevel}
              onChange={(e) => setConfig({ ...config, aiLevel: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 md:px-4 py-2 md:py-3 text-white text-sm md:text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="standard">标准 (GTO 策略)</option>
            </select>
          </div>

          {/* 开始按钮 */}
          <button
            onClick={startGame}
            disabled={loading || (!stats?.is_pro && stats?.today_remaining === 0)}
            className="w-full py-3 md:py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-bold text-base md:text-lg rounded-lg transition-colors"
          >
            {loading ? '准备中...' : stats?.is_pro ? '开始一局' : stats?.today_remaining === 0 ? '今日额度已用完' : '开始一局'}
          </button>
        </div>
      </div>
    );
  }

  // 渲染复盘界面
  if (review) {
    return (
      <div className={`max-w-2xl mx-auto ${isMobile ? 'px-2' : ''}`}>
        <h1 className={`font-bold text-white mb-4 md:mb-6 ${isMobile ? 'text-xl' : 'text-2xl'}`}>
          牌局复盘
        </h1>

        {/* 结果摘要 */}
        <div className={`rounded-xl p-4 mb-4 ${
          review.result_bb > 0 ? 'bg-green-900/50 border border-green-700' : 
          review.result_bb < 0 ? 'bg-red-900/50 border border-red-700' : 
          'bg-gray-800'
        }`}>
          <div className="text-center">
            <div className={`text-4xl font-bold mb-2 ${
              review.result_bb > 0 ? 'text-green-400' : 
              review.result_bb < 0 ? 'text-red-400' : 
              'text-gray-400'
            }`}>
              {review.result_bb > 0 ? '+' : ''}{review.result_bb.toFixed(1)} BB
            </div>
            <div className="text-gray-400">
              {review.ended_by === 'showdown' ? '摊牌' : review.ended_by === 'fold' ? '弃牌' : '结束'}
            </div>
          </div>
        </div>

        {/* 摊牌详细分析 */}
        {review.showdown_analysis && (
          <div className="bg-gray-800 rounded-xl p-4 mb-4">
            <h3 className="text-lg font-bold text-white mb-3">
              🎴 摊牌分析
            </h3>
            
            {/* 公共牌 */}
            <div className="mb-4">
              <div className="text-sm text-gray-400 mb-2">公共牌</div>
              <div className="flex justify-center gap-2">
                {review.showdown_analysis.community_cards.map((card, idx) => (
                  <div key={idx} className="w-10 h-14 bg-white rounded flex items-center justify-center text-lg font-bold text-black">
                    {formatCard(card)}
                  </div>
                ))}
              </div>
            </div>

            {/* 底池信息 */}
            <div className="mb-4 text-center">
              <div className="text-sm text-gray-400">底池</div>
              <div className="text-xl font-bold text-yellow-400">
                {review.showdown_analysis.pot.toFixed(1)} BB
              </div>
            </div>

            {/* 所有玩家手牌 */}
            <div className="mb-4">
              <div className="text-sm text-gray-400 mb-2">玩家手牌</div>
              <div className="space-y-2">
                {review.showdown_analysis.players.map((player) => (
                  <div 
                    key={player.seat}
                    className={`p-3 rounded-lg ${
                      player.is_winner ? 'bg-green-900/50 border border-green-600' : 
                      player.is_hero ? 'bg-blue-900/30 border border-blue-600' : 
                      'bg-gray-700'
                    } ${!player.in_hand ? 'opacity-50' : ''}`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`font-bold ${player.is_hero ? 'text-blue-400' : 'text-white'}`}>
                          {player.position}
                          {player.is_hero && ' (你)'}
                          {player.is_winner && ' 🏆'}
                        </span>
                        {!player.in_hand && (
                          <span className="text-xs text-gray-500">(弃牌)</span>
                        )}
                      </div>
                      <div className="text-sm text-gray-400">
                        投入: {player.total_committed.toFixed(1)} BB
                      </div>
                    </div>
                    {player.in_hand && (
                      <div className="mt-2 flex items-center gap-3">
                        <div className="flex gap-1">
                          {player.hole_cards.map((card, idx) => (
                            <div key={idx} className="w-8 h-11 bg-white rounded flex items-center justify-center text-sm font-bold text-black">
                              {formatCard(card)}
                            </div>
                          ))}
                        </div>
                        <div className={`text-sm font-medium ${
                          player.is_winner ? 'text-green-400' : 'text-gray-300'
                        }`}>
                          {player.hand_name}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* 详细解释 */}
            {review.showdown_analysis.explanation && (
              <div className="bg-gray-700/50 rounded-lg p-3">
                <div className="text-sm text-gray-300 whitespace-pre-line">
                  {review.showdown_analysis.explanation}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 翻牌关键点复盘 */}
        {review.flop_spot && (
          <div className="bg-gray-800 rounded-xl p-4 mb-4">
            <h3 className="text-lg font-bold text-white mb-3">
              翻牌关键点
            </h3>

            {/* 场景信息 */}
            <div className="grid grid-cols-2 gap-2 mb-4">
              <div className="bg-gray-700 rounded p-2 text-center">
                <div className="text-xs text-gray-400">底池类型</div>
                <div className="text-sm font-medium text-white">{review.flop_spot.pot_type}</div>
              </div>
              <div className="bg-gray-700 rounded p-2 text-center">
                <div className="text-xs text-gray-400">位置</div>
                <div className="text-sm font-medium text-white">{review.flop_spot.ip_oop}</div>
              </div>
            </div>

            {/* 公共牌 */}
            <div className="flex justify-center gap-2 mb-4">
              {review.flop_spot.board.map((card, idx) => (
                <div key={idx} className="w-10 h-14 bg-white rounded flex items-center justify-center text-lg">
                  {formatCard(card)}
                </div>
              ))}
            </div>

            {/* 你的选择 */}
            <div className="mb-4">
              <div className="text-sm text-gray-400 mb-1">你的选择</div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold text-white">
                  {ACTION_LABELS[review.flop_spot.user_action] || review.flop_spot.user_action}
                </span>
                <span className={`text-sm ${GRADE_COLORS[review.flop_spot.grade]}`}>
                  {GRADE_ICONS[review.flop_spot.grade]} {review.flop_spot.grade}
                </span>
              </div>
            </div>

            {/* Pro: 频率分布 */}
            {review.flop_spot.strategy && (
              <div className="mb-4">
                <div className="text-sm text-gray-400 mb-2">GTO 频率分布</div>
                <div className="space-y-2">
                  {(() => {
                    const flopSpot = review.flop_spot!;
                    const strategy = flopSpot.strategy!;
                    return Object.entries(strategy)
                      .sort(([, a], [, b]) => b - a)
                      .map(([action, freq]) => (
                        <div key={action} className="flex items-center gap-2">
                          <div className="w-20 text-sm text-gray-300">
                            {ACTION_LABELS[action] || action}
                          </div>
                          <div className="flex-1 bg-gray-700 rounded-full h-3 overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                action === flopSpot.best_action
                                  ? 'bg-green-500'
                                  : action === flopSpot.user_action
                                  ? 'bg-blue-500'
                                  : 'bg-gray-500'
                              }`}
                              style={{ width: `${freq * 100}%` }}
                            />
                          </div>
                          <div className="w-12 text-right text-sm text-gray-300">
                            {Math.round(freq * 100)}%
                          </div>
                        </div>
                      ));
                  })()}
                </div>
              </div>
            )}

            {/* 推荐动作 */}
            <div className="mb-4">
              <div className="text-sm text-gray-400 mb-1">推荐动作</div>
              <div className="text-lg font-bold text-green-400">
                {ACTION_LABELS[review.flop_spot.best_action] || review.flop_spot.best_action}
              </div>
            </div>

            {/* 解释 */}
            {review.flop_spot.explanation && (
              <div className="text-sm text-gray-300 bg-gray-700/50 rounded p-3">
                {review.flop_spot.explanation}
              </div>
            )}
          </div>
        )}

        {/* 按钮 */}
        <div className="flex gap-3">
          {review.can_replay && (
            <button
              onClick={replayHand}
              disabled={loading}
              className="flex-1 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 text-white font-bold rounded-lg transition-colors"
            >
              {loading ? '加载中...' : '重打同一手'}
            </button>
          )}
          <button
            onClick={() => { setReview(null); setSession(null); }}
            className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg transition-colors"
          >
            再来一局
          </button>
        </div>
      </div>
    );
  }

  // 渲染牌桌
  const state = session?.state;
  if (!state) return null;

  const hero = state.players.find(p => p.is_hero);
  const isHeroTurn = state.to_act_seat === state.hero_seat;
  const canAct = isHeroTurn && !loading;

  return (
    <div className={`max-w-4xl mx-auto ${isMobile ? 'px-0' : ''}`}>
      {/* 顶部信息栏 */}
      <div className="bg-gray-800 rounded-t-xl p-3 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div>
            <span className="text-gray-400 text-xs">底池</span>
            <div className="text-xl font-bold text-yellow-400">{state.pot.toFixed(1)} BB</div>
          </div>
          <div>
            <span className="text-gray-400 text-xs">当前下注</span>
            <div className="text-lg font-medium text-white">{state.current_bet.toFixed(1)} BB</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-400">
            {state.street === 'preflop' ? '翻前' : 
             state.street === 'flop' ? '翻牌' : 
             state.street === 'turn' ? '转牌' : 
             state.street === 'river' ? '河牌' : '摊牌'}
          </div>
        </div>
      </div>

      {/* 牌桌区域 */}
      <div 
        className="relative bg-green-900 rounded-b-xl overflow-hidden"
        style={{ height: isMobile ? '350px' : '450px' }}
      >
        {/* 牌桌椭圆形 */}
        <div 
          className="absolute bg-green-800 border-4 border-amber-900 rounded-full"
          style={{
            top: '15%',
            left: '10%',
            right: '10%',
            bottom: '15%',
          }}
        />

        {/* 按钮标记 */}
        {SEAT_POSITIONS.map(pos => {
          const isButton = pos.seat === state.button_seat;
          if (!isButton) return null;
          return (
            <div
              key={`btn-${pos.seat}`}
              className="absolute w-6 h-6 bg-white rounded-full flex items-center justify-center text-xs font-bold text-gray-800 z-10"
              style={{
                top: `calc(${pos.top} + 5%)`,
                left: pos.label === 'left' ? '20%' : pos.label === 'right' ? '75%' : pos.left,
                transform: 'translate(-50%, -50%)',
              }}
            >
              D
            </div>
          );
        })}

        {/* 公共牌 */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex gap-2 z-10">
          {state.community_cards.map((card, idx) => (
            <div key={idx} className="w-10 h-14 bg-white rounded shadow-lg flex items-center justify-center text-xl">
              {formatCard(card)}
            </div>
          ))}
          {/* 空位占位 */}
          {[...Array(5 - state.community_cards.length)].map((_, idx) => (
            <div key={`empty-${idx}`} className="w-10 h-14 bg-green-700/50 border-2 border-dashed border-green-600 rounded" />
          ))}
        </div>

        {/* 玩家座位 */}
        {state.players.map((player) => {
          const pos = getPlayerPosition(player.seat);
          const isActive = player.seat === state.to_act_seat;
          
          return (
            <div
              key={player.seat}
              className={`absolute transform -translate-x-1/2 -translate-y-1/2 z-20 ${
                player.in_hand ? '' : 'opacity-50'
              }`}
              style={{ top: pos.top, left: pos.left }}
            >
              {/* 玩家信息 */}
              <div className={`bg-gray-800 rounded-lg p-2 min-w-[80px] text-center ${
                isActive ? 'ring-2 ring-yellow-400' : ''
              } ${player.is_hero ? 'ring-2 ring-blue-400' : ''}`}>
                <div className={`text-xs font-bold ${POSITION_COLORS[player.position] || 'text-gray-400'}`}>
                  {player.position}
                </div>
                <div className="text-sm text-white">{player.stack.toFixed(1)} BB</div>
                
                {/* Hero 手牌 */}
                {player.is_hero && player.hole_cards && (
                  <div className="flex justify-center gap-1 mt-1">
                    {player.hole_cards.map((card, idx) => (
                      <div key={idx} className="w-6 h-8 bg-white rounded text-xs flex items-center justify-center">
                        {formatCard(card)}
                      </div>
                    ))}
                  </div>
                )}
                
                {/* 非 Hero 背面牌 */}
                {!player.is_hero && player.in_hand && (
                  <div className="flex justify-center gap-1 mt-1">
                    <div className="w-6 h-8 bg-blue-600 rounded text-xs" />
                    <div className="w-6 h-8 bg-blue-600 rounded text-xs" />
                  </div>
                )}
              </div>

              {/* 已投入筹码 */}
              {player.committed_this_street > 0 && (
                <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs text-yellow-400">
                  {player.committed_this_street.toFixed(1)}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 行动日志 */}
      <div className="bg-gray-800 mt-2 p-2 rounded-lg overflow-x-auto">
        <div className="flex gap-2 text-xs text-gray-400 whitespace-nowrap">
          {session.action_log.slice(-5).map((action, idx) => (
            <span key={idx}>
              {action.position}: {ACTION_LABELS[action.action] || action.action}
              {action.amount ? ` ${action.amount.toFixed(1)}` : ''}
            </span>
          ))}
        </div>
      </div>

      {/* 操作面板 */}
      {isHeroTurn && (
        <div className="mt-4 bg-gray-800 rounded-xl p-4">
          {/* 关键点提示 */}
          {session.is_key_spot && (
            <div className="mb-4 text-center">
              <span className="inline-block px-3 py-1 bg-yellow-500/20 text-yellow-400 rounded-full text-sm font-medium">
                🎯 翻牌关键点
              </span>
            </div>
          )}

          {/* 需要跟注 */}
          {state.current_bet > (hero?.committed_this_street || 0) && (
            <div className="text-center mb-4">
              <span className="text-gray-400">需跟注 </span>
              <span className="text-xl font-bold text-yellow-400">
                {(state.current_bet - (hero?.committed_this_street || 0)).toFixed(1)} BB
              </span>
            </div>
          )}

          {/* 基本动作按钮 */}
          <div className="grid grid-cols-4 gap-2 mb-3">
            {session.legal_actions.includes('fold') && (
              <button
                onClick={() => executeAction('fold')}
                disabled={!canAct}
                className="py-3 bg-gray-600 hover:bg-gray-500 disabled:bg-gray-800 text-white font-bold rounded-lg transition-colors"
              >
                弃牌
              </button>
            )}
            {session.legal_actions.includes('check') && (
              <button
                onClick={() => executeAction('check')}
                disabled={!canAct}
                className="py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 text-white font-bold rounded-lg transition-colors"
              >
                过牌
              </button>
            )}
            {session.legal_actions.includes('call') && (
              <button
                onClick={() => executeAction('call')}
                disabled={!canAct}
                className="py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 text-white font-bold rounded-lg transition-colors"
              >
                跟注
              </button>
            )}
            {session.legal_actions.includes('allin') && (
              <button
                onClick={() => executeAction('allin')}
                disabled={!canAct}
                className="py-3 bg-red-600 hover:bg-red-500 disabled:bg-gray-800 text-white font-bold rounded-lg transition-colors"
              >
                全下
              </button>
            )}
          </div>

          {/* 下注/加注按钮 */}
          {(session.legal_actions.includes('bet') || session.legal_actions.includes('raise')) && (
            <div className="grid grid-cols-3 gap-2">
              {betSizes && (
                <>
                  <button
                    onClick={() => executeAction(
                      session.legal_actions.includes('bet') ? 'bet' : 'raise',
                      betSizes.bet33
                    )}
                    disabled={!canAct}
                    className="py-3 bg-red-600 hover:bg-red-500 disabled:bg-gray-800 text-white font-bold rounded-lg transition-colors"
                  >
                    <div className="text-xs opacity-75">33% 底池</div>
                    <div>{betSizes.bet33.toFixed(1)} BB</div>
                  </button>
                  <button
                    onClick={() => executeAction(
                      session.legal_actions.includes('bet') ? 'bet' : 'raise',
                      betSizes.bet75
                    )}
                    disabled={!canAct}
                    className="py-3 bg-red-600 hover:bg-red-500 disabled:bg-gray-800 text-white font-bold rounded-lg transition-colors"
                  >
                    <div className="text-xs opacity-75">75% 底池</div>
                    <div>{betSizes.bet75.toFixed(1)} BB</div>
                  </button>
                  <button
                    onClick={() => executeAction(
                      session.legal_actions.includes('bet') ? 'bet' : 'raise',
                      betSizes.bet125
                    )}
                    disabled={!canAct}
                    className="py-3 bg-red-600 hover:bg-red-500 disabled:bg-gray-800 text-white font-bold rounded-lg transition-colors"
                  >
                    <div className="text-xs opacity-75">125% 底池</div>
                    <div>{betSizes.bet125.toFixed(1)} BB</div>
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* 等待提示 */}
      {!isHeroTurn && state.status !== 'ENDED' && (
        <div className="mt-4 text-center py-4 bg-gray-800 rounded-xl">
          <div className="text-gray-400">AI 思考中...</div>
        </div>
      )}
    </div>
  );
};

export default FullHand;
