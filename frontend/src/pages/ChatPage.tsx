import React, { useState } from 'react';
import PromptInput from '../components/PromptInput';
import AgentResponsesPanel from '../components/AgentResponsesPanel';
import ChatHistory from '../components/ChatHistory';
import SettingsModal from '../components/SettingsModal';
import { sendChat, ChatRequest, ChatResponse } from '../services/chatService';

const AGENT_NAMES = ['Agent 1', 'Agent 2', 'Agent 3'];

const ChatPage: React.FC = () => {
  const [settingsOpen, setSettingsOpen] = useState(false);
  React.useEffect(() => {
    const open = () => setSettingsOpen(true);
    window.addEventListener('open-settings', open);
    return () => window.removeEventListener('open-settings', open);
  }, []);
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedAgent, setExpandedAgent] = useState<number | null>(null);
  const [showAgentThinking, setShowAgentThinking] = useState(false);
  const [agentThinking, setAgentThinking] = useState<string[]>([]);
  const [showConsensusThinking, setShowConsensusThinking] = useState(false);

  const AGENT_NAMES = ['Agent 1', 'Agent 2', 'Agent 3'];

  const handleSend = async (prompt: string) => {
    setLoading(true);
    setExpandedAgent(null);
    setShowAgentThinking(true);
    setAgentThinking(AGENT_NAMES);
    setShowConsensusThinking(false);
    
    // Mostra subito il messaggio utente
    const messageId = Date.now().toString();
    setMessages(prev => [...prev, { 
      id: messageId, 
      sender: 'Utente', 
      content: prompt, 
      timestamp: new Date().toLocaleTimeString() 
    }]);
    
    // Chiamata API reale - manteniamo l'animazione "thinking" durante la chiamata
    try {
      console.log('Invio richiesta al backend:', prompt);
      const req: ChatRequest = { message: prompt };
      
      // Utilizziamo la chiamata sincrona che attende la risposta completa
      // Questa chiamata può richiedere molto tempo, ma l'animazione "thinking" rimarrà attiva
      console.log('Avvio chiamata sincrona a sendChat');
      const res: ChatResponse = await sendChat(req);
      console.log('Risposta ricevuta dal backend:', res);
      
      // Disattiva animazione thinking solo dopo aver ricevuto la risposta
      setShowAgentThinking(false);
      
      // Mostra risposte agenti
      let agentMsgs = AGENT_NAMES.map((name, idx) => ({
        id: `${res.message_id}-agent${idx}`,
        sender: name,
        content: res.agent_responses?.[name] || '',
        agent: name,
        timestamp: new Date().toLocaleTimeString()
      }));
      
      setMessages(prev => [
        ...prev,
        ...agentMsgs
      ]);
      
      // Dopo breve attesa, mostra thinking consenso
      setTimeout(() => {
        setShowConsensusThinking(true);
        
        // Dopo altro timeout, mostra risposta consenso
        setTimeout(() => {
          setShowConsensusThinking(false);
          setMessages(prev => [
            ...prev,
            {
              id: `${res.message_id}-fusion`,
              sender: 'Fusione',
              content: res.response,
              fusion: true,
              timestamp: new Date().toLocaleTimeString()
            }
          ]);
          setLoading(false);
        }, 1200);
      }, 900);
    } catch (e) {
      console.error('Errore durante la chiamata API:', e);
      setShowAgentThinking(false);
      setShowConsensusThinking(false);
      
      // Aggiungi messaggio di errore alla chat
      setMessages(prev => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          sender: 'Sistema',
          content: 'Si è verificato un errore nella comunicazione con il backend. Il processo multi-agente potrebbe richiedere più tempo del previsto.',
          error: true,
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
      
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full bg-[#10121a] text-white">
      {/* Header */}
      <header className="flex items-center h-16 px-8 border-b border-muted bg-[#181a20] sticky top-0 z-10">
        <h1 className="text-2xl font-bold tracking-tight flex-1">Chat Multi-Agente</h1>
        <button
          className="bg-primary text-white rounded px-4 py-2 mr-2 hover:bg-primary/80 transition-all"
          onClick={() => window.location.href = '/conversations'}
        >
          Storico
        </button>
        <button
          className="bg-secondary text-black rounded px-4 py-2 hover:bg-secondary/80 transition-all"
          onClick={() => window.dispatchEvent(new CustomEvent('open-settings'))}
        >
          Impostazioni
        </button>
      </header>
      {/* Area chat centrale */}
      <div className="flex-1 flex flex-col max-w-2xl mx-auto w-full px-2 py-4 gap-2 overflow-y-auto">
        {/* Messaggi chat bubble */}
        {messages.map((msg, idx) => (
          <div key={msg.id} className={`flex ${msg.sender === 'Utente' ? 'justify-end' : 'justify-start'} w-full`}>
            <div
              className={`relative max-w-[80%] rounded-2xl px-4 py-2 mb-2 shadow-md ${msg.sender === 'Utente' ? 'bg-primary text-white' : msg.fusion ? 'bg-gradient-to-r from-blue-900 to-purple-800 text-white' : 'bg-[#23263a] text-white'} cursor-pointer group`}
              onClick={() => msg.agent && setExpandedAgent(idx === expandedAgent ? null : idx)}
            >
              <div className="flex items-center gap-2 mb-1">
                {msg.agent && <img src={`/avatars/agent${msg.agent.replace(/\D/g, '')}.svg`} alt="avatar" className="w-6 h-6 rounded-full" />}
                {msg.fusion && <span className="text-xs font-semibold bg-purple-700 px-2 py-0.5 rounded">Consenso</span>}
                {msg.agent && <span className="text-xs font-semibold bg-blue-700 px-2 py-0.5 rounded">Cloud Agent</span>}
                <span className="text-xs text-gray-400 ml-2">{msg.timestamp}</span>
              </div>
              <div className="whitespace-pre-line">
                {expandedAgent === idx ? (msg.content || <span className="italic text-gray-400">(Nessuna risposta)</span>) : (msg.content.length > 120 ? msg.content.slice(0, 120) + '…' : msg.content)}
              </div>
              {expandedAgent === idx && (
                <div className="absolute top-1 right-2 text-xs text-gray-300">Click per ridurre</div>
              )}
            </div>
          </div>
        ))}
        {/* Loading agenti e consenso */}
        {showAgentThinking && agentThinking.map((a, i) => (
          <div key={i} className="flex justify-start w-full">
            <div className="relative max-w-[80%] rounded-2xl px-4 py-2 mb-2 shadow-md bg-[#23263a] text-white flex items-center gap-2">
              <img src={`/avatars/agent${i+1}.svg`} alt="avatar" className="w-6 h-6 rounded-full animate-pulse" />
              <span className="text-xs font-semibold bg-blue-700 px-2 py-0.5 rounded">Cloud Agent</span>
              <span className="ml-2 italic text-gray-400 animate-pulse">{a} sta pensando…</span>
            </div>
          </div>
        ))}
        {showConsensusThinking && (
          <div className="flex justify-start w-full">
            <div className="relative max-w-[80%] rounded-2xl px-4 py-2 mb-2 shadow-md bg-gradient-to-r from-blue-900 to-purple-800 text-white flex items-center gap-2">
              <span className="text-xs font-semibold bg-purple-700 px-2 py-0.5 rounded">Consenso</span>
              <span className="ml-2 italic text-gray-200 animate-pulse">L’agente del consenso sta generando il resoconto…</span>
            </div>
          </div>
        )}
      </div>
      {/* Prompt input sticky in basso */}
      <div className="sticky bottom-0 bg-[#181a20] px-2 py-4 border-t border-muted z-10">
        <PromptInput onSend={handleSend} loading={loading} />
      </div>
      {/* Settings Modal */}
      <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );

};

export default ChatPage;
