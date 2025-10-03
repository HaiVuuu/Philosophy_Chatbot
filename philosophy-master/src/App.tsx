import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useParams, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Sidebar } from './components/Sidebar';
import { ChatWindow } from './components/ChatWindow';
import { PHILOSOPHERS } from './constants/philosophers';
import { Philosopher } from './types';

const queryClient = new QueryClient();

const PhilosopherChat: React.FC<{ isDarkMode: boolean }> = ({ isDarkMode }) => {
  const { id } = useParams<{ id: string }>();
  
  const philosopher = PHILOSOPHERS.find(p => p.id === id);
  
  if (!philosopher) {
    return <Navigate to={`/${PHILOSOPHERS[0].id}`} replace />;
  }

  return <ChatWindow philosopher={philosopher} isDarkMode={isDarkMode} />;
};

const MainLayout: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    // Check for saved theme preference or default to light mode
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
      setIsDarkMode(true);
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggleDarkMode = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    
    if (newMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  };

  return (
    <div className="flex h-screen bg-gradient-bg">
      <Sidebar isDarkMode={isDarkMode} toggleDarkMode={toggleDarkMode} />
      <div className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<Navigate to={`/${PHILOSOPHERS[0].id}`} replace />} />
          <Route path="/:id" element={<PhilosopherChat isDarkMode={isDarkMode} />} />
          <Route path="*" element={<Navigate to={`/${PHILOSOPHERS[0].id}`} replace />} />
        </Routes>
      </div>
    </div>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <MainLayout />
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
