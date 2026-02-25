import React, { useEffect, useState } from 'react';
import { paymentApi } from '../services/api';
import { useAuthStore } from '../store/authStore';
import { SubscriptionStatus } from '../types';
import { useMobile } from '../hooks/useMobile';
import toast from 'react-hot-toast';

const Subscription: React.FC = () => {
  const { user, updateUser } = useAuthStore();
  const { isMobile } = useMobile();
  const [status, setStatus] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const response = await paymentApi.getStatus();
      setStatus(response.data);
    } catch (error) {
      console.error('Failed to load subscription status:', error);
    }
  };

  const handleSubscribe = async () => {
    setLoading(true);
    try {
      const returnUrl = `${window.location.origin}/subscription`;
      const notifyUrl = `${window.location.origin}/api/v1/payment/notify`;
      
      const response = await paymentApi.createSubscription({
        return_url: returnUrl,
        notify_url: notifyUrl,
      });
      
      const { payment_url, order_id } = response.data;
      
      if (payment_url) {
        localStorage.setItem('pending_order_id', order_id);
        window.location.href = payment_url;
      } else {
        toast.success('开发模式：模拟支付成功');
        checkPayment(order_id);
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '创建订单失败');
    } finally {
      setLoading(false);
    }
  };

  const checkPayment = async (orderId: string) => {
    setChecking(true);
    try {
      const response = await paymentApi.verifyPayment(orderId);
      if (response.data.success) {
        toast.success('支付成功！VIP 已激活');
        updateUser({ is_subscribed: true });
        loadStatus();
        localStorage.removeItem('pending_order_id');
      } else {
        toast.error('支付未完成');
      }
    } catch (error) {
      toast.error('检查支付状态失败');
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    const pendingOrderId = localStorage.getItem('pending_order_id');
    if (pendingOrderId && !user?.is_subscribed) {
      checkPayment(pendingOrderId);
    }
  }, []);

  const handleCancel = async () => {
    try {
      await paymentApi.cancelSubscription();
      toast.success('订阅将在到期后取消');
      loadStatus();
    } catch (error) {
      toast.error('取消订阅失败');
    }
  };

  return (
    <div className={`max-w-4xl mx-auto animate-fade-in ${isMobile ? '' : ''}`}>
      <h1 className={`font-bold text-white mb-4 md:mb-6 ${isMobile ? 'text-lg' : 'text-xl md:text-2xl'}`}>
        订阅管理
      </h1>

      {/* Current Status */}
      <div className="bg-gray-800 rounded-xl p-4 md:p-6 mb-6">
        <h2 className={`font-semibold text-white mb-3 md:mb-4 ${isMobile ? 'text-base' : 'text-lg'}`}>
          当前状态
        </h2>
        
        {status?.is_subscribed ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 md:gap-4">
              <div className="w-12 h-12 md:w-16 md:h-16 bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-full flex items-center justify-center text-2xl md:text-3xl">
                💎
              </div>
              <div>
                <div className="text-lg md:text-xl font-bold text-white">
                  VIP 会员
                </div>
                <div className="text-xs md:text-sm text-gray-400">
                  到期: {status.expires_at ? new Date(status.expires_at).toLocaleDateString('zh-CN') : '永久'}
                </div>
                <div className="text-xs md:text-sm text-green-400">
                  剩余 {status.days_remaining} 天
                </div>
              </div>
            </div>
            <button
              onClick={handleCancel}
              className="px-3 md:px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-xs md:text-sm rounded-lg transition-colors"
            >
              取消续费
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 md:gap-4">
              <div className="w-12 h-12 md:w-16 md:h-16 bg-gray-700 rounded-full flex items-center justify-center text-2xl md:text-3xl">
                👤
              </div>
              <div>
                <div className="text-lg md:text-xl font-bold text-white">
                  免费用户
                </div>
                <div className="text-xs md:text-sm text-gray-400">
                  每日 {user?.free_trains_today || 20} 次免费训练
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Pricing Plans */}
      {!status?.is_subscribed && (
        <div className={`grid gap-3 md:gap-6 ${isMobile ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2'}`}>
          {/* Free Plan */}
          <div className="bg-gray-800 rounded-xl p-4 md:p-6 border border-gray-700">
            <h3 className={`font-semibold text-white mb-2 ${isMobile ? 'text-base' : 'text-lg'}`}>免费版</h3>
            <div className="text-2xl md:text-3xl font-bold text-white mb-4 md:mb-6">
              ¥0 <span className="text-xs md:text-sm text-gray-400">/ 月</span>
            </div>
            
            <ul className="space-y-2 md:space-y-3 mb-4 md:mb-6">
              {[
                '每天 20 次训练',
                '基础 GTO 策略',
                '50bb/100bb 支持',
                '基础统计分析',
              ].map((feature, i) => (
                <li key={i} className="flex items-center text-gray-300 text-sm">
                  <span className="text-green-500 mr-2">✓</span>
                  {feature}
                </li>
              ))}
            </ul>
            
            <button
              disabled
              className="w-full py-2.5 md:py-3 bg-gray-700 text-gray-400 font-bold rounded-lg cursor-not-allowed text-sm"
            >
              当前方案
            </button>
          </div>

          {/* VIP Plan */}
          <div className="bg-gradient-to-br from-purple-900/50 to-blue-900/50 rounded-xl p-4 md:p-6 border border-purple-500/50 relative overflow-hidden">
            <div className="absolute top-3 md:top-4 right-3 md:right-4 bg-gradient-to-r from-yellow-400 to-yellow-600 text-black text-xs font-bold px-2 md:px-3 py-0.5 md:py-1 rounded-full">
              推荐
            </div>
            
            <h3 className={`font-semibold text-white mb-2 ${isMobile ? 'text-base' : 'text-lg'}`}>VIP 会员</h3>
            <div className="text-2xl md:text-3xl font-bold text-white mb-4 md:mb-6">
              ¥1 <span className="text-xs md:text-sm text-gray-400">/ 月</span>
            </div>
            
            <ul className="space-y-2 md:space-y-3 mb-4 md:mb-6">
              {[
                '无限次训练',
                '完整 GTO 策略数据',
                '50bb/100bb 支持',
                '详细统计分析',
                '历史训练回顾',
                '优先客服支持',
              ].map((feature, i) => (
                <li key={i} className="flex items-center text-white text-sm">
                  <span className="text-yellow-400 mr-2">✓</span>
                  {feature}
                </li>
              ))}
            </ul>
            
            <button
              onClick={handleSubscribe}
              disabled={loading || checking}
              className="w-full py-2.5 md:py-3 bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 text-black font-bold rounded-lg transition-colors disabled:opacity-50 text-sm"
            >
              {loading ? '处理中...' : checking ? '验证中...' : '立即订阅'}
            </button>
            
            <p className="text-xs text-gray-400 text-center mt-2 md:mt-3">
              安全支付由支付宝提供
            </p>
          </div>
        </div>
      )}

      {/* FAQ */}
      <div className="mt-8 md:mt-12">
        <h2 className={`font-semibold text-white mb-3 md:mb-4 ${isMobile ? 'text-base' : 'text-lg'}`}>
          常见问题
        </h2>
        <div className="space-y-2 md:space-y-4">
          {[
            {
              q: '订阅后如何取消？',
              a: '您可以随时在订阅管理页面取消续费，取消后当前订阅期仍然有效，到期后不再扣费。'
            },
            {
              q: '支付方式有哪些？',
              a: '目前仅支持支付宝支付，后续会增加更多支付方式。'
            },
            {
              q: 'GTO 策略数据准确吗？',
              a: '我们的 GTO 策略基于行业标准求解器（Monker Solver、PioSolver）计算，是可靠的近似 GTO 策略。'
            },
            {
              q: '可以切换筹码深度吗？',
              a: '可以，VIP 用户可以训练 50bb 和 100bb 两种筹码深度。'
            },
          ].map((faq, i) => (
            <div key={i} className="bg-gray-800 rounded-lg p-3 md:p-4">
              <h3 className="font-medium text-white mb-1 md:mb-2 text-sm md:text-base">{faq.q}</h3>
              <p className="text-xs md:text-sm text-gray-400">{faq.a}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Subscription;
