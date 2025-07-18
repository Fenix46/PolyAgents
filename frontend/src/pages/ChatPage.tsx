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
      console.log('Risposta ricevuta dal backend:', JSON.stringify(res, null, 2));
      
      // Disattiva animazione thinking solo dopo aver ricevuto la risposta
      setShowAgentThinking(false);
      
      // Estrai le risposte degli agenti in modo più robusto
      // 1. Verifica se agent_responses è un oggetto o un array
      let agentResponses: Array<{name: string, content: string}> = [];
      
      if (res.agent_responses) {
        if (Array.isArray(res.agent_responses)) {
          // Se è un array, lo usiamo direttamente
          agentResponses = res.agent_responses.map((resp, idx) => ({
            name: `Agent ${idx+1}`,
            content: typeof resp === 'string' ? resp : JSON.stringify(resp)
          }));
        } else {
          // Se è un oggetto, lo convertiamo in array per mantenere l'ordine
          agentResponses = Object.entries(res.agent_responses).map(([name, content]) => ({
            name,
            content: typeof content === 'string' ? content : JSON.stringify(content)
          }));
        }
      }
      
      // Garantisci che ci siano sempre 3 agenti, anche se vuoti
      while (agentResponses.length < 3) {
        agentResponses.push({
          name: `Agent ${agentResponses.length + 1}`,
          content: ''
        });
      }
      
      // Limita a 3 agenti se ce ne sono di più
      if (agentResponses.length > 3) {
        agentResponses = agentResponses.slice(0, 3);
      }
      
      // Crea i messaggi degli agenti con l'ordine corretto
      const agentMsgs = agentResponses.map((agent, idx) => ({
        id: `${res.message_id}-agent${idx}`,
        sender: agent.name,
        content: agent.content || '(Nessuna risposta)',
        agent: agent.name,
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
          
          // Usa res.consensus se disponibile, altrimenti res.response
          // Rimuovi eventuali prompt interni che iniziano con "You are a thinking assistant"
          let consensusContent = res.consensus || res.response || '';
          
          // Assicurati che consensusContent sia una stringa
          if (typeof consensusContent !== 'string') {
            consensusContent = JSON.stringify(consensusContent);
          }
          
          // Rimuovi il prompt interno se presente
          if (consensusContent.includes && consensusContent.includes('You are a thinking assistant')) {
            const parts = consensusContent.split('You are a thinking assistant');
            if (parts.length > 1) {
              // Prendi la parte dopo il prompt
              const afterPrompt = parts[1].split('\n').slice(1).join('\n').trim();
              consensusContent = afterPrompt || consensusContent;
            }
          }
          
          setMessages(prev => [
            ...prev,
            {
              id: `${res.message_id}-fusion`,
              sender: 'Fusione',
              content: consensusContent,
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
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-2 py-4 gap-4 overflow-y-auto">
        {/* Messaggi chat bubble */}
        {messages.map((msg, idx) => {
          // Se è un messaggio utente o di errore, mostralo normalmente
          if (msg.sender === 'Utente' || msg.error) {
            return (
              <div key={msg.id} className={`flex ${msg.sender === 'Utente' ? 'justify-end' : 'justify-start'} w-full`}>
                <div
                  className={`relative max-w-[80%] rounded-2xl px-4 py-2 mb-2 shadow-md ${msg.sender === 'Utente' ? 'bg-primary text-white' : msg.error ? 'bg-red-700 text-white' : 'bg-[#23263a] text-white'}`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    {msg.error && <span className="text-xs font-semibold bg-red-900 px-2 py-0.5 rounded">Errore</span>}
                    <span className="text-xs text-gray-400 ml-2">{msg.timestamp}</span>
                  </div>
                  <div className="whitespace-pre-line">
                    {msg.content}
                  </div>
                </div>
              </div>
            );
          }
          
          // Se è un messaggio di fusione (consenso), mostralo a tutta larghezza
          if (msg.fusion) {
            return (
              <div key={msg.id} className="flex flex-col w-full mt-4">
                <div className="text-center mb-2">
                  <span className="text-xs font-semibold bg-purple-700 px-3 py-1 rounded-full text-white">Consenso Semantico</span>
                </div>
                <div
                  className="relative w-full rounded-2xl px-4 py-3 mb-2 shadow-md bg-gradient-to-r from-blue-900 to-purple-800 text-white cursor-pointer"
                  onClick={() => setExpandedAgent(idx === expandedAgent ? null : idx)}
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center">
                      <span className="text-sm font-semibold">Fusione</span>
                      <span className="text-xs text-gray-300 ml-2">{msg.timestamp}</span>
                    </div>
                    {expandedAgent === idx ? (
                      <span className="text-xs text-gray-300">Click per ridurre</span>
                    ) : (
                      <span className="text-xs text-gray-300">Click per espandere</span>
                    )}
                  </div>
                  <div className="whitespace-pre-line text-sm">
                    {expandedAgent === idx ? (
                      msg.content || <span className="italic text-gray-400">(Nessuna risposta)</span>
                    ) : (
                      msg.content.length > 240 ? msg.content.slice(0, 240) + '…' : msg.content
                    )}
                  </div>
                </div>
              </div>
            );
          }
          
          // Raggruppa i messaggi degli agenti in un unico gruppo orizzontale
          // Trova tutti i messaggi degli agenti che appartengono allo stesso gruppo (stesso message_id)
          if (msg.agent && !messages.some(m => m.id.includes(msg.id.split('-agent')[0]) && m.id < msg.id)) {
            // Questo è il primo agente di un gruppo, mostra tutti gli agenti orizzontalmente
            const messageIdBase = msg.id.split('-agent')[0];
            const agentMessages = messages.filter(m => m.id.includes(messageIdBase) && m.agent && !m.fusion);
            
            return (
              <div key={`group-${messageIdBase}`} className="w-full mt-2">
                <div className="text-center mb-2">
                  <span className="text-xs font-semibold bg-blue-700 px-3 py-1 rounded-full text-white">Risposte Agenti</span>
                </div>
                <div className="flex flex-row gap-2 overflow-x-auto pb-2">
                  {agentMessages.map((agentMsg, agentIdx) => (
                    <div 
                      key={agentMsg.id} 
                      className="flex-1 min-w-[250px] max-w-[350px] rounded-2xl px-4 py-2 shadow-md bg-[#23263a] text-white cursor-pointer"
                      onClick={() => setExpandedAgent(messages.indexOf(agentMsg) === expandedAgent ? null : messages.indexOf(agentMsg))}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <img 
                          src={`/avatars/agent${agentMsg.agent.replace(/\D/g, '') || agentIdx+1}.svg`} 
                          alt="avatar" 
                          className="w-6 h-6 rounded-full" 
                        />
                        <span className="text-sm font-semibold">{agentMsg.agent}</span>
                        <span className="text-xs text-gray-400 ml-auto">{agentMsg.timestamp}</span>
                      </div>
                      <div className="whitespace-pre-line text-sm">
                        {messages.indexOf(agentMsg) === expandedAgent ? (
                          agentMsg.content || <span className="italic text-gray-400">(Nessuna risposta)</span>
                        ) : (
                          agentMsg.content.length > 150 ? agentMsg.content.slice(0, 150) + '…' : agentMsg.content
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          } else if (msg.agent) {
            // Questo è un agente che fa parte di un gruppo già mostrato, non mostrarlo di nuovo
            return null;
          }
          
          // Fallback per altri tipi di messaggi
          return (
            <div key={msg.id} className="flex justify-start w-full">
              <div className="relative max-w-[80%] rounded-2xl px-4 py-2 mb-2 shadow-md bg-[#23263a] text-white">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-gray-400">{msg.timestamp}</span>
                </div>
                <div className="whitespace-pre-line">{msg.content}</div>
              </div>
            </div>
          );
        })}
        
        {/* Loading agenti e consenso */}
        {showAgentThinking && (
          <div className="w-full mt-2">
            <div className="text-center mb-2">
              <span className="text-xs font-semibold bg-blue-700 px-3 py-1 rounded-full text-white">Agenti al lavoro</span>
            </div>
            <div className="flex flex-row gap-2 overflow-x-auto pb-2">
              {agentThinking.map((a, i) => (
                <div key={i} className="flex-1 min-w-[250px] max-w-[350px] rounded-2xl px-4 py-2 shadow-md bg-[#23263a] text-white">
                  <div className="flex items-center gap-2 mb-2">
                    <img src={`/avatars/agent${i+1}.svg`} alt="avatar" className="w-6 h-6 rounded-full animate-pulse" />
                    <span className="text-sm font-semibold">{a}</span>
                  </div>
                  <div className="italic text-gray-400 animate-pulse">L'agente sta analizzando il prompt...</div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {showConsensusThinking && (
          <div className="flex flex-col w-full mt-4">
            <div className="text-center mb-2">
              <span className="text-xs font-semibold bg-purple-700 px-3 py-1 rounded-full text-white">Consenso in elaborazione</span>
            </div>
            <div className="relative w-full rounded-2xl px-4 py-3 mb-2 shadow-md bg-gradient-to-r from-blue-900 to-purple-800 text-white">
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-sm font-semibold">Fusione</span>
              </div>
              <div className="italic text-gray-200 animate-pulse">L'agente del consenso sta generando il resoconto semantico...</div>
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
