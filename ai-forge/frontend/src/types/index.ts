export interface User {
  id: number;
  email: string;
  nickname: string;
  role: "user" | "admin";
  created_at: string;
}
export interface Conversation {
  id: number;
  title: string;
  model_type: string;
  created_at: string;
  updated_at: string;
}
export interface Message {
  id?: number;
  role: "user" | "assistant";
  content: string;
  token_usage?: number;
  created_at?: string;
  tools?: ToolEvent[];
}
export interface KnowledgeBase {
  id: number;
  name: string;
  description: string;
  created_at: string;
}
export interface ToolEvent {
  type: "tool_start" | "tool_end";
  name: string;
  input?: unknown;
  output?: unknown;
}
export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}
