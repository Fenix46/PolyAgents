import { motion } from 'framer-motion';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { 
  Bot, 
  Zap, 
  Clock, 
  TrendingUp,
  Activity,
  Brain
} from 'lucide-react';
import { SystemHealth, SystemStatistics } from '@/types';

interface AgentStatusPanelProps {
  agentCount?: number;
  isVisible?: boolean;
  systemHealth?: SystemHealth | null;
  systemStats?: SystemStatistics | null;
}

export default function AgentStatusPanel({ 
  agentCount = 3, 
  isVisible = true 
}: AgentStatusPanelProps) {
  const mockAgents = [
    { id: 'agent-1', name: 'Research Agent', model: 'Gemini Pro', temperature: 0.3, status: 'active', progress: 85 },
    { id: 'agent-2', name: 'Analysis Agent', model: 'Gemini Pro', temperature: 0.5, status: 'thinking', progress: 45 },
    { id: 'agent-3', name: 'Synthesis Agent', model: 'Gemini Pro', temperature: 0.7, status: 'waiting', progress: 0 },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-success/20 text-success border-success/30';
      case 'thinking':
        return 'bg-warning/20 text-warning border-warning/30';
      case 'waiting':
        return 'bg-muted/20 text-muted-foreground border-muted/30';
      default:
        return 'bg-muted/20 text-muted-foreground border-muted/30';
    }
  };

  const getAgentColor = (index: number) => {
    const colors = ['agent-1', 'agent-2', 'agent-3', 'agent-4', 'agent-5'];
    return colors[index % colors.length];
  };

  if (!isVisible) return null;

  return (
    <div className="w-96 shrink-0 border-l border-slate-700 bg-slate-800/60 backdrop-blur-md hidden lg:block">
      <div className="flex flex-col h-full overflow-y-auto scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-transparent">
        {/* Header */}
        <div className="sticky top-0 z-20 flex items-center justify-between h-14 px-4 bg-slate-800/80 backdrop-blur-md border-b border-slate-700">
          <div className="flex items-center space-x-2">
            <Bot className="w-5 h-5 text-primary" />
            <h3 className="font-semibold">Agent Status</h3>
          </div>
          <Badge variant="outline" className="text-xs">
            {agentCount} active
          </Badge>
        </div>

        {/* Content */}
        <div className="flex-1 p-4 space-y-4">
          {/* System Status */}
          <Card className="rounded-2xl p-4 bg-surface/50">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium flex items-center space-x-2">
                <Activity className="w-4 h-4" />
                <span>System Status</span>
              </h4>
              <Badge variant="outline" className="bg-success/20 text-success border-success/30">
                Healthy
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Response Time</span>
                <span>245ms</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Active Agents</span>
                <span>{agentCount}/5</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Total Messages</span>
                <span>1,247</span>
              </div>
            </div>
          </Card>

          {/* Agent Cards */}
          <div className="space-y-3">
            {mockAgents.slice(0, agentCount).map((agent, index) => (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="rounded-2xl p-4 bg-surface/50 border-l-4 border-l-[hsl(var(--agent-1))]">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <div className={`w-3 h-3 rounded-full bg-${getAgentColor(index)}`} />
                      <div>
                        <h5 className="font-medium text-sm">{agent.name}</h5>
                        <p className="text-xs text-muted-foreground">{agent.model}</p>
                      </div>
                    </div>
                    <Badge variant="outline" className={`text-xs ${getStatusColor(agent.status)}`}>
                      {agent.status}
                    </Badge>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Temperature</span>
                      <span>{agent.temperature}</span>
                    </div>
                    
                    {agent.status === 'active' && (
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-muted-foreground">Progress</span>
                          <span>{agent.progress}%</span>
                        </div>
                        <Progress value={agent.progress} className="h-2" />
                      </div>
                    )}
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>

          {/* Consensus Status */}
          <Card className="rounded-2xl p-4 bg-surface/50">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium flex items-center space-x-2">
                <Brain className="w-4 h-4" />
                <span>Consensus</span>
              </h4>
              <Badge variant="outline" className="bg-accent/20 text-accent border-accent/30">
                In Progress
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Agreement</span>
                <span>78%</span>
              </div>
              <Progress value={78} className="h-2" />
              <p className="text-xs text-muted-foreground">
                Agents are converging on response...
              </p>
            </div>
          </Card>

          {/* Performance Metrics */}
          <Card className="rounded-2xl p-4 bg-surface/50">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium flex items-center space-x-2">
                <TrendingUp className="w-4 h-4" />
                <span>Performance</span>
              </h4>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Avg. Response</span>
                <span>2.3s</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Success Rate</span>
                <span>99.2%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Consensus Rate</span>
                <span>85%</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}