import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  Send, 
  Paperclip, 
  Smile,
  Zap,
  Settings
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
  agentCount?: number;
  onOpenAgentSettings?: () => void;
}

export default function ChatInput({
  onSendMessage,
  isLoading = false,
  disabled = false,
  placeholder = "Type your message... (Ctrl + Enter to send)",
  agentCount = 3,
  onOpenAgentSettings
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading && !disabled) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  return (
    <motion.div
      className="sticky bottom-0 bg-background/80 backdrop-blur-sm border-t border-border p-4"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <form onSubmit={handleSubmit} className="space-y-3">
        {/* Agent Status Bar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="text-xs">
              <Zap className="w-3 h-3 mr-1" />
              {agentCount} Agent{agentCount !== 1 ? 's' : ''} Active
            </Badge>
            <Badge variant="outline" className="text-xs text-success">
              Ready
            </Badge>
          </div>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={onOpenAgentSettings}
            className="text-xs"
          >
            <Settings className="w-3 h-3 mr-1" />
            Configure
          </Button>
        </div>

        {/* Input Area */}
        <div className={cn(
          "relative bg-surface rounded-lg border border-border transition-all duration-200",
          isFocused && "border-primary/50 shadow-lg shadow-primary/10"
        )}>
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            className="min-h-[60px] max-h-[200px] resize-none border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 pr-16"
          />

          {/* Input Actions */}
          <div className="absolute bottom-3 right-3 flex items-center space-x-2">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="w-8 h-8 text-muted-foreground hover:text-foreground"
              disabled={disabled || isLoading}
            >
              <Paperclip className="w-4 h-4" />
            </Button>
            
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="w-8 h-8 text-muted-foreground hover:text-foreground"
              disabled={disabled || isLoading}
            >
              <Smile className="w-4 h-4" />
            </Button>
            
            <Button
              type="submit"
              size="icon"
              disabled={!message.trim() || isLoading || disabled}
              className="w-8 h-8 bg-primary hover:bg-primary/90"
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Helper Text */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center space-x-2">
            <kbd className="px-2 py-1 bg-surface rounded text-xs">Ctrl</kbd>
            <span>+</span>
            <kbd className="px-2 py-1 bg-surface rounded text-xs">Enter</kbd>
            <span>to send</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <span>{message.length}/2000</span>
            {message.length > 1800 && (
              <Badge variant="destructive" className="text-xs">
                Limit approaching
              </Badge>
            )}
          </div>
        </div>
      </form>
    </motion.div>
  );
}