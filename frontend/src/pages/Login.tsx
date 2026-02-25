import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { authApi } from '../services/api';
import toast from 'react-hot-toast';
import { useMobile } from '../hooks/useMobile';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const { isMobile } = useMobile();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await authApi.login(formData.email, formData.password);
      const { access_token, user } = response.data;
      
      setAuth(user, access_token);
      toast.success('登录成功！');
      navigate('/');
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail;
      toast.error(typeof errorMsg === 'string' ? errorMsg : '登录失败，请检查邮箱和密码');
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
            Poker GTO Trainer
          </h2>
          <p className="mt-1 md:mt-2 text-gray-400 text-sm md:text-base">
            登录你的账户，开始 GTO 训练
          </p>
        </div>

        <form className="mt-6 md:mt-8 space-y-4 md:space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-3 md:space-y-4">
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
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1">
                密码
              </label>
              <input
                id="password"
                type="password"
                required
                autoComplete="current-password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="block w-full px-3 py-2.5 md:py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2.5 md:py-3 border border-transparent rounded-lg shadow-sm text-sm md:text-base font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? '登录中...' : '登录'}
          </button>
        </form>

        <div className="text-center">
          <p className="text-gray-400 text-sm">
            还没有账户？{' '}
            <Link to="/register" className="text-blue-400 hover:text-blue-300 font-medium">
              立即注册
            </Link>
          </p>
        </div>

        {/* Features */}
        <div className={`grid gap-2 md:gap-4 text-center ${isMobile ? 'grid-cols-3' : 'grid-cols-3'}`}>
          {[
            { icon: '🎯', label: 'GTO 训练' },
            { icon: '📊', label: '数据分析' },
            { icon: '💎', label: '1元/月' },
          ].map((item) => (
            <div key={item.label} className="p-2 md:p-3 bg-gray-800 rounded-lg">
              <div className={`mb-1 ${isMobile ? 'text-xl' : 'text-2xl'}`}>{item.icon}</div>
              <div className="text-xs text-gray-400">{item.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Login;
