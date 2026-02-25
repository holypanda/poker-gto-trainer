// 完整牌局模拟类型定义
// V1.1 新增

export type Street = 'preflop' | 'flop' | 'turn' | 'river' | 'showdown';
export type GameStatus = 'INIT' | 'PREFLOP' | 'FLOP_DECISION' | 'FAST_FORWARD' | 'ENDED';
export type PotType = 'SRP' | '3BP' | '4BP';
export type IPOOP = 'IP' | 'OOP';
export type SPRBucket = 'LOW' | 'MED' | 'HIGH';
export type HandBucket = 'made_strong' | 'made_medium' | 'made_weak' | 'draw_strong' | 'draw_weak' | 'air';
export type Grade = 'PERFECT' | 'ACCEPTABLE' | 'WRONG';

export interface PlayerState {
  seat: number;
  position: string; // UTG, MP, CO, BTN, SB, BB
  stack: number;
  in_hand: boolean;
  committed_this_street: number;
  total_committed: number;
  hole_cards?: string[];
  is_hero: boolean;
  is_active: boolean;
}

export interface ActionRecord {
  street: string;
  seat: number;
  position: string;
  action: string;
  amount?: number;
  pot_after: number;
  timestamp?: string;
}

export interface KeySpotInfo {
  street: string;
  context_id: string;
  pot_type?: PotType;
  ip_oop?: IPOOP;
  spr_bucket?: SPRBucket;
  board?: string[];
  hero_hand: string;
  hero_hand_bucket?: HandBucket;
  legal_actions: string[];
  strategy?: Record<string, number>;
  best_action: string;
}

export interface GameState {
  status: GameStatus;
  street: Street;
  players: PlayerState[];
  button_seat: number;
  sb_seat: number;
  bb_seat: number;
  pot: number;
  current_bet: number;
  community_cards: string[];
  to_act_seat?: number;
  hero_seat: number;
  hero_cards: string[];
  min_raise_to?: number;
}

export interface FullHandSession {
  hand_id: number;
  state: GameState;
  legal_actions: string[];
  action_log: ActionRecord[];
  is_key_spot: boolean;
  key_spot_info?: KeySpotInfo;
}

export interface FullHandStartRequest {
  table_type: string;
  stack_bb: number;
  ai_level: string;
  replay_seed?: string;
}

export interface FullHandActRequest {
  hand_id: number;
  action: string;
  amount?: number;
}

export interface FullHandActResponse {
  state: GameState;
  legal_actions: string[];
  is_key_spot: boolean;
  key_spot_info?: KeySpotInfo;
  final_result?: {
    result_bb: number;
    ended_by: string;
  };
  review_payload?: FullHandReview;
}

export interface PreflopSpotReview {
  context_id: string;
  strategy?: Record<string, number>;
  user_action: string;
  user_action_prob?: number;
  best_action: string;
  grade: Grade;
}

export interface FlopSpotReview {
  context_id: string;
  pot_type: PotType;
  ip_oop: IPOOP;
  spr_bucket: SPRBucket;
  board: string[];
  hero_hand: string;
  hero_hand_bucket: HandBucket;
  strategy?: Record<string, number>;
  legal_actions: string[];
  user_action: string;
  user_action_prob?: number;
  best_action: string;
  grade: Grade;
  explanation: string;
}

export interface FullHandReview {
  hand_id: number;
  result_bb: number;
  ended_by: string;
  action_log: ActionRecord[];
  preflop_spot?: PreflopSpotReview;
  flop_spot?: FlopSpotReview;
  can_replay: boolean;
}

export interface FullHandStats {
  total_hands: number;
  total_result_bb: number;
  avg_result_bb: number;
  preflop_accuracy?: number;
  flop_accuracy?: number;
  today_hands: number;
  today_remaining: number;
  is_pro: boolean;
}

// 下注尺度
export interface BetSizes {
  bet33: number;
  bet75: number;
  bet125: number;
}

// 动作标签映射
export const ACTION_LABELS: Record<string, string> = {
  fold: '弃牌',
  check: '过牌',
  call: '跟注',
  bet: '下注',
  raise: '加注',
  allin: '全下',
  bet33: '33% 底池',
  bet75: '75% 底池',
  bet125: '125% 底池',
  raise75: '75% 底池',
  raise125: '125% 底池',
  sb: '小盲',
  bb: '大盲',
};

// 位置颜色
export const POSITION_COLORS: Record<string, string> = {
  UTG: 'text-red-400',
  MP: 'text-orange-400',
  CO: 'text-yellow-400',
  BTN: 'text-green-400',
  SB: 'text-blue-400',
  BB: 'text-purple-400',
};

// 评级颜色
export const GRADE_COLORS: Record<Grade, string> = {
  PERFECT: 'text-green-400',
  ACCEPTABLE: 'text-yellow-400',
  WRONG: 'text-red-400',
};

// 评级图标
export const GRADE_ICONS: Record<Grade, string> = {
  PERFECT: '✅',
  ACCEPTABLE: '⚠️',
  WRONG: '❌',
};
