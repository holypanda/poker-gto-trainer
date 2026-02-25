import { useState, useEffect } from 'react';

export const useMobile = () => {
  const [isMobile, setIsMobile] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768 || 
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      setIsMobile(mobile);
    };

    // 检查是否为 PWA 模式
    const checkStandalone = () => {
      const standalone = window.matchMedia('(display-mode: standalone)').matches ||
        (navigator as any).standalone === true;
      setIsStandalone(standalone);
    };

    checkMobile();
    checkStandalone();
    
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  return { isMobile, isStandalone };
};

export const useViewport = () => {
  const [height, setHeight] = useState(window.innerHeight);
  const [width, setWidth] = useState(window.innerWidth);

  useEffect(() => {
    const handleResize = () => {
      setHeight(window.innerHeight);
      setWidth(window.innerWidth);
    };

    window.addEventListener('resize', handleResize);
    // 处理键盘弹出时的高度变化
    window.addEventListener('orientationchange', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
    };
  }, []);

  return { height, width, isPortrait: height > width };
};

export const useTouchFeedback = () => {
  const [touched, setTouched] = useState<string | null>(null);

  const onTouchStart = (id: string) => {
    setTouched(id);
  };

  const onTouchEnd = () => {
    setTimeout(() => setTouched(null), 150);
  };

  return { touched, onTouchStart, onTouchEnd };
};
