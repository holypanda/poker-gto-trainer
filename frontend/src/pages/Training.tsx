import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { trainingApi } from '../services/api';
import { useAuthStore } from '../store/authStore';
import { useMobile, useTouchFeedback } from '../hooks/useMobile';
import { 
  TrainingSession, TrainingScenario, TrainingResult, 
  POSITIONS, ACTIONS_TO_YOU, StackSize, Position, ACTION_LABELS 
} from '../types';
import toast from 'react-hot-toast';

const Training: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { isMobile } = useMobile();
  const { touched, onTouchStart, onTouchEnd } = useTouchFeedback();
  
  // Training config state
  const [config, setConfig] = useState({
    stackSize: 100 as StackSize,
    position: 'BTN' as Position,
    actionToYou: 'open',
    scenarioCount: isMobile ? 10 : 15,
  });
  
  // Training session state
  const [session, setSession] = useState<TrainingSession | null>(null);
  const [currentResult, setCurrentResult] = useState<TrainingResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [startTime, setStartTime] = useState<number>(0);
  
  // 新增：计时器状态
  const [timeLeft, setTimeLeft] = useState<number>(10);
  const [isTimeout, setIsTimeout] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const [totalScore, setTotalScore] = useState(0);

  const canStartTraining = user?.is_subscribed || (user?.free_trains_today || 0) > 0;

  const startTraining = async () => {
    if (!canStartTraining) {
      toast.error('今日免费训练次数已用完，请订阅 VIP');
      return;
    }

    setLoading(true);
    setTotalScore(0);
    try {
      const response = await trainingApi.createSession({
        stack_size: config.stackSize,
        position: config.position,
        action_to_you: config.actionToYou,
        scenario_count: config.scenarioCount,
      });
      
      setSession(response.data);
      setStartTime(Date.now());
      setCurrentResult(null);
      
      // 设置初始倒计时
      const firstScenario = response.data.scenarios[0];
      const timeLimit = firstScenario?.time_limit || 10;
      setTimeLeft(timeLimit);
      setIsTimeout(false);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '开始训练失败');
    } finally {
      setLoading(false);
    }
  };

  // 倒计时逻辑
  useEffect(() => {
    if (session && !currentResult && timeLeft > 0) {
      timerRef.current = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            // 超时自动提交
            setIsTimeout(true);
            submitAnswer('timeout');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [session, currentResult, timeLeft]);

  const submitAnswer = async (action: string) => {
    if (!session || currentResult) return;

    // 清除计时器
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    const responseTime = Date.now() - startTime;
    
    try {
      const response = await trainingApi.submitAnswer(session.id, {
        scenario_id: session.scenarios[session.current_index].id,
        action,
        response_time_ms: responseTime,
      });
      
      setCurrentResult(response.data);
      
      // 累加得分
      if (response.data.score) {
        setTotalScore(prev => prev + response.data.score);
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '提交答案失败');
    }
  };

  const nextScenario = () => {
    if (!session) return;
    
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    
    if (session.current_index + 1 >= session.scenarios.length) {
      completeTraining();
    } else {
      const nextIndex = session.current_index + 1;
      const nextScenario = session.scenarios[nextIndex];
      const timeLimit = nextScenario?.time_limit || 10;
      
      setCurrentResult(null);
      setStartTime(Date.now());
      setTimeLeft(timeLimit);
      setIsTimeout(false);
      setSession({
        ...session,
        current_index: nextIndex,
      });
    }
  };

  const completeTraining = async () => {
    if (!session) return;
    
    try {
      const response = await trainingApi.completeSession(session.id);
      toast.success(`训练完成！正确率: ${response.data.accuracy}%`);
      setSession(null);
      setCurrentResult(null);
    } catch (error) {
      toast.error('完成训练失败');
    }
  };

  // Format hand display
  const formatHand = (hand: string) => {
    const isPair = hand.length === 2;
    const isSuited = hand.endsWith('s');
    
    let display = hand;
    if (!isPair) {
      display = hand.slice(0, 2);
    }
    
    return {
      display,
      suffix: isPair ? '' : isSuited ? 's' : 'o',
      isSuited,
    };
  };

  // Get hand strength color
  const getHandColor = (hand: string) => {
    const premium = ['AA', 'KK', 'QQ', 'JJ', 'AKs', 'AKo', 'AQs'];
    const strong = ['TT', '99', '88', 'AJs', 'ATs', 'KQs', 'AQo'];
    
    if (premium.includes(hand)) return 'text-yellow-400';
    if (strong.includes(hand)) return 'text-green-400';
    return 'text-white';
  };

  // Config Screen
  if (!session) {
    return (
      <div className={`max-w-2xl mx-auto animate-fade-in ${isMobile ? 'px-2' : ''}`}>
        <h1 className={`font-bold text-white mb-4 md:mb-6 ${isMobile ? 'text-xl' : 'text-2xl'}`}>
          开始训练
        </h1>
        
        {!canStartTraining && (
          <div className="bg-red-900/50 border border-red-700 rounded-lg p-3 md:p-4 mb-4 md:mb-6">
            <p className="text-red-300 text-sm md:text-base">
              今日免费训练次数已用完。请订阅 VIP 享受无限训练！
            </p>
          </div>
        )}

        <div className="bg-gray-800 rounded-xl p-4 md:p-6 space-y-4 md:space-y-6">
          {/* Stack Size */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2 md:mb-3">
              筹码深度 (BB)
            </label>
            <div className="grid grid-cols-2 gap-2 md:gap-3">
              {[50, 100].map((size) => (
                <button
                  key={size}
                  onClick={() => setConfig({ ...config, stackSize: size as StackSize })}
                  className={`py-2 md:py-3 px-3 md:px-4 rounded-lg font-medium transition-colors ${
                    config.stackSize === size
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {size} BB
                </button>
              ))}
            </div>
          </div>

          {/* Position */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2 md:mb-3">
              你的位置
            </label>
            <div className="grid grid-cols-3 gap-2">
              {POSITIONS.map((pos) => (
                <button
                  key={pos.value}
                  onClick={() => setConfig({ ...config, position: pos.value })}
                  className={`py-2 md:py-3 px-2 md:px-3 rounded-lg text-sm font-medium transition-colors ${
                    config.position === pos.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {pos.value}
                </button>
              ))}
            </div>
          </div>

          {/* Action to You */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2 md:mb-3">
              面对的行动
            </label>
            <select
              value={config.actionToYou}
              onChange={(e) => setConfig({ ...config, actionToYou: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 md:px-4 py-2 md:py-3 text-white text-sm md:text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {ACTIONS_TO_YOU.map((action) => (
                <option key={action.value} value={action.value}>
                  {action.label}
                </option>
              ))}
            </select>
          </div>

          {/* Scenario Count */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2 md:mb-3">
              训练题数: {config.scenarioCount}
            </label>
            <input
              type="range"
              min="5"
              max={isMobile ? "30" : "50"}
              step="5"
              value={config.scenarioCount}
              onChange={(e) => setConfig({ ...config, scenarioCount: parseInt(e.target.value) })}
              className="w-full accent-blue-500"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>5</span>
              <span>{isMobile ? "30" : "50"}</span>
            </div>
          </div>

          {/* Start Button */}
          <button
            onClick={startTraining}
            disabled={loading || !canStartTraining}
            className="w-full py-3 md:py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-bold text-base md:text-lg rounded-lg transition-colors active:scale-95 transform"
          >
            {loading ? '准备中...' : '开始训练'}
          </button>
        </div>
      </div>
    );
  }

  // Training Screen
  const currentScenario = session.scenarios[session.current_index];
  const handInfo = formatHand(currentScenario.hand);
  
  // 获取当前难度和时间限制
  const difficulty = currentScenario.difficulty || 'normal';
  const difficultyColors: Record<string, string> = {
    easy: 'text-green-400',
    normal: 'text-yellow-400', 
    hard: 'text-red-400'
  };

  return (
    <div className={`max-w-2xl mx-auto animate-fade-in ${isMobile ? 'px-0' : ''}`}>
      {/* Progress & Timer & Score */}
      <div className="mb-4 md:mb-6 px-2 md:px-0">
        <div className="flex justify-between text-sm text-gray-400 mb-1 md:mb-2">
          <span>进度: {session.current_index + 1} / {session.scenarios.length}</span>
          <div className="flex items-center gap-4">
            <span className={difficultyColors[difficulty]}>
              {difficulty === 'easy' ? '简单' : difficulty === 'hard' ? '困难' : '中等'}
            </span>
            <span className="text-yellow-400 font-bold">得分: {totalScore}</span>
          </div>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2 mb-3">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${((session.current_index + 1) / session.scenarios.length) * 100}%` }}
          />
        </div>
        
        {/* 倒计时条 */}
        {!currentResult && (
          <div className="w-full bg-gray-800 rounded-full h-4 overflow-hidden border border-gray-700">
            <div
              className={`h-full transition-all duration-1000 ${
                timeLeft <= 3 ? 'bg-red-500' : timeLeft <= 5 ? 'bg-yellow-500' : 'bg-green-500'
              }`}
              style={{ width: `${(timeLeft / (currentScenario.time_limit || 10)) * 100}%` }}
            />
          </div>
        )}
        {!currentResult && (
          <div className={`text-center text-sm mt-1 ${timeLeft <= 3 ? 'text-red-400 font-bold' : 'text-gray-400'}`}>
            {timeLeft} 秒
          </div>
        )}
      </div>

      {/* Scenario Card */}
      <div className="bg-gray-800 rounded-xl md:rounded-2xl p-4 md:p-8">
        {/* Hand Display */}
        <div className="text-center mb-4 md:mb-8">
          <div className={`font-bold mb-1 md:mb-2 ${isMobile ? 'text-5xl' : 'text-6xl'} ${getHandColor(currentScenario.hand)}`}>
            {handInfo.display}
            {!handInfo.display.match(/[so]/) && handInfo.suffix && (
              <span className={`align-top ${isMobile ? 'text-xl' : 'text-2xl'}`}>{handInfo.suffix}</span>
            )}
          </div>
          <div className="text-gray-400 text-sm md:text-base">你的起手牌</div>
        </div>

        {/* Context */}
        <div className="grid grid-cols-2 gap-2 md:gap-4 mb-4 md:mb-8">
          <div className="bg-gray-700 rounded-lg p-3 md:p-4 text-center">
            <div className={`font-bold text-blue-400 ${isMobile ? 'text-lg' : 'text-2xl'}`}>
              {config.stackSize} BB
            </div>
            <div className="text-xs text-gray-400">筹码深度</div>
          </div>
          <div className="bg-gray-700 rounded-lg p-3 md:p-4 text-center">
            <div className={`font-bold text-green-400 ${isMobile ? 'text-lg' : 'text-2xl'}`}>
              {config.position}
            </div>
            <div className="text-xs text-gray-400">你的位置</div>
          </div>
        </div>

        {/* Action Description */}
        <div className="bg-gray-700/50 rounded-lg p-3 md:p-4 mb-4 md:mb-6">
          <div className="text-xs md:text-sm text-gray-400 mb-1">场景</div>
          <div className="text-white text-sm md:text-base">
            {ACTIONS_TO_YOU.find(a => a.value === config.actionToYou)?.label}
          </div>
        </div>

        {/* Action Buttons */}
        {!currentResult ? (
          <div className="grid grid-cols-2 gap-2 md:gap-3">
            {currentScenario.options.map((action) => (
              <button
                key={action}
                onClick={() => submitAnswer(action)}
                onTouchStart={() => onTouchStart(action)}
                onTouchEnd={onTouchEnd}
                disabled={isTimeout}
                className={`py-3 md:py-4 px-2 md:px-4 rounded-lg font-medium transition-all active:scale-95 transform min-h-[52px] md:min-h-[60px] ${
                  action === 'fold'
                    ? 'bg-gray-600 hover:bg-gray-500 text-white'
                    : action.startsWith('raise')
                    ? 'bg-red-600 hover:bg-red-500 text-white'
                    : action === 'call' || action === 'limp'
                    ? 'bg-blue-600 hover:bg-blue-500 text-white'
                    : 'bg-green-600 hover:bg-green-500 text-white'
                } ${touched === action ? 'scale-95 opacity-80' : ''} ${isTimeout ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <span className="text-sm md:text-base">{ACTION_LABELS[action] || action}</span>
              </button>
            ))}
          </div>
        ) : (
          <div className={`rounded-lg p-4 md:p-6 ${currentResult.is_correct ? 'bg-green-900/50 border border-green-700' : 'bg-red-900/50 border border-red-700'}`}>
            <div className="flex items-center gap-2 md:gap-3 mb-3 md:mb-4">
              <span className="text-2xl md:text-3xl">{currentResult.is_correct ? '✅' : '❌'}</span>
              <div className="flex-1">
                <div className="font-bold text-white text-base md:text-lg">
                  {currentResult.is_correct ? '正确!' : '错误'}
                  {currentResult.time_bonus && (
                    <span className="ml-2 text-yellow-400 text-sm">⚡ 速度奖励!</span>
                  )}
                </div>
                <div className="text-xs md:text-sm text-gray-300">
                  你的选择: {ACTION_LABELS[currentResult.user_action]}
                </div>
              </div>
              {currentResult.score !== undefined && (
                <div className="text-right">
                  <div className="text-2xl font-bold text-yellow-400">+{currentResult.score}</div>
                  <div className="text-xs text-gray-400">得分</div>
                </div>
              )}
            </div>

            {!currentResult.is_correct && (
              <div className="mb-3 md:mb-4">
                <div className="text-xs md:text-sm text-gray-400">GTO 建议:</div>
                <div className="text-base md:text-lg font-semibold text-green-400">
                  {ACTION_LABELS[currentResult.correct_action]}
                </div>
              </div>
            )}

            {/* GTO Frequency */}
            <div className="mb-3 md:mb-4">
              <div className="text-xs md:text-sm text-gray-400 mb-2">GTO 频率分布:</div>
              <div className="space-y-1.5 md:space-y-2">
                {Object.entries(currentResult.gto_frequency)
                  .sort(([, a], [, b]) => b - a)
                  .map(([action, freq]) => (
                    <div key={action} className="flex items-center gap-2">
                      <div className="w-16 md:w-20 text-xs md:text-sm text-gray-300">
                        {ACTION_LABELS[action]}
                      </div>
                      <div className="flex-1 bg-gray-700 rounded-full h-2.5 md:h-4 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            action === currentResult.correct_action
                              ? 'bg-green-500'
                              : 'bg-gray-500'
                          }`}
                          style={{ width: `${freq * 100}%` }}
                        />
                      </div>
                      <div className="w-10 md:w-12 text-right text-xs md:text-sm text-gray-300">
                        {Math.round(freq * 100)}%
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            <div className="text-xs md:text-sm text-gray-300 mb-3 md:mb-4">
              {currentResult.explanation}
            </div>

            <button
              onClick={nextScenario}
              className="w-full py-2.5 md:py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg transition-colors active:scale-95 transform"
            >
              {session.current_index + 1 >= session.scenarios.length ? '完成训练' : '下一题'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Training;
