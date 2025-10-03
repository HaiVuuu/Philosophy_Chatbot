import React from 'react';
import { User, BrainCircuit } from 'lucide-react'; 
import { ChatMessage as ChatMessageType, MessageAuthor } from '@/types';

interface ChatMessageProps {
  message: ChatMessageType;
  philosopherName: string;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ 
  message, 
  philosopherName 
}) => {
  const isUser = message.author === MessageAuthor.USER;

  return (
    <div className={`flex gap-4 p-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex gap-3 max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-elegant ${
          isUser 
            ? 'bg-user-bg border-2 border-accent/30' 
            : 'bg-philosopher-bg border-2 border-primary/30'
        }`}>
          {isUser ? (
            <User className="h-5 w-5 text-foreground" />
          ) : (
            <BrainCircuit className="h-5 w-5 text-primary" />
          )}
        </div>

        {/* Message Bubble */}
        <div className={`rounded-2xl px-4 py-3 shadow-elegant backdrop-blur-sm ${
          isUser 
            ? 'bg-user-bg text-foreground ml-auto' 
            : 'bg-philosopher-bg text-foreground'
        }`}>
          {/* Author Label */}
          <div className={`text-xs font-medium mb-1 opacity-70 ${
            isUser ? 'text-right' : 'text-left'
          }`}>
            {isUser ? 'Bạn' : philosopherName}
          </div>
          
          {/* Message Text */}
          <div className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.text}
          </div>
          
          {/* Timestamp */}
          {message.timestamp && (
            <div className={`text-xs opacity-50 mt-2 ${
              isUser ? 'text-right' : 'text-left'
            }`}>
              {message.timestamp.toLocaleTimeString('vi-VN', { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};