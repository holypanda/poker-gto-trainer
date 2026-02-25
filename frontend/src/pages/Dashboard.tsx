import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { authApi } from '../services/api';
import { UserStats } from '../types';
import { useMobile } from '../hooks/useMobile';

const Dashboard: React.FC = () => {
  const { user } = useAuthStore();
  const { isMobile } = useMobile();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await authApi.getStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">加载中...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4 md:space-y-8 animate-fade-in">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-900 to-purple-900 rounded-xl md:rounded-2xl p-4 md:p-8">
        <h1 className={`font-bold text-white mb-2 ${isMobile ? 'text-lg' : 'text-2xl md:text-3xl'}`}>
          欢迎回来, {user?.username}! 👋
        </h1>
        <p className="text-gray-300 mb-4 md:mb-6 text-sm md:text-base">
          今天也要继续练习 GTO 策略，提升你的翻前决策水平！
        </p>
        
        <div className="flex flex-wrap gap-2 md:gap-4">
          <Link
            to="/training"
            className="inline-flex items-center px-4 md:px-6 py-2 md:py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors text-sm md:text-base"
          >
            <span className="mr-1 md:mr-2">🎯</span>
            开始训练
          </Link>
          
          {!user?.is_subscribed && (
            <Link
              to="/subscription"
              className="inline-flex items-center px-4 md:px-6 py-2 md:py-3 bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 text-black font-semibold rounded-lg transition-colors text-sm md:text-base"
            >
              <span className="mr-1 md:mr-2">💎</span>
              升级 VIP
            </Link>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className={`grid gap-2 md:gap-4 ${isMobile ? 'grid-cols-2' : 'grid-cols-2 md:grid-cols-4'}`}>
        <div className="stat-card p-3 md:p-4">
          <div className={`font-bold text-white ${isMobile ? 'text-xl' : 'text-2xl md:text-3xl'}`}>
            {stats?.total_trains || 0}
          </div>
          <div className="text-xs md:text-sm text-gray-400">总训练次数</div>
        </div>
        
        <div className="stat-card p-3 md:p-4">
          <div className={`font-bold text-green-400 ${isMobile ? 'text-xl' : 'text-2xl md:text-3xl'}`}>
            {stats?.accuracy || 0}%
          </div>
          <div className="text-xs md:text-sm text-gray-400">正确率</div>
        </div>
        
        <div className="stat-card p-3 md:p-4">
          <div className={`font-bold text-yellow-400 ${isMobile ? 'text-xl' : 'text-2xl md:text-3xl'}`}>
            {stats?.streak_days || 0}
          </div>
          <div className="text-xs md:text-sm text-gray-400">连续天数</div>
        </div>
        
        <div className="stat-card p-3 md:p-4">
          <div className={`font-bold text-blue-400 ${isMobile ? 'text-xl' : 'text-2xl md:text-3xl'}`}>
            {user?.is_subscribed ? '∞' : (stats?.free_trains_today || 0)}
          </div>
          <div className="text-xs md:text-sm text-gray-400">
            {user?.is_subscribed ? '无限训练' : '今日剩余'}
          </div>
        </div>
      </div>

      {/* Quick Start */}
      <div>
        <h2 className={`font-bold text-white mb-3 md:mb-4 ${isMobile ? 'text-base' : 'text-xl'}`}>
          快速开始
        </h2>
        <div className={`grid gap-3 md:gap-4 ${isMobile ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-3'}`}>
          <Link
            to="/training"
            className="bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-xl p-4 md:p-6 transition-colors group"
          >
            <div className="text-2xl md:text-3xl mb-2 md:mb-3">🎯</div>
            <h3 className={`font-semibold text-white mb-1 md:mb-2 group-hover:text-blue-400 ${isMobile ? 'text-base' : 'text-lg'}`}>
              开始新训练
            </h3>
            <p className="text-xs md:text-sm text-gray-400">
              选择位置、筹码深度和场景，开始你的 GTO 训练
            </p>
          </Link>

          <Link
            to="/fullhand"
            className="bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-xl p-4 md:p-6 transition-colors group"
          >
            <div className="text-2xl md:text-3xl mb-2 md:mb-3">🎮</div>
            <h3 className={`font-semibold text-white mb-1 md:mb-2 group-hover:text-blue-400 ${isMobile ? 'text-base' : 'text-lg'}`}>
              完整牌局模拟
            </h3>
            <p className="text-xs md:text-sm text-gray-400">
              体验完整的 6max 牌局，在翻牌关键点做出决策并获取 GTO 反馈
            </p>
          </Link>

          <Link
            to="/stats"
            className="bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-xl p-4 md:p-6 transition-colors group"
          >
            <div className="text-2xl md:text-3xl mb-2 md:mb-3">📊</div>
            <h3 className={`font-semibold text-white mb-1 md:mb-2 group-hover:text-blue-400 ${isMobile ? 'text-base' : 'text-lg'}`}>
              查看统计
            </h3>
            <p className="text-xs md:text-sm text-gray-400">
              分析你的训练数据，找出需要改进的地方
            </p>
          </Link>

          <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 md:p-6">
            <div className="text-2xl md:text-3xl mb-2 md:mb-3">📚</div>
            <h3 className={`font-semibold text-white mb-1 md:mb-2 ${isMobile ? 'text-base' : 'text-lg'}`}>
              GTO 提示
            </h3>
            <p className="text-xs md:text-sm text-gray-400">
              BTN 位置是最有利的位置，你可以用更宽的范围开牌。
              在 100bb 深度下，BTN 的开牌范围可以达到约 45%。
            </p>
          </div>
        </div>
      </div>

      {/* Subscription Banner */}
      {!user?.is_subscribed && (
        <div className="bg-gradient-to-r from-yellow-900/50 to-orange-900/50 border border-yellow-700/50 rounded-xl p-4 md:p-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-3 md:gap-4">
            <div>
              <h3 className={`font-semibold text-yellow-400 mb-1 ${isMobile ? 'text-base' : 'text-lg'}`}>
                💎 升级 VIP 解锁无限训练
              </h3>
              <p className="text-xs md:text-sm text-gray-300">
                仅需 1元/月，即可享受无限次训练、详细数据分析等 VIP 专属功能
              </p>
            </div>
            <Link
              to="/subscription"
              className="px-4 md:px-6 py-2 bg-yellow-500 hover:bg-yellow-600 text-black font-semibold rounded-lg whitespace-nowrap text-sm md:text-base w-full md:w-auto text-center"
            >
              立即订阅
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
