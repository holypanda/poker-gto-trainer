import React, { useEffect, useState } from 'react';
import api from '../services/api';
import toast from 'react-hot-toast';

interface DashboardData {
  users: {
    total: number;
    today: number;
    vip: number;
  };
  training: {
    total: number;
    today: number;
  };
  revenue: {
    total: number;
  };
  trend: Array<{ date: string; count: number }>;
}

interface User {
  id: number;
  username: string;
  email: string;
  is_subscribed: boolean;
  total_trains: number;
  accuracy: number;
  created_at: string;
}

const Admin: React.FC = () => {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'users'>('dashboard');

  useEffect(() => {
    loadDashboard();
    loadUsers();
  }, []);

  const loadDashboard = async () => {
    try {
      const res = await api.get('/admin/dashboard');
      setDashboard(res.data);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '加载失败');
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const res = await api.get('/admin/users');
      setUsers(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  const makeVIP = async (userId: number, username: string) => {
    try {
      await api.post(`/admin/users/${userId}/make-vip`, null, {
        params: { days: 30 }
      });
      toast.success(`用户 ${username} 已升级为 VIP`);
      loadUsers();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '操作失败');
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
    <div className="max-w-6xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">🔐 管理后台</h1>

      {/* Tabs */}
      <div className="border-b border-gray-700">
        <div className="flex gap-6">
          {[
            { key: 'dashboard', label: '仪表盘' },
            { key: 'users', label: '用户管理' },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`py-3 text-sm font-medium border-b-2 transition-colors ${
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

      {activeTab === 'dashboard' && dashboard && (
        <div className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="stat-card">
              <div className="text-3xl font-bold text-white">{dashboard.users.total}</div>
              <div className="text-sm text-gray-400">总用户数</div>
              <div className="text-xs text-green-400 mt-1">+{dashboard.users.today} 今日</div>
            </div>
            <div className="stat-card">
              <div className="text-3xl font-bold text-yellow-400">{dashboard.users.vip}</div>
              <div className="text-sm text-gray-400">VIP 用户</div>
            </div>
            <div className="stat-card">
              <div className="text-3xl font-bold text-blue-400">{dashboard.training.total}</div>
              <div className="text-sm text-gray-400">总训练数</div>
              <div className="text-xs text-green-400 mt-1">+{dashboard.training.today} 今日</div>
            </div>
            <div className="stat-card">
              <div className="text-3xl font-bold text-green-400">¥{dashboard.revenue.total}</div>
              <div className="text-sm text-gray-400">总收入</div>
            </div>
          </div>

          {/* Trend Chart */}
          <div className="bg-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">最近7天训练趋势</h3>
            <div className="h-64 flex items-end gap-2">
              {dashboard.trend.map((day, i) => {
                const max = Math.max(...dashboard.trend.map(d => d.count), 1);
                const height = max > 0 ? (day.count / max) * 100 : 0;
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-2">
                    <div className="w-full bg-gray-700 rounded-t-lg relative" style={{ height: '100%' }}>
                      <div 
                        className="absolute bottom-0 left-0 right-0 bg-blue-500 rounded-t-lg transition-all"
                        style={{ height: `${height}%`, minHeight: day.count > 0 ? '4px' : '0' }}
                      />
                    </div>
                    <span className="text-xs text-gray-400">{day.date}</span>
                    <span className="text-xs text-white">{day.count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'users' && (
        <div className="bg-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-700 text-gray-300">
                <th className="text-left p-4">ID</th>
                <th className="text-left p-4">用户名</th>
                <th className="text-left p-4">邮箱</th>
                <th className="text-left p-4">VIP</th>
                <th className="text-left p-4">训练数</th>
                <th className="text-left p-4">正确率</th>
                <th className="text-left p-4">操作</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-t border-gray-700">
                  <td className="p-4 text-gray-400">{user.id}</td>
                  <td className="p-4 text-white font-medium">{user.username}</td>
                  <td className="p-4 text-gray-400">{user.email}</td>
                  <td className="p-4">
                    {user.is_subscribed ? (
                      <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-xs">
                        VIP
                      </span>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                  <td className="p-4 text-white">{user.total_trains}</td>
                  <td className="p-4 text-white">{user.accuracy}%</td>
                  <td className="p-4">
                    {!user.is_subscribed && (
                      <button
                        onClick={() => makeVIP(user.id, user.username)}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded"
                      >
                        开通VIP
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default Admin;
