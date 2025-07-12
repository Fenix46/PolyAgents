import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Progress } from '@/components/ui/progress';
import { 
  Bot, 
  Clock, 
  Zap, 
  Settings, 
  Activity,
  Thermometer,
  MessageCircle,
  Play,
  Pause,
  RotateCcw
} from 'lucide-react';
import { Agent } from '@/types';
import { cn } from '@/lib/utils';

interface AgentCardProps {
  agent: Agent;
  onConfigure?: (agentId: string) => void;
  onToggleStatus?: (agentId: string, status: 'active' | 'paused') => void;
  onReset?: (agentId: string) => void;
  compact?: boolean;
}

export default function AgentCard({
  agent,
  onConfigure,
  onToggleStatus,
  onReset,
  compact = false
}: AgentCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'thinking':
        return 'bg-warning/20 text-warning border-warning/30';
      case 'responding':
        return 'bg-success/20 text-success border-success/30';
      case 'offline':
        return 'bg-destructive/20 text-destructive border-destructive/30';
      case 'idle':
      default:
        return 'bg-muted/20 text-muted-foreground border-muted/30';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'thinking':
        return <Activity className="w-3 h-3 animate-pulse" />;
      case 'responding':
        return <MessageCircle className="w-3 h-3" />;
      case 'offline':
        return <Pause className="w-3 h-3" />;
      case 'idle':
      default:
        return <Bot className="w-3 h-3" />;
    }
  };

  const getAgentNumber = (id: string) => {
    return parseInt(id.slice(-1)) || 1;
  };

  const agentNumber = getAgentNumber(agent.id);

  if (compact) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.2 }}
        className="flex items-center space-x-3 p-3 bg-surface rounded-lg border border-border"
      >
        <Avatar className="w-10 h-10">
          <AvatarFallback className={cn(
            "text-white font-medium",
            `bg-agent-${(agentNumber % 5 + 1) as 1 | 2 | 3 | 4 | 5}`
          )}>
            {agentNumber}
          </AvatarFallback>
        </Avatar>

        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">{agent.name}</span>
            <Badge 
              variant="outline" 
              className={cn("text-xs", getStatusColor(agent.status))}
            >
              {getStatusIcon(agent.status)}
              <span className="ml-1 capitalize">{agent.status}</span>
            </Badge>
          </div>
          <div className="flex items-center space-x-2 mt-1">
            <span className="text-xs text-muted-foreground">{agent.model}</span>
            <span className="text-xs text-muted-foreground">•</span>
            <span className="text-xs text-muted-foreground">T: {agent.temperature}</span>
          </div>
        </div>

        <Button
          variant="ghost"
          size="icon"
          onClick={() => onConfigure?.(agent.id)}
          className="w-8 h-8 surface-hover"
        >
          <Settings className="w-4 h-4" />
        </Button>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="group"
    >
      <Card className="bg-surface border-border hover:border-border/80 transition-colors">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Avatar className="w-12 h-12">
                <AvatarFallback className={cn(
                  "text-white font-bold text-lg",
                  `bg-agent-${(agentNumber % 5 + 1) as 1 | 2 | 3 | 4 | 5}`
                )}>
                  {agentNumber}
                </AvatarFallback>
              </Avatar>
              <div>
                <h3 className="font-semibold text-lg">{agent.name}</h3>
                <p className="text-sm text-muted-foreground">{agent.model}</p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Badge 
                variant="outline" 
                className={cn("text-xs", getStatusColor(agent.status))}
              >
                {getStatusIcon(agent.status)}
                <span className="ml-1 capitalize">{agent.status}</span>
              </Badge>
              
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-8 h-8 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Performance Metrics */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Thermometer className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">Temperature</span>
              </div>
              <div className="flex items-center space-x-2">
                <Progress value={agent.temperature * 100} className="flex-1" />
                <span className="text-xs text-muted-foreground w-8">
                  {agent.temperature}
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium">Response Time</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm">
                  {agent.responseTime ? `${agent.responseTime}ms` : 'N/A'}
                </span>
                {agent.responseTime && (
                  <Badge variant="outline" className="text-xs">
                    {agent.responseTime < 1000 ? 'Fast' : 
                     agent.responseTime < 3000 ? 'Medium' : 'Slow'}
                  </Badge>
                )}
              </div>
            </div>
          </div>

          {/* Expanded Details */}
          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
                className="border-t border-border pt-4 space-y-3"
              >
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Turns:</span>
                    <span className="ml-2">{agent.turns || 0}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Model:</span>
                    <span className="ml-2">{agent.model}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onToggleStatus?.(agent.id, 
                      agent.status === 'offline' ? 'active' : 'paused'
                    )}
                    className="flex-1"
                  >
                    {agent.status === 'offline' ? (
                      <Play className="w-4 h-4 mr-2" />
                    ) : (
                      <Pause className="w-4 h-4 mr-2" />
                    )}
                    {agent.status === 'offline' ? 'Activate' : 'Pause'}
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onReset?.(agent.id)}
                    className="flex-1"
                  >
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Reset
                  </Button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    </motion.div>
  );
}