// User Types
export interface User {
  id: number;
  email: string;
  username: string;
  total_trains: number;
  correct_trains: number;
  accuracy: number;
  streak_days: number;
  is_subscribed: boolean;
  subscription_expires_at: string | null;
  free_trains_today: number;
  free_trains_reset_at: string | null;
  created_at: string;
}

export interface UserStats {
  total_trains: number;
  correct_trains: number;
  accuracy: number;
  streak_days: number;
  is_subscribed: boolean;
  subscription_expires_at: string | null;
  free_trains_today: number;
  free_trains_reset_at: string | null;
}

// Training Types
export type Position = 'UTG' | 'MP' | 'CO' | 'BTN' | 'SB' | 'BB';
export type StackSize = 50 | 100;

export interface TrainingScenario {
  id: number;
  hand: string;
  position: string;
  action_to_you: string;
  options: string[];
  difficulty?: string;  // easy, normal, hard
  time_limit?: number;  // 答题时间限制（秒）
}

export interface TrainingSession {
  id: number;
  stack_size: number;
  position: string;
  action_to_you: string;
  scenarios: TrainingScenario[];
  current_index: number;
  completed: boolean;
  created_at: string;
}

export interface TrainingResult {
  is_correct: boolean;
  correct_action: string;
  user_action: string;
  gto_frequency: Record<string, number>;
  explanation: string;
  score?: number;         // 本题得分
  time_bonus?: boolean;   // 是否有速度奖励
}

export interface TrainingRecord {
  hand: string;
  position: string;
  vs_position: string | null;
  action_to_you: string;
  user_action: string;
  correct_action: string;
  is_correct: boolean;
  response_time_ms: number | null;
}

export interface TrainingCompleteResponse {
  session_id: number;
  total_scenarios: number;
  correct_count: number;
  accuracy: number;
  records: TrainingRecord[];
}

export interface DailyStats {
  date: string;
  train_count: number;
  correct_count: number;
  accuracy: number;
}

export interface OverallStats {
  total_trains: number;
  correct_trains: number;
  accuracy: number;
  streak_days: number;
  daily_stats: DailyStats[];
  position_stats: Record<string, { total: number; correct: number }>;
  hand_type_stats: Record<string, { total: number; correct: number }>;
}

export interface HandAdvice {
  hand: string;
  position: string;
  vs_position: string | null;
  action_to_you: string;
  stack_size: number;
  advice: string;
  gto_frequency: Record<string, number>;
  explanation: string;
}

// Subscription Types
export interface SubscriptionStatus {
  is_subscribed: boolean;
  expires_at: string | null;
  days_remaining: number;
}

export interface PaymentResponse {
  order_id: string;
  payment_url: string | null;
  qr_code: string | null;
}

// Config Types
export const POSITIONS: { value: Position; label: string; color: string }[] = [
  { value: 'UTG', label: 'UTG (枪口位)', color: 'bg-red-100 text-red-800' },
  { value: 'MP', label: 'MP (中位)', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'CO', label: 'CO ( cutoff )', color: 'bg-green-100 text-green-800' },
  { value: 'BTN', label: 'BTN (按钮位)', color: 'bg-blue-100 text-blue-800' },
  { value: 'SB', label: 'SB (小盲)', color: 'bg-purple-100 text-purple-800' },
  { value: 'BB', label: 'BB (大盲)', color: 'bg-gray-100 text-gray-800' },
];

export const ACTIONS_TO_YOU = [
  { value: 'open', label: '开牌 (前面都弃牌)' },
  { value: 'vs_limp', label: '面对溜入 (Limp)' },
  { value: 'vs_raise_2bb', label: '面对 2BB 加注' },
  { value: 'vs_raise_2.5bb', label: '面对 2.5BB 加注' },
  { value: 'vs_raise_3bb', label: '面对 3BB 加注' },
  { value: 'vs_3bet', label: '面对 3bet' },
  { value: 'vs_all_in', label: '面对 All-in' },
];

export const ACTION_LABELS: Record<string, string> = {
  'fold': '弃牌',
  'check': '过牌',
  'call': '跟注',
  'limp': '溜入',
  'raise_2bb': '加注到 2BB',
  'raise_2.5bb': '加注到 2.5BB',
  'raise_3bb': '加注到 3BB',
  'raise_4bb': '加注到 4BB',
  'raise_3x': '3bet (3倍)',
  'raise_all_in': 'All-in',
  'all_in': 'All-in',
};

// Re-export fullhand types
export * from './fullhand';
