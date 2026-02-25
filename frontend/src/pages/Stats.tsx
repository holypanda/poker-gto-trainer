import React, { useEffect, useState } from 'react';
import { trainingApi } from '../services/api';
import { OverallStats } from '../types';
import { useMobile } from '../hooks/useMobile';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line
} from 'recharts';

const Stats: React.FC = () => {
  const { isMobile } = useMobile();
  const [stats, setStats] = useState<OverallStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'position' | 'daily'>('overview');

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await trainingApi.getStats();
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
        <div className="text-gray-400">加载统计中...</div>
      </div>
    );
  }

  if (!stats || stats.total_trains === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-5xl md:text-6xl mb-4">📊</div>
        <h2 className="text-lg md:text-xl font-bold text-white mb-2">暂无训练数据</h2>
        <p className="text-gray-400 text-sm md:text-base">开始训练后，这里会显示你的统计信息</p>
      </div>
    );
  }

  // Prepare chart data
  const positionData = Object.entries(stats.position_stats || {}).map(([pos, data]) => ({
    name: pos,
    total: data.total,
    correct: data.correct,
    accuracy: data.total > 0 ? Math.round((data.correct / data.total) * 100) : 0,
  }));

  const handTypeData = Object.entries(stats.hand_type_stats || {}).map(([type, data]) => ({
    name: type === 'pair' ? '对子' : type === 'suited' ? '同花' : '不同花',
    value: data.total,
    correct: data.correct,
  }));

  const dailyData = (stats.daily_stats || [])
    .slice(isMobile ? -7 : -14)
    .map(d => ({
      date: d.date.slice(5),
      count: d.train_count,
      accuracy: d.accuracy,
    }));

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'];

  return (
    <div className="space-y-4 md:space-y-6 animate-fade-in">
      <h1 className={`font-bold text-white ${isMobile ? 'text-lg' : 'text-xl md:text-2xl'}`}>
        训练统计
      </h1>

      {/* Summary Cards */}
      <div className={`grid gap-2 md:gap-4 ${isMobile ? 'grid-cols-2' : 'grid-cols-2 md:grid-cols-4'}`}>
        <div className="stat-card p-3 md:p-4">
          <div className={`font-bold text-white ${isMobile ? 'text-xl' : 'text-2xl md:text-3xl'}`}>
            {stats.total_trains}
          </div>
          <div className="text-xs md:text-sm text-gray-400">总训练次数</div>
        </div>
        <div className="stat-card p-3 md:p-4">
          <div className={`font-bold text-green-400 ${isMobile ? 'text-xl' : 'text-2xl md:text-3xl'}`}>
            {stats.accuracy}%
          </div>
          <div className="text-xs md:text-sm text-gray-400">整体正确率</div>
        </div>
        <div className="stat-card p-3 md:p-4">
          <div className={`font-bold text-yellow-400 ${isMobile ? 'text-xl' : 'text-2xl md:text-3xl'}`}>
            {stats.streak_days}
          </div>
          <div className="text-xs md:text-sm text-gray-400">连续天数</div>
        </div>
        <div className="stat-card p-3 md:p-4">
          <div className={`font-bold text-blue-400 ${isMobile ? 'text-xl' : 'text-2xl md:text-3xl'}`}>
            {stats.correct_trains}
          </div>
          <div className="text-xs md:text-sm text-gray-400">正确次数</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-700">
        <div className="flex gap-4 md:gap-6">
          {[
            { key: 'overview', label: '概览' },
            { key: 'position', label: '位置' },
            { key: 'daily', label: '趋势' },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`py-2 md:py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-4 md:space-y-6">
          {/* Hand Type Distribution */}
          <div className="bg-gray-800 rounded-xl p-4 md:p-6">
            <h3 className={`font-semibold text-white mb-3 md:mb-4 ${isMobile ? 'text-base' : 'text-lg'}`}>
              手牌类型分布
            </h3>
            <div className={`${isMobile ? 'h-48' : 'h-64'}`}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={handTypeData}
                    cx="50%"
                    cy="50%"
                    innerRadius={isMobile ? 40 : 60}
                    outerRadius={isMobile ? 60 : 80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {handTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', fontSize: isMobile ? 12 : 14 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-3 md:gap-4 mt-3 md:mt-4 flex-wrap">
              {handTypeData.map((item, index) => (
                <div key={item.name} className="flex items-center gap-1.5 md:gap-2">
                  <div 
                    className="w-2.5 md:w-3 h-2.5 md:h-3 rounded-full" 
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className="text-xs md:text-sm text-gray-400">{item.name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Accuracy Summary */}
          <div className="bg-gray-800 rounded-xl p-4 md:p-6">
            <h3 className={`font-semibold text-white mb-3 md:mb-4 ${isMobile ? 'text-base' : 'text-lg'}`}>
              正确率分析
            </h3>
            <div className="space-y-3 md:space-y-4">
              {handTypeData.map((type) => {
                const accuracy = type.value > 0 ? Math.round((type.correct / type.value) * 100) : 0;
                return (
                  <div key={type.name}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-300 text-xs md:text-sm">{type.name}</span>
                      <span className="text-white text-xs md:text-sm">{accuracy}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all"
                        style={{ width: `${accuracy}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'position' && (
        <div className="bg-gray-800 rounded-xl p-4 md:p-6">
          <h3 className={`font-semibold text-white mb-3 md:mb-4 ${isMobile ? 'text-base' : 'text-lg'}`}>
            各位置表现
          </h3>
          <div className={`${isMobile ? 'h-56' : 'h-80'}`}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={positionData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#9CA3AF" fontSize={isMobile ? 10 : 12} />
                <YAxis stroke="#9CA3AF" fontSize={isMobile ? 10 : 12} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', fontSize: isMobile ? 12 : 14 }}
                />
                <Bar dataKey="total" name="总次数" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="correct" name="正确次数" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {activeTab === 'daily' && (
        <div className="bg-gray-800 rounded-xl p-4 md:p-6">
          <h3 className={`font-semibold text-white mb-3 md:mb-4 ${isMobile ? 'text-base' : 'text-lg'}`}>
            每日训练趋势 (最近{isMobile ? '7' : '14'}天)
          </h3>
          <div className={`${isMobile ? 'h-56' : 'h-80'}`}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dailyData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#9CA3AF" fontSize={isMobile ? 10 : 12} />
                <YAxis yAxisId="left" stroke="#9CA3AF" fontSize={isMobile ? 10 : 12} />
                <YAxis yAxisId="right" orientation="right" stroke="#9CA3AF" domain={[0, 100]} fontSize={isMobile ? 10 : 12} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', fontSize: isMobile ? 12 : 14 }}
                />
                <Bar yAxisId="left" dataKey="count" name="训练次数" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                <Line 
                  yAxisId="right" 
                  type="monotone" 
                  dataKey="accuracy" 
                  name="正确率" 
                  stroke="#10B981" 
                  strokeWidth={2}
                  dot={{ fill: '#10B981', r: isMobile ? 3 : 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

export default Stats;
