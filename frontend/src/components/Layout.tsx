import React from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useMobile } from '../hooks/useMobile';

const Layout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, clearAuth } = useAuthStore();
  const { isMobile } = useMobile();

  const handleLogout = () => {
    clearAuth();
    navigate('/login');
  };

  const navItems = [
    { path: '/', label: '首页', icon: '🏠', shortLabel: '首页' },
    { path: '/training', label: '基础训练', icon: '🎯', shortLabel: '基础' },
    { path: '/fullhand', label: '牌局模拟', icon: '🎮', shortLabel: '牌局' },
    { path: '/advanced', label: '高级模拟', icon: '🚀', shortLabel: '高级' },
    { path: '/stats', label: '统计', icon: '📊', shortLabel: '统计' },
    { path: '/subscription', label: 'VIP', icon: '💎', shortLabel: 'VIP' },
  ];

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      {/* Header - 桌面端显示完整，移动端简化 */}
      <nav className="bg-gray-800 border-b border-gray-700 sticky top-0 z-50 safe-area-top">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-14 md:h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2">
              <span className="text-xl md:text-2xl">♠️</span>
              <span className="font-bold text-lg md:text-xl text-white hidden sm:block">
                GTO Trainer
              </span>
              <span className="font-bold text-lg text-white sm:hidden">
                GTO
              </span>
            </Link>

            {/* Desktop Nav Links */}
            <div className="hidden md:flex items-center space-x-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive(item.path)
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </div>

            {/* User Menu */}
            <div className="flex items-center gap-2 md:gap-4">
              {user?.is_subscribed && (
                <span className="bg-gradient-to-r from-yellow-400 to-yellow-600 text-black text-xs font-bold px-2 py-0.5 rounded-full">
                  VIP
                </span>
              )}
              <div className="text-sm text-gray-300 hidden sm:block">
                {user?.username}
              </div>
              <button
                onClick={handleLogout}
                className="text-gray-400 hover:text-white text-sm p-2"
              >
                <span className="hidden sm:inline">退出</span>
                <span className="sm:hidden">🚪</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-3 md:px-4 py-4 md:py-8 pb-24 md:pb-8">
        <Outlet />
      </main>

      {/* Mobile Bottom Navigation */}
      {isMobile && (
        <nav className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 z-50 safe-area-bottom">
          <div className="flex justify-around items-center h-16">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex flex-col items-center justify-center flex-1 h-full ${
                  isActive(item.path)
                    ? 'text-blue-400'
                    : 'text-gray-400'
                }`}
              >
                <span className="text-xl mb-0.5">{item.icon}</span>
                <span className="text-xs">{item.shortLabel}</span>
              </Link>
            ))}
          </div>
        </nav>
      )}

      {/* Footer - 桌面端显示 */}
      {!isMobile && (
        <footer className="bg-gray-800 border-t border-gray-700 mt-auto">
          <div className="max-w-7xl mx-auto px-4 py-4 text-center text-gray-400 text-sm">
            © 2024 Poker GTO Trainer. All rights reserved.
          </div>
        </footer>
      )}
    </div>
  );
};

export default Layout;
