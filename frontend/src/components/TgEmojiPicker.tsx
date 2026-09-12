import React, { useState, useRef, useEffect } from 'react';
import { TELEGRAM_ANIMATED_EMOJIS, TgAnimatedEmoji } from './TgEmoji';
import { Smile, Sparkles } from 'lucide-react';

interface TgEmojiPickerProps {
  onSelectEmoji: (code: string) => void;
  className?: string;
}

export const TgEmojiPicker: React.FC<TgEmojiPickerProps> = ({ onSelectEmoji, className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className={`relative inline-block ${className}`} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 text-gray-400 hover:text-amber-400 hover:bg-white/10 rounded-full transition-all duration-200 flex items-center gap-1 group"
        title="Telegram Animated Emojis (Premium)"
      >
        <Smile className="w-5 h-5 transition-transform group-hover:scale-110" />
        <Sparkles className="w-3 h-3 text-amber-400 animate-pulse" />
      </button>

      {isOpen && (
        <div className="absolute bottom-full right-0 mb-2 w-64 bg-slate-900/95 backdrop-blur-md border border-slate-700/80 rounded-2xl p-3 shadow-2xl z-50 animate-in fade-in slide-in-from-bottom-2 duration-200">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
            <span className="text-xs font-semibold text-amber-400 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" /> Telegram Custom Emojis
            </span>
            <span className="text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded-full font-mono">
              PREMIUM
            </span>
          </div>

          <div className="grid grid-cols-4 gap-2 max-h-48 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-slate-700">
            {Object.entries(TELEGRAM_ANIMATED_EMOJIS).map(([code, emoji]) => (
              <button
                key={code}
                type="button"
                onClick={() => {
                  onSelectEmoji(code);
                  setIsOpen(false);
                }}
                className="p-2 hover:bg-slate-800 rounded-xl flex items-center justify-center transition-all duration-150 transform hover:scale-125"
                title={emoji.name}
              >
                <img
                  src={emoji.url}
                  alt={emoji.name}
                  className="w-7 h-7 object-contain select-none pointer-events-none"
                />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
