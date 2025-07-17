import { useState } from 'react';
import Header from '@/components/layout/Header';
import Sidebar from '@/components/layout/Sidebar';
import ChatInterface from '@/components/chat/ChatInterface';
import AgentStatusPanel from '@/components/agents/AgentStatusPanel';
import { usePolyAgents } from '@/hooks/usePolyAgents';
import { ChatRequest } from '@/types';

const Index = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [rightPanelVisible, setRightPanelVisible] = useState(true);
  
  const {
    conversations,
    currentConversation,
    messages,
    agentResponses,
    consensus,
    connectionStatus,
    systemHealth,
    systemStats,
    isLoading,
    processingStatus,
    error,
    setError,
    loadConversation,
    sendMessage,
    searchConversations,
    disconnect,
  } = usePolyAgents();

  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return;

    const request: ChatRequest = {
      message: message.trim(),
      conversation_id: currentConversation?.id,
      agents: {
        count: 3,
        turns: 2,
        temperature: 0.7,
        model: 'gemini-pro'
      }
    };

    try {
      console.log('Index: Sending message:', request);
      await sendMessage(request);
      console.log('Index: Message sent successfully');
    } catch (err) {
      console.error('Index: Failed to send message:', err);
      // L'errore viene già gestito nell'hook usePolyAgents
      // Qui possiamo aggiungere ulteriori azioni se necessario
    }
  };

  const handleSelectConversation = (conversationId: string) => {
    loadConversation(conversationId);
  };

  const handleNewConversation = () => {
    // Create a new conversation by sending a message without conversation_id
    // This will be handled by the backend
  };

  const handleSearchConversations = (query: string) => {
    if (query.trim()) {
      searchConversations(query);
    } else {
      // Reload all conversations
      // This would need to be added to the hook
    }
  };

  const handleOpenSettings = () => {
    // TODO: Implement settings modal
    console.log('Open settings');
  };

  const handleOpenAgentSettings = () => {
    // TODO: Implement agent settings modal
    console.log('Open agent settings');
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-900">
      <Header
        connectionStatus={connectionStatus}
        onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
        onOpenSettings={handleOpenSettings}
      />
      
      <div className="flex flex-1 pt-16 gap-x-0">
        <Sidebar
          conversations={conversations}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onSearchConversations={handleSearchConversations}
          isCollapsed={sidebarCollapsed}
          isLoading={isLoading}
        />
        
        <div className="flex flex-col flex-1 relative">
          {/* Error Display */}
          {error && (
            <div className="absolute top-0 left-0 right-0 z-50 bg-red-500 text-white p-3 text-center">
              <p className="text-sm font-medium">Errore: {error}</p>
              <button 
                onClick={() => setError(null)} 
                className="text-xs underline mt-1"
              >
                Chiudi
              </button>
            </div>
          )}
          
          {/* Loading Indicator */}
          {isLoading && (
            <div className="absolute top-0 left-0 right-0 z-40 bg-blue-500 text-white p-2 text-center">
              <p className="text-sm font-medium">
                {processingStatus || 'Caricamento...'}
              </p>
            </div>
          )}
          
          <ChatInterface
            messages={messages}
            agentResponses={agentResponses}
            onSendMessage={handleSendMessage}
            onOpenAgentSettings={handleOpenAgentSettings}
          />
        </div>
        
        <AgentStatusPanel 
          agentCount={currentConversation?.agents?.length || 0}
          isVisible={rightPanelVisible}
          systemHealth={systemHealth}
          systemStats={systemStats}
        />
      </div>
    </div>
  );
};

export default Index;