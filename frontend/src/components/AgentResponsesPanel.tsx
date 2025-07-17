import React from 'react';
import AgentResponseCard from './AgentResponseCard';
import FusionResponseCard from './FusionResponseCard';

interface AgentResponsesPanelProps {
  agentResponses: Array<{
    agentName: string;
    agentAvatar?: string;
    response: string;
    loading?: boolean;
    error?: string;
  }>;
  fusionResponse: {
    response: string;
    loading?: boolean;
    error?: string;
  };
}

const AgentResponsesPanel: React.FC<AgentResponsesPanelProps> = ({ agentResponses, fusionResponse }) => {
  return (
    <div className="flex flex-col gap-4 mt-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
        {agentResponses.map((agent, idx) => (
          <AgentResponseCard key={agent.agentName + idx} {...agent} />
        ))}
      </div>
      <FusionResponseCard {...fusionResponse} />
    </div>
  );
};

export default AgentResponsesPanel;
