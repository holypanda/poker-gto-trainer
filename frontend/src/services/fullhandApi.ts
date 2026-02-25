// 完整牌局模拟 API
// V1.1 新增

import api from './api';
import {
  FullHandSession,
  FullHandStartRequest,
  FullHandActRequest,
  FullHandActResponse,
  FullHandReview,
  FullHandStats,
} from '../types/fullhand';

export const fullhandApi = {
  // 开始一局
  start: async (data: FullHandStartRequest): Promise<FullHandSession> => {
    const response = await api.post('/fullhand/start', data);
    return response.data;
  },

  // 执行动作
  act: async (data: FullHandActRequest): Promise<FullHandActResponse> => {
    const response = await api.post('/fullhand/act', data);
    return response.data;
  },

  // 获取复盘
  getReview: async (handId: number): Promise<FullHandReview> => {
    const response = await api.get(`/fullhand/review/${handId}`);
    return response.data;
  },

  // 重打同一手
  replay: async (handId: number): Promise<FullHandSession> => {
    const response = await api.post(`/fullhand/replay/${handId}`);
    return response.data;
  },

  // 获取统计
  getStats: async (): Promise<FullHandStats> => {
    const response = await api.get('/fullhand/stats');
    return response.data;
  },
};
