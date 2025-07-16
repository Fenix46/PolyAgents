import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { Send, Loader2, MoreHorizontal, ThumbsUp, ThumbsDown, MessageSquare, ArrowUp, Settings, Download, RotateCcw, Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';
import { Card } from '@/components/ui/card';
import { Message, AgentResponse } from '@/types';
import { ConsensusVisualization } from '@/components/consensus/ConsensusVisualization';
import { InteractiveFeedback } from '@/components/feedback/InteractiveFeedback';
import { VirtualizedChatList } from './VirtualizedChatList';
import { useLazyConversation } from '@/hooks/useLazyConversation';
import { cachedApiCall } from '@/services/apiCacheService';
import { cn } from '@/lib/utils';
import MessageBubble from './MessageBubble';

interface ChatInterfaceProps {
  messages: Message[];
  agentResponses: AgentResponse[];
  onSendMessage: (content: string) => void;
  isTyping?: boolean;
  showMetadata?: boolean;
  conversationId?: string;
  fetchMoreMessages?: (conversationId: string, offset: number, limit: number) => Promise<{
    messages: Message[];
    agentResponses: AgentResponse[];
    hasMore: boolean;
  }>;
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
  messages: initialMessages,
  agentResponses: initialAgentResponses = [],
  onSendMessage,
  isTyping = false,
  showMetadata = true,
  conversationId = 'current',
  fetchMoreMessages,
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
  const isAtBottomRef = useRef<boolean>(true);
  const { register, handleSubmit, reset, watch } = useForm<{ message: string }>({
    defaultValues: { message: '' }
  });
  const messageContent = watch('message');

  // Implementazione del fetcher per il lazy loading
  const defaultFetchMoreMessages = useCallback(async (convId: string, offset: number, limit: number) => {
    if (!fetchMoreMessages) {
      return { messages: [], agentResponses: [], hasMore: false };
    }
    
    return cachedApiCall(
      `/api/conversations/${convId}/messages?offset=${offset}&limit=${limit}`,
      () => fetchMoreMessages(convId, offset, limit)
    );
  }, [fetchMoreMessages]);

  // Utilizzo dell'hook per il lazy loading delle conversazioni
  const {
    messages,
    agentResponses,
    loading,
    hasMore,
    loadMoreMessages,
    addMessage
  } = useLazyConversation({
    conversationId,
    initialMessages: initialMessages,
    initialAgentResponses: initialAgentResponses,
    pageSize: 20,
    fetchMessages: defaultFetchMoreMessages
  });

  const handleSendMessage = (data: { message: string }) => {
    if (data.message.trim()) {
      onSendMessage(data.message.trim());
      reset();
    }
  };

  // Gestione del feedback dell'utente
  const handleSubmitFeedback = (messageId: string, feedback: any) => {
    console.log('Feedback ricevuto:', messageId, feedback);
    // Qui puoi implementare la logica per inviare il feedback al backend
  };

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

      {/* Area messaggi con virtualizzazione */}
      <div className="flex-1 relative overflow-hidden">
        {/* Pulsante per caricare più messaggi */}
        {hasMore && (
          <div className="absolute top-2 left-1/2 transform -translate-x-1/2 z-10">
            <Button 
              variant="outline" 
              size="sm" 
              className="flex items-center gap-1 bg-background/80 backdrop-blur-sm"
              onClick={() => loadMoreMessages()}
              disabled={loading}
            >
              {loading ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <ArrowUp className="h-3 w-3" />
              )}
              Carica messaggi precedenti
            </Button>
          </div>
        )}
        
        {/* Lista messaggi virtualizzata */}
        <VirtualizedChatList
          messages={messages}
          agentResponses={agentResponses}
          onSubmitFeedback={handleSubmitFeedback}
          isAtBottomRef={isAtBottomRef}
          showMetadata={showMetadata}
        />
        
        {/* Indicatore di digitazione */}
        <AnimatePresence>
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="absolute bottom-0 left-0 right-0 flex items-center space-x-2 p-4 bg-background/80 backdrop-blur-sm"
            >
              <div className="bg-primary/10 rounded-full p-2">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
              </div>
              <p className="text-sm text-muted-foreground">L'assistente sta scrivendo...</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Chat Input */}
      <div className="p-4 border-t border-slate-600">
        <form onSubmit={handleSubmit(handleSendMessage)}>
          <div className="relative">
            <Textarea
              {...register('message')}
              className="w-full p-4 text-sm text-muted-foreground border border-slate-600 rounded-lg focus:ring-primary focus:border-primary"
              placeholder="Scrivi un messaggio..."
            />
            <div className="absolute bottom-2 right-2 flex items-center gap-2">
              {onOpenAgentSettings && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={onOpenAgentSettings}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <Settings className="w-4 h-4" />
                </Button>
              )}
              <Button
                type="submit"
                variant="primary"
                size="sm"
                disabled={isTyping || !messageContent.trim()}
              >
                {isTyping ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}