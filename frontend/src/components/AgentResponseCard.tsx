import React from 'react';

interface AgentResponseCardProps {
  agentName: string;
  agentAvatar?: string;
  response: string;
  loading?: boolean;
  error?: string;
}

const AgentResponseCard: React.FC<AgentResponseCardProps> = ({ agentName, agentAvatar, response, loading, error }) => {
  return (
    <div className="bg-card rounded-lg shadow p-4 mb-2 border border-muted flex gap-3 items-start">
      {agentAvatar && (
        <img src={agentAvatar} alt={agentName} className="w-10 h-10 rounded-full object-cover" />
      )}
      <div className="flex-1">
        <div className="font-semibold text-primary flex items-center gap-2">
          {agentName}
          <span className="text-xs bg-secondary px-2 py-0.5 rounded ml-2">Cloud Agent</span>
        </div>
        {loading ? (
          <div className="text-muted-foreground mt-2">Risposta in arrivo...</div>
        ) : error ? (
          <div className="text-destructive mt-2">Errore: {error}</div>
        ) : (
          <div className="mt-2 whitespace-pre-line">{response}</div>
        )}
      </div>
    </div>
  );
};

export default AgentResponseCard;
