import React, { useState } from 'react';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';
import { useMobile } from '../hooks/useMobile';
import toast from 'react-hot-toast';

interface Scenario {
  id: number;
  description: string;
  hero_position: string;
  hero_hand: string;
  hand_type: string;
  stack_size: number;
  actions_before: Array<{
    position: string;
    action: string;
    amount: number | null;
    display: string;
  }>;
  current_bet: number;
  pot_size: number;
  options: string[];
}

const AdvancedTraining: React.FC = () => {
  const { user } = useAuthStore();
  const { isMobile } = useMobile();
  
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [completed, setCompleted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [finalResult, setFinalResult] = useState<any>(null);

  const startTraining = async () => {
    setLoading(true);
    try {
      const res = await api.post('/advanced/start', null, {
        params: { stack_size: 100, scenario_count: 10 }
      });
      
      setSessionId(res.data.session_id);
      setScenarios(res.data.scenarios);
      setCurrentIndex(0);
      setResult(null);
      setCompleted(false);
      setFinalResult(null);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '开始训练失败');
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async (action: string) => {
    if (!sessionId) return;
    
    const scenario = scenarios[currentIndex];
    
    try {
      const res = await api.post(`/advanced/answer/${sessionId}`, null, {
        params: {
          scenario_id: scenario.id,
          action: action
        }
      });
      
      setResult(res.data.result);
      
      if (res.data.progress.completed) {
        setCompleted(true);
        // 获取最终结果
        const finalRes = await api.get(`/advanced/result/${sessionId}`);
        setFinalResult(finalRes.data);
      } else {
        setCurrentIndex(res.data.progress.current);
      }
    } catch (error: any) {
      toast.error('提交失败');
    }
  };

  const nextScenario = () => {
    setResult(null);
  };

  // 格式化行动按钮显示
  const formatAction = (action: string) => {
    if (action === 'fold') return '弃牌';
    if (action === 'call') return `跟注 ${scenarios[currentIndex]?.current_bet}BB`;
    if (action === 'check') return '过牌';
    if (action === 'all_in') return 'All-in';
    if (action.startsWith('raise_')) {
      const amount = action.replace('raise_', '').replace('bb', '');
      return `加注到 ${amount}BB`;
    }
    if (action === 'limp') return '溜入';
    return action;
  };

  // 获取手牌颜色
  const getHandColor = (hand: string) => {
    const premium = ['AA', 'KK', 'QQ', 'JJ', 'AKs', 'AKo', 'AQs'];
    const strong = ['TT', '99', '88', 'AJs', 'ATs', 'KQs', 'AQo'];
    
    if (premium.includes(hand)) return 'text-yellow-400';
    if (strong.includes(hand)) return 'text-green-400';
    return 'text-white';
  };

  // 开始界面
  if (!sessionId) {
    return (
      <div className={`max-w-2xl mx-auto animate-fade-in ${isMobile ? 'px-2' : ''}`}>
        <h1 className={`font-bold text-white mb-4 ${isMobile ? 'text-xl' : 'text-2xl'}`}>
          🎮 高级牌局模拟
        </h1>
        
        <div className="bg-gray-800 rounded-xl p-4 md:p-6 space-y-4">
          <p className="text-gray-300 text-sm md:text-base">
            在高级模式下，你将面对真实的牌局场景：
          </p>
          
          <ul className="space-y-2 text-sm text-gray-400">
            <li className="flex items-center"><span className="text-blue-400 mr-2">•</span>多人参与的复杂局面</li>
            <li className="flex items-center"><span className="text-blue-400 mr-2">•</span>面对加注、3bet、All-in</li>
            <li className="flex items-center"><span className="text-blue-400 mr-2">•</span>挤压局面和底池赔率计算</li>
            <li className="flex items-center"><span className="text-blue-400 mr-2">•</span>更贴近真实游戏的决策训练</li>
          </ul>
          
          <div className="bg-gray-700 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-2">示例场景：</div>
            <div className="text-sm text-white">
              "UTG 加注到 3BB，MP 跟注，你在 CO 位拿到 AKs，底池挤压机会..."
            </div>
          </div>
          
          <button
            onClick={startTraining}
            disabled={loading}
            className="w-full py-3 md:py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold rounded-lg transition-colors"
          >
            {loading ? '准备中...' : '开始高级训练'}
          </button>
        </div>
      </div>
    );
  }

  // 完成界面
  if (completed && finalResult) {
    return (
      <div className={`max-w-2xl mx-auto animate-fade-in ${isMobile ? 'px-2' : ''}`}>
        <div className="bg-gray-800 rounded-xl p-6 text-center">
          <div className="text-5xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold text-white mb-2">训练完成！</h2>
          
          <div className="grid grid-cols-3 gap-4 my-6">
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="text-2xl font-bold text-white">{finalResult.total_scenarios}</div>
              <div className="text-xs text-gray-400">总题数</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="text-2xl font-bold text-green-400">{finalResult.correct_count}</div>
              <div className="text-xs text-gray-400">正确数</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="text-2xl font-bold text-blue-400">{finalResult.accuracy}%</div>
              <div className="text-xs text-gray-400">正确率</div>
            </div>
          </div>
          
          <button
            onClick={startTraining}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg transition-colors"
          >
            再练一次
          </button>
        </div>
      </div>
    );
  }

  // 训练界面
  const scenario = scenarios[currentIndex];

  return (
    <div className={`max-w-2xl mx-auto animate-fade-in ${isMobile ? 'px-0' : ''}`}>
      {/* 进度 */}
      <div className="mb-4 px-2">
        <div className="flex justify-between text-sm text-gray-400 mb-1">
          <span>高级模拟 - 进度 {currentIndex + 1}/{scenarios.length}</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div
            className="bg-purple-600 h-2 rounded-full transition-all"
            style={{ width: `${((currentIndex + 1) / scenarios.length) * 100}%` }}
          />
        </div>
      </div>

      {/* 场景卡片 */}
      <div className="bg-gray-800 rounded-xl p-4 md:p-6">
        {/* 场景描述 */}
        <div className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 rounded-lg p-3 md:p-4 mb-4">
          <div className="text-xs text-purple-400 mb-1">场景描述</div>
          <div className="text-white text-sm md:text-base">{scenario.description}</div>
        </div>

        {/* 之前的行动 */}
        {scenario.actions_before.length > 0 && (
          <div className="mb-4">
            <div className="text-xs text-gray-400 mb-2">前面行动：</div>
            <div className="space-y-1">
              {scenario.actions_before.map((action, i) => (
                <div key={i} className="text-sm text-gray-300 bg-gray-700/50 rounded px-2 py-1">
                  {action.display}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 手牌和位置 */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-gray-700 rounded-lg p-3 text-center">
            <div className={`text-3xl md:text-4xl font-bold ${getHandColor(scenario.hero_hand)}`}>
              {scenario.hero_hand}
            </div>
            <div className="text-xs text-gray-400">你的手牌 ({scenario.hand_type})</div>
          </div>
          <div className="bg-gray-700 rounded-lg p-3 text-center">
            <div className="text-3xl md:text-4xl font-bold text-blue-400">
              {scenario.hero_position}
            </div>
            <div className="text-xs text-gray-400">你的位置</div>
          </div>
        </div>

        {/* 底池信息 */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-gray-700/50 rounded-lg p-2 text-center">
            <div className="text-lg font-bold text-green-400">{scenario.pot_size}BB</div>
            <div className="text-xs text-gray-400">底池</div>
          </div>
          <div className="bg-gray-700/50 rounded-lg p-2 text-center">
            <div className="text-lg font-bold text-yellow-400">{scenario.current_bet}BB</div>
            <div className="text-xs text-gray-400">需跟注</div>
          </div>
        </div>

        {/* 行动按钮 */}
        {!result ? (
          <div className="grid grid-cols-2 gap-2">
            {scenario.options.map((action) => (
              <button
                key={action}
                onClick={() => submitAnswer(action)}
                className={`py-3 px-2 rounded-lg font-medium text-sm transition-colors ${
                  action === 'fold'
                    ? 'bg-gray-600 hover:bg-gray-500 text-white'
                    : action === 'check'
                    ? 'bg-blue-600 hover:bg-blue-500 text-white'
                    : action === 'call'
                    ? 'bg-blue-600 hover:bg-blue-500 text-white'
                    : action === 'all_in'
                    ? 'bg-red-600 hover:bg-red-500 text-white'
                    : 'bg-purple-600 hover:bg-purple-500 text-white'
                }`}
              >
                {formatAction(action)}
              </button>
            ))}
          </div>
        ) : (
          <div className={`rounded-lg p-4 ${result.is_correct ? 'bg-green-900/50 border border-green-700' : 'bg-red-900/50 border border-red-700'}`}>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">{result.is_correct ? '✅' : '❌'}</span>
              <span className="font-bold text-white">
                {result.is_correct ? '正确!' : '还可以更好'}
              </span>
            </div>
            
            <div className="text-sm text-gray-300 mb-2">
              你的选择: <span className="text-white font-medium">{formatAction(result.user_action)}</span>
            </div>
            
            {!result.is_correct && (
              <div className="text-sm text-gray-300 mb-2">
                GTO 建议: <span className="text-green-400 font-medium">{formatAction(result.correct_action)}</span>
              </div>
            )}
            
            <div className="text-sm text-gray-400 mb-3">
              {result.feedback}
            </div>
            
            <div className="text-sm text-gray-500 italic">
              {result.explanation}
            </div>
            
            <button
              onClick={nextScenario}
              className="w-full mt-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg transition-colors"
            >
              {currentIndex >= scenarios.length - 1 ? '查看结果' : '下一题'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdvancedTraining;
