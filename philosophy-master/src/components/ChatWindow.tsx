import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ChatMessage } from './ChatMessage';
import { ChatMessage as ChatMessageType, MessageAuthor, Philosopher } from '@/types';
import { useToast } from '@/hooks/use-toast';

interface ChatWindowProps {
  philosopher: Philosopher;
  isDarkMode: boolean; 
}

// Component TypingIndicator không thay đổi
const TypingIndicator: React.FC<{ philosopherName: string }> = ({ philosopherName }) => (
    <div className="flex justify-start p-4">
      <div className="flex items-center gap-3 max-w-[80%]">
        <div className="w-10 h-10 rounded-full bg-philosopher-bg border-2 border-primary/30 flex items-center justify-center shadow-elegant">
          <Loader2 className="h-5 w-5 text-primary animate-spin" />
        </div>
        <div className="bg-philosopher-bg rounded-2xl px-4 py-3 shadow-elegant">
          <div className="text-xs font-medium mb-1 opacity-70">
            {philosopherName}
          </div>
          <div className="text-sm text-muted-foreground">
            Đang suy nghĩ...
          </div>
        </div>
      </div>
    </div>
);

export const ChatWindow: React.FC<ChatWindowProps> = ({ philosopher, isDarkMode }) => {
  const [messages, setMessages] = useState<ChatMessageType[]>([
    {
      author: MessageAuthor.MODEL,
      text: philosopher.openingMessage,
      timestamp: new Date()
    }
  ]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    setMessages([
      {
        author: MessageAuthor.MODEL,
        text: philosopher.openingMessage,
        timestamp: new Date()
      }
    ]);
    setUserInput('');
  }, [philosopher.id, philosopher.openingMessage]);
  
  useEffect(() => {
    if (textAreaRef.current) {
      textAreaRef.current.style.height = 'auto';
      textAreaRef.current.style.height = `${textAreaRef.current.scrollHeight}px`;
    }
  }, [userInput]);

  // --- HÀM XỬ LÝ GỬI TIN NHẮN ĐÃ ĐƯỢC SỬA LỖI UI ---
  const handleSendMessage = useCallback(async () => {
    if (!userInput.trim() || isLoading) return;

    const userMessage: ChatMessageType = {
      author: MessageAuthor.USER,
      text: userInput.trim(),
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    const currentHistory = [...messages, userMessage];
    setUserInput('');
    setIsLoading(true);

    try {
      const historyForRAG = currentHistory.map(msg => ({
        sender: msg.author,
        text: msg.text,
      }));

      const response = await fetch('http://localhost:3001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userMessage.text,
          philosopher: philosopher,
          chatHistory: historyForRAG,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`API call failed with status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let isFirstChunk = true;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        
        if (isFirstChunk) {
          // Với chunk đầu tiên, TẮT "Đang suy nghĩ..."
          setIsLoading(false); 
          
          // và TẠO MỚI tin nhắn model
          setMessages(prev => [
            ...prev,
            { author: MessageAuthor.MODEL, text: chunk, timestamp: new Date() }
          ]);
          isFirstChunk = false;
        } else {
          // Với các chunk sau, chỉ CẬP NHẬT tin nhắn cuối cùng
          setMessages(prev => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage && lastMessage.author === MessageAuthor.MODEL) {
              lastMessage.text += chunk;
            }
            return newMessages;
          });
        }
      }

    } catch (error) {
      console.error("Error during streaming:", error);
      toast({
        title: "Lỗi kết nối",
        description: "Không thể nhận phản hồi từ AI. Vui lòng thử lại.",
        variant: "destructive"
      });
      // Thêm tin nhắn báo lỗi
      setMessages(prev => [
          ...prev,
          { author: MessageAuthor.MODEL, text: "Xin lỗi, đã có lỗi kết nối đến máy chủ xử lý.", timestamp: new Date() }
      ]);
    } finally {
      // Đảm bảo isLoading luôn được tắt khi kết thúc, kể cả khi có lỗi
      setIsLoading(false);
    }
  }, [userInput, isLoading, toast, messages, philosopher]);

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div
      className="relative flex flex-col h-full bg-cover bg-center bg-fixed"
      style={{ backgroundImage: `url(${philosopher.backgroundImage})` }}
    >
      <div className="absolute inset-0 bg-background/85 backdrop-blur-sm" />

      <div className="relative z-10 flex flex-col h-full">
        {/* Phần Header */}
        <div className="bg-card/90 backdrop-blur-md border-b border-border/50 p-4 shadow-elegant">
          <div className="flex items-center gap-3">
             <div className="w-12 h-12 rounded-full bg-gradient-primary flex items-center justify-center shadow-glow">
                <i className="fas fa-brain text-white text-xl"></i>
             </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">{philosopher.title}</h2>
              <p className="text-sm text-muted-foreground">Một cuộc đối thoại triết học</p>
            </div>
          </div>
        </div>

        {/* Phần hiển thị tin nhắn */}
        <div className="flex-1 overflow-y-auto bg-gradient-bg/30 backdrop-blur-sm p-4">
          <div className="max-w-4xl mx-auto">
            {messages.map((message, index) => (
              <ChatMessage
                key={index}
                message={message}
                philosopherName={philosopher.title}
              />
            ))}
            {/* Typing Indicator chỉ hiển thị khi isLoading là true */}
            {isLoading && (
                <TypingIndicator philosopherName={philosopher.title} />
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Phần input */}
        <div className="bg-card/90 backdrop-blur-md border-t border-border/50 p-4 shadow-elegant">
          <div className="max-w-4xl mx-auto flex gap-3">
            <Textarea
              ref={textAreaRef}
              placeholder={`Chia sẻ suy nghĩ của bạn...`}
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyPress={handleKeyPress}
              className="flex-1 min-h-[48px] max-h-32 resize-none bg-background/50 border-border/50 focus:border-accent transition-colors"
              rows={1}
              disabled={isLoading}
            />
            <Button
              onClick={handleSendMessage}
              disabled={isLoading || !userInput.trim()}
              className="px-4 bg-gradient-primary hover:shadow-glow transition-all duration-300 text-white font-medium"
              size="sm"
            >
              {/* Nút bấm giờ cũng chỉ dựa vào isLoading */}
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};