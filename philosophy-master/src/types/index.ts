export enum MessageAuthor {
  USER = 'user',
  MODEL = 'model',
}

export interface ChatMessage {
  author: MessageAuthor;
  text: string;
  timestamp?: Date;
}

export interface Philosopher {
  id: string;
  name: string;
  school: string;
  title: string;
  openingMessage: string;
  backgroundImage: string;
  avatar?: string;
  accentColor: string;
  systemInstruction: string;
}

export interface ChatSession {
  philosopherId: string;
  messages: ChatMessage[];
  lastActivity: Date;
}