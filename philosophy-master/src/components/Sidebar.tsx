import React from 'react';
import { NavLink } from 'react-router-dom';
import { Moon, Sun, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { PHILOSOPHERS } from '@/constants/philosophers';

interface SidebarProps {
  isDarkMode: boolean;
  toggleDarkMode: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isDarkMode, toggleDarkMode }) => {
  return (
    <div className="flex flex-col h-full w-64 bg-sidebar border-r border-sidebar-border shadow-elegant">
      {/* Header */}
      <div className="p-6 border-b border-sidebar-border">
        <h1 className="text-xl font-bold text-sidebar-foreground text-center mb-4">
          Đối thoại Triết học
        </h1>
        <Button
          variant="outline"
          size="sm"
          onClick={toggleDarkMode}
          className="w-full bg-sidebar-accent hover:bg-sidebar-accent/80 border-sidebar-border text-sidebar-accent-foreground"
        >
          {isDarkMode ? (
            <>
              <Sun className="h-4 w-4 mr-2" />
              Chế độ Sáng
            </>
          ) : (
            <>
              <Moon className="h-4 w-4 mr-2" />
              Chế độ Tối
            </>
          )}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-grow p-4">
        <div className="mb-4">
          <h2 className="text-sm font-semibold text-sidebar-foreground/70 uppercase tracking-wider mb-3">
            Triết gia
          </h2>
        </div>
        <ul className="space-y-2">
          {PHILOSOPHERS.map((philosopher) => (
            <li key={philosopher.id}>
              <NavLink
                to={`/${philosopher.id}`}
                className={({ isActive }) =>
                  `group flex items-center w-full text-left px-4 py-3 rounded-lg transition-all duration-200 hover:shadow-glow ${
                    isActive
                      ? 'bg-gradient-primary text-white shadow-glow'
                      : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                  }`
                }
              >
                <MessageSquare className="h-4 w-4 mr-3 flex-shrink-0" />
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-sm truncate">
                    {philosopher.name}
                  </div>
                  <div className="text-xs opacity-70 truncate">
                    {philosopher.school}
                  </div>
                </div>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-sidebar-border">
        <div className="text-xs text-sidebar-foreground/50 text-center">
          Khám phá trí tuệ của những bậc thầy
        </div>
      </div>
    </div>
  );
};