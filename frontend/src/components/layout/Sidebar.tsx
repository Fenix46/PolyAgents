import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { 
  Search, 
  MessageCircle, 
  Clock, 
  Plus,
  X,
  ChevronRight
} from 'lucide-react';
import { Conversation } from '@/types';
import { cn } from '@/lib/utils';

interface SidebarProps {
  conversations: Conversation[];
  currentConversationId?: string;
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void;
  onSearchConversations: (query: string) => void;
  isCollapsed: boolean;
  isLoading?: boolean;
  searchResults?: Conversation[];
  isSearching?: boolean;
}

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onSearchConversations,
  isCollapsed,
  searchResults,
  isSearching
}: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);

  const displayConversations = (searchResults || conversations || []) as Conversation[];

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    if (query.trim()) {
      onSearchConversations(query);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setShowSearch(false);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const truncateTitle = (title: string, maxLength: number = 30) => {
    return title.length > maxLength ? `${title.substring(0, maxLength)}...` : title;
  };

  return (
    <motion.div
      className={cn(
        "w-80 shrink-0 border-r border-slate-700 bg-slate-800/60 backdrop-blur-md md:static fixed left-0 top-0 h-full transition-transform z-30",
        isCollapsed ? "translate-x-[-100%] md:translate-x-0 w-16" : "translate-x-0 w-80"
      )}
      animate={{ width: isCollapsed ? 64 : 320 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
    >
      <div className="flex flex-col h-full overflow-y-auto scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <AnimatePresence mode="wait">
          {!isCollapsed && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-semibold">Conversations</h2>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onNewConversation}
                  className="surface-hover"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>

              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search conversations..."
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  onFocus={() => setShowSearch(true)}
                  className="pl-10 pr-10 bg-background/50"
                />
                {searchQuery && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={clearSearch}
                    className="absolute right-1 top-1/2 transform -translate-y-1/2 w-6 h-6"
                  >
                    <X className="w-3 h-3" />
                  </Button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {isCollapsed && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onNewConversation}
            className="w-full surface-hover"
          >
            <Plus className="w-5 h-5" />
          </Button>
        )}
      </div>

      {/* Conversations List */}
      <ScrollArea className="flex-1 px-2">
        <div className="space-y-2 py-4">
          {isSearching && (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin w-6 h-6 border-2 border-primary border-t-transparent rounded-full" />
            </div>
          )}

          {!isSearching && displayConversations.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <MessageCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">
                {searchQuery ? 'No conversations found' : 'No conversations yet'}
              </p>
            </div>
          )}

          <AnimatePresence>
            {displayConversations.map((conversation) => (
              <motion.div
                key={conversation.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
                className={cn(
                  "group relative rounded-lg border border-transparent hover:border-border cursor-pointer transition-all duration-200",
                  currentConversationId === conversation.id && "border-primary/50 bg-primary/5"
                )}
                onClick={() => onSelectConversation(conversation.id)}
              >
                {!isCollapsed ? (
                  <div className="p-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-sm truncate">
                          {truncateTitle(conversation.title)}
                        </h3>
                        <div className="flex items-center space-x-2 mt-1">
                          <Clock className="w-3 h-3 text-muted-foreground" />
                          <span className="text-xs text-muted-foreground">
                            {formatDate(conversation.updated_at)}
                          </span>
                        </div>
                      </div>
                      <div className="flex flex-col items-end space-y-1">
                        <Badge variant="secondary" className="text-xs">
                          {conversation.message_count}
                        </Badge>
                        <div className="flex -space-x-1">
                          {conversation.agents.slice(0, 3).map((agent, index) => (
                            <div
                              key={agent.id}
                              className={cn(
                                "w-4 h-4 rounded-full border-2 border-background",
                                `bg-agent-${((index % 5) + 1) as 1 | 2 | 3 | 4 | 5}`
                              )}
                            />
                          ))}
                          {conversation.agents.length > 3 && (
                            <div className="w-4 h-4 rounded-full border-2 border-background bg-muted text-xs flex items-center justify-center">
                              +{conversation.agents.length - 3}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 flex items-center justify-center">
                    <MessageCircle className="w-5 h-5 text-muted-foreground" />
                  </div>
                )}

                {currentConversationId === conversation.id && (
                  <motion.div
                    layoutId="active-conversation"
                    className="absolute right-2 top-1/2 transform -translate-y-1/2"
                  >
                    <ChevronRight className="w-4 h-4 text-primary" />
                  </motion.div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </ScrollArea>

      {/* Search Results Info */}
      {searchQuery && !isCollapsed && (
        <div className="p-4 border-t border-border">
          <p className="text-xs text-muted-foreground">
            {searchResults?.length || 0} result{searchResults?.length === 1 ? '' : 's'} for "{searchQuery}"
          </p>
        </div>
      )}
      </div>
    </motion.div>
  );
}