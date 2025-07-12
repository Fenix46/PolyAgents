import { useState } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { 
  User, 
  Bot, 
  Clock, 
  Copy, 
  Check, 
  Zap,
  Users,
  AlertCircle
} from 'lucide-react';
import { Message } from '@/types';
import { cn } from '@/lib/utils';

interface MessageBubbleProps {
  message: Message;
  isTyping?: boolean;
  showMetadata?: boolean;
}

export default function MessageBubble({ 
  message, 
  isTyping = false, 
  showMetadata = true 
}: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getAgentColor = (agentId?: string) => {
    if (!agentId) return 'bg-muted';
    const index = parseInt(agentId.slice(-1)) || 1;
    return `bg-agent-${((index % 5) + 1) as 1 | 2 | 3 | 4 | 5}`;
  };

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'user':
        return <User className="w-4 h-4" />;
      case 'consensus':
        return <Users className="w-4 h-4" />;
      case 'system':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Bot className="w-4 h-4" />;
    }
  };

  const getBubbleClass = () => {
    switch (message.type) {
      case 'user':
        return 'user-bubble ml-auto';
      case 'consensus':
        return 'consensus-bubble mx-auto';
      case 'system':
        return 'system-bubble mx-auto';
      default:
        return `agent-bubble agent-${message.agent_id ? (parseInt(message.agent_id.slice(-1)) || 1) % 5 + 1 : 1}`;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={cn(
        "flex items-start space-x-3 group",
        message.type === 'user' ? 'justify-end' : 'justify-start'
      )}
    >
      {message.type !== 'user' && (
        <Avatar className="w-8 h-8 mt-1">
          <AvatarFallback className={cn(
            "text-white",
            message.type === 'system' ? 'bg-muted' : 
            message.type === 'consensus' ? 'bg-accent' :
            getAgentColor(message.agent_id)
          )}>
            {getAgentIcon(message.type)}
          </AvatarFallback>
        </Avatar>
      )}

      <div className={cn(
        "flex flex-col space-y-1",
        message.type === 'user' ? 'items-end' : 'items-start'
      )}>
        {/* Message Header */}
        {showMetadata && message.type !== 'system' && (
          <div className="flex items-center space-x-2 text-xs text-muted-foreground">
            {message.type === 'user' ? (
              <span>You</span>
            ) : message.type === 'consensus' ? (
              <span>Consensus</span>
            ) : (
              <span>Agent {message.agent_id || 'Unknown'}</span>
            )}
            <span>•</span>
            <span>{formatTimestamp(message.timestamp)}</span>
            {message.metadata?.response_time && (
              <>
                <span>•</span>
                <div className="flex items-center space-x-1">
                  <Zap className="w-3 h-3" />
                  <span>{message.metadata.response_time}ms</span>
                </div>
              </>
            )}
          </div>
        )}

        {/* Message Content */}
        <div className={cn(getBubbleClass(), "relative")}>
          {isTyping ? (
            <div className="flex items-center space-x-2">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-current rounded-full animate-typing" />
                <div className="w-2 h-2 bg-current rounded-full animate-typing" style={{ animationDelay: '0.2s' }} />
                <div className="w-2 h-2 bg-current rounded-full animate-typing" style={{ animationDelay: '0.4s' }} />
              </div>
              <span className="text-sm text-muted-foreground">typing...</span>
            </div>
          ) : (
            <div className="prose prose-sm max-w-none prose-invert">
              <ReactMarkdown
                components={{
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  code: ({ children, className }) => (
                    <code className={cn(
                      "bg-surface rounded px-1 py-0.5 text-sm font-mono",
                      className
                    )}>
                      {children}
                    </code>
                  ),
                  pre: ({ children }) => (
                    <pre className="bg-surface rounded p-3 overflow-x-auto">
                      {children}
                    </pre>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}

          {/* Copy Button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => copyToClipboard(message.content)}
            className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-opacity w-6 h-6 bg-surface border border-border"
          >
            {copied ? (
              <Check className="w-3 h-3 text-success" />
            ) : (
              <Copy className="w-3 h-3" />
            )}
          </Button>
        </div>

        {/* Metadata */}
        {showMetadata && message.metadata && (
          <div className="flex items-center space-x-2 text-xs text-muted-foreground">
            {message.metadata.model && (
              <Badge variant="outline" className="text-xs">
                {message.metadata.model}
              </Badge>
            )}
            {message.metadata.temperature && (
              <Badge variant="outline" className="text-xs">
                T: {message.metadata.temperature}
              </Badge>
            )}
          </div>
        )}
      </div>

      {message.type === 'user' && (
        <Avatar className="w-8 h-8 mt-1">
          <AvatarFallback className="bg-primary text-primary-foreground">
            <User className="w-4 h-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </motion.div>
  );
}