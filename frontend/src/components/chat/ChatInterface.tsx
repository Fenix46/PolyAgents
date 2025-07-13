import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { 
  ArrowDown, 
  Volume2, 
  VolumeX, 
  RotateCcw,
  Download,
  Settings,
  Loader2
} from 'lucide-react';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import { Message, AgentResponse } from '@/types';
import { cn } from '@/lib/utils';
import { AgentBubble } from './MessageBubble';

interface ChatInterfaceProps {
  messages: Message[];
  agentResponses?: AgentResponse[];
  consensus?: { content: string; explanation?: string } | null;
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  processingStatus?: string;
  error?: string | null;
  typingAgents?: Set<string>;
  autoScroll?: boolean;
  onToggleAutoScroll?: (enabled: boolean) => void;
  soundEnabled?: boolean;
  onToggleSound?: (enabled: boolean) => void;
  agentCount?: number;
  onOpenAgentSettings?: () => void;
  onExportConversation?: () => void;
  onClearConversation?: () => void;
}

export default function ChatInterface({
  messages,
  agentResponses = [],
  consensus = null,
  onSendMessage,
  isLoading = false,
  processingStatus = '',
  typingAgents = new Set(),
  autoScroll = true,
  onToggleAutoScroll,
  soundEnabled = true,
  onToggleSound,
  agentCount = 3,
  onOpenAgentSettings,
  onExportConversation,
  onClearConversation
}: ChatInterfaceProps) {
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [showToolbar, setShowToolbar] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleScroll = () => {
    if (scrollAreaRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollAreaRef.current;
      const isScrolledToBottom = scrollHeight - scrollTop - clientHeight < 100;
      setShowScrollButton(!isScrolledToBottom);
    }
  };

  useEffect(() => {
    if (autoScroll) {
      scrollToBottom();
    }
  }, [messages, autoScroll]);

  useEffect(() => {
    const scrollArea = scrollAreaRef.current;
    if (scrollArea) {
      scrollArea.addEventListener('scroll', handleScroll);
      return () => scrollArea.removeEventListener('scroll', handleScroll);
    }
  }, []);

  return (
    <div className="flex flex-col flex-1">
      {/* Chat Header */}
      <div className="sticky top-0 z-20 flex items-center justify-between h-14 px-4 bg-slate-800/80 backdrop-blur-md border-b border-slate-700">
        <div className="flex items-center space-x-3">
          <h2 className="text-xl font-semibold">Multi-Agent Chat</h2>
          <Badge variant="outline" className="text-xs">
            {messages.length} message{messages.length !== 1 ? 's' : ''}
          </Badge>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onToggleSound?.(!soundEnabled)}
            className="w-8 h-8"
          >
            {soundEnabled ? (
              <Volume2 className="w-4 h-4" />
            ) : (
              <VolumeX className="w-4 h-4" />
            )}
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={onExportConversation}
            className="w-8 h-8"
          >
            <Download className="w-4 h-4" />
          </Button>

          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShowToolbar(!showToolbar)}
            className="w-8 h-8"
          >
            <Settings className="w-4 h-4" />
          </Button>
        </div>

        {/* Toolbar */}
        <AnimatePresence>
          {showToolbar && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="mt-4 flex items-center justify-between border-t border-border pt-4"
            >
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onToggleAutoScroll?.(!autoScroll)}
                  className={cn(
                    "text-xs",
                    autoScroll && "bg-primary/10 text-primary border-primary/50"
                  )}
                >
                  Auto-scroll {autoScroll ? 'ON' : 'OFF'}
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onOpenAgentSettings}
                  className="text-xs"
                >
                  <Settings className="w-3 h-3 mr-1" />
                  Agents
                </Button>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={onClearConversation}
                className="text-xs text-destructive border-destructive/50 hover:bg-destructive/10"
              >
                <RotateCcw className="w-3 h-3 mr-1" />
                Clear Chat
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 space-y-4 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent">
        <div className="py-6">
          <div className="space-y-6 max-w-4xl mx-auto">
            {messages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-12"
              >
                <div className="w-16 h-16 bg-gradient-primary rounded-full flex items-center justify-center mx-auto mb-4">
                  <Settings className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-2">Welcome to PolyAgents</h3>
                <p className="text-muted-foreground mb-4">
                  Start a conversation and watch our AI agents collaborate in real-time
                </p>
                <Button onClick={onOpenAgentSettings} variant="outline">
                  <Settings className="w-4 h-4 mr-2" />
                  Configure Agents
                </Button>
              </motion.div>
            ) : (
              <>
                {/* Messaggi utente e consensus */}
                {messages.map((message) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    showMetadata={true}
                  />
                ))}
                {/* Risposte agenti (sotto l'ultimo messaggio utente) */}
                {(() => {
                  return Array.isArray(agentResponses) && agentResponses.filter(Boolean).length > 0 && (
                    <div className="mt-4">
                      {agentResponses
                        .filter(Boolean)
                        .filter(agent => agent && agent.agent_id && agent.status)
                        .map((agent, idx) => {
                          return (
                            <AgentBubble 
                              key={agent.agent_id || `agent-${idx}`} 
                              {...agent} 
                              index={idx} 
                            />
                          );
                        })}
                    </div>
                  );
                })()}
                {/* Consensus (bubble separata, evidenziata) */}
                {(() => {
                  return consensus && (
                    <div className="mt-6">
                      <div className="flex items-start gap-2 mb-2">
                        <div className="w-8 h-8 rounded-full flex items-center justify-center bg-gradient-to-br from-primary to-blue-600 text-white font-bold text-lg">
                          ★
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm">Consensus</span>
                          </div>
                          <div className="mt-1 text-base font-medium whitespace-pre-line bg-primary/10 rounded-lg p-3">
                            {consensus.content}
                          </div>
                          {consensus.explanation && (
                            <div className="mt-1 text-xs text-muted-foreground italic">
                              {consensus.explanation}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </>
            )}

            {/* Typing Indicators */}
            <AnimatePresence>
              {Array.from(typingAgents).map((agentId) => (
                <motion.div
                  key={`typing-${agentId}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  <MessageBubble
                    message={{
                      id: `typing-${agentId}`,
                      conversation_id: '',
                      type: 'agent',
                      content: 'Agent is thinking...',
                      agent_id: agentId,
                      timestamp: new Date().toISOString(),
                    }}
                    isTyping={true}
                    showMetadata={false}
                  />
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Processing Status */}
            {processingStatus && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex items-center justify-center py-4"
              >
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{processingStatus}</span>
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>

      {/* Chat Input */}
      <div className="sticky bottom-0 z-10 bg-slate-800 px-4 pb-4 pt-2">
        <ChatInput
          onSendMessage={onSendMessage}
          isLoading={isLoading}
          agentCount={agentCount}
          onOpenAgentSettings={onOpenAgentSettings}
        />
      </div>
    </div>
  );
}