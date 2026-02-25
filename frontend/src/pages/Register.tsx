import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../services/api';
import toast from 'react-hot-toast';
import { useMobile } from '../hooks/useMobile';

const Register: React.FC = () => {
  const navigate = useNavigate();
  const { isMobile } = useMobile();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      toast.error('两次输入的密码不一致');
      return;
    }

    if (formData.password.length < 6) {
      toast.error('密码至少需要6个字符');
      return;
    }

    setLoading(true);

    try {
      await authApi.register({
        email: formData.email,
        username: formData.username,
        password: formData.password,
      });
      
      toast.success('注册成功！请登录');
      navigate('/login');
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail;
      toast.error(typeof errorMsg === 'string' ? errorMsg : '注册失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 px-4 py-6">
      <div className="w-full max-w-md space-y-4 md:space-y-8">
        <div className="text-center">
          <span className={`${isMobile ? 'text-4xl' : 'text-5xl'}`}>♠️</span>
          <h2 className={`mt-3 md:mt-4 font-bold text-white ${isMobile ? 'text-2xl' : 'text-3xl'}`}>
            创建账户
          </h2>
          <p className="mt-1 md:mt-2 text-gray-400 text-sm md:text-base">
            加入 Poker GTO Trainer，提升你的牌技
          </p>
        </div>

        <form className="mt-6 md:mt-8 space-y-3 md:space-y-4" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-1">
              邮箱
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              inputMode="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="block w-full px-3 py-2.5 md:py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
              placeholder="your@email.com"
            />
          </div>

          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-1">
              用户名
            </label>
            <input
              id="username"
              type="text"
              required
              autoComplete="username"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              className="block w-full px-3 py-2.5 md:py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
              placeholder="poker_pro"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1">
              密码
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="new-password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="block w-full px-3 py-2.5 md:py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
              placeholder="••••••••"
            />
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-300 mb-1">
              确认密码
            </label>
            <input
              id="confirmPassword"
              type="password"
              required
              autoComplete="new-password"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              className="block w-full px-3 py-2.5 md:py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2.5 md:py-3 border border-transparent rounded-lg shadow-sm text-sm md:text-base font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors mt-2"
          >
            {loading ? '注册中...' : '注册'}
          </button>
        </form>

        <div className="text-center">
          <p className="text-gray-400 text-sm">
            已有账户？{' '}
            <Link to="/login" className="text-blue-400 hover:text-blue-300 font-medium">
              立即登录
            </Link>
          </p>
        </div>

        {/* Benefits */}
        <div className="bg-gray-800 rounded-xl p-3 md:p-4">
          <h3 className="text-sm font-medium text-white mb-2 md:mb-3">注册即可获得：</h3>
          <ul className="space-y-1.5 md:space-y-2 text-xs md:text-sm text-gray-400">
            {[
              '每天 20 次免费训练',
              '完整的 GTO 策略数据',
              '详细的统计分析',
              '6max 50bb/100bb 支持',
            ].map((item, i) => (
              <li key={i} className="flex items-center">
                <span className="text-green-500 mr-2">✓</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Register;
