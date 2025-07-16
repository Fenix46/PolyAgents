import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, ChevronUp, Brain, MessageCircle } from 'lucide-react';
import { AgentResponse } from '@/types';

interface ConsensusVisualizationProps {
  agentResponses: AgentResponse[];
  consensus: { content: string; explanation?: string } | null;
}

export function ConsensusVisualization({ agentResponses, consensus }: ConsensusVisualizationProps) {
  const [expanded, setExpanded] = useState(false);
  
  if (!agentResponses.length || !consensus) {
    return null;
  }

  // Calcola il livello di accordo tra gli agenti (simulato)
  const calculateAgreementLevel = () => {
    // Simulazione: in un'implementazione reale, questo verrebbe calcolato in base alla similarità delle risposte
    const agreementScores = agentResponses.map(() => Math.random() * 100);
    return agreementScores.reduce((sum, score) => sum + score, 0) / agreementScores.length;
  };

  const agreementLevel = calculateAgreementLevel();
  
  // Determina il colore in base al livello di accordo
  const getAgreementColor = () => {
    if (agreementLevel > 80) return 'bg-green-500';
    if (agreementLevel > 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <Card className="mt-4 border border-slate-700 bg-slate-800/50 overflow-hidden">
      <CardHeader className="p-4 pb-0">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Processo di Consenso
            <Badge className={`${getAgreementColor()} text-white ml-2`}>
              {agreementLevel.toFixed(0)}% accordo
            </Badge>
          </CardTitle>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setExpanded(!expanded)}
            className="h-8 w-8 p-0"
          >
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
        </div>
      </CardHeader>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <CardContent className="p-4">
              <div className="space-y-4">
                {/* Visualizzazione del processo di pensiero */}
                <div className="space-y-2">
                  {agentResponses.map((agent, index) => (
                    <div 
                      key={agent.agent_id || `agent-${index}`} 
                      className="p-3 rounded-lg bg-slate-700/30 border border-slate-600"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center text-xs font-bold">
                          {index + 1}
                        </div>
                        <div className="font-medium">Agente {index + 1}</div>
                      </div>
                      <div className="pl-8 text-sm text-slate-300">
                        {agent.content || "Nessuna risposta"}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Visualizzazione del consenso */}
                <div className="p-4 rounded-lg bg-primary/20 border border-primary/30">
                  <div className="flex items-center gap-2 mb-2">
                    <MessageCircle className="h-5 w-5 text-primary" />
                    <div className="font-medium">Consenso Raggiunto</div>
                  </div>
                  <div className="text-sm">
                    {consensus.content}
                  </div>
                  {consensus.explanation && (
                    <div className="mt-2 text-xs text-slate-400 italic">
                      {consensus.explanation}
                    </div>
                  )}
                </div>

                {/* Grafico di visualizzazione del consenso (simulato con barre) */}
                <div className="pt-2">
                  <div className="text-sm font-medium mb-2">Livello di accordo tra agenti</div>
                  <div className="flex gap-1 h-4">
                    {agentResponses.map((_, index) => {
                      // Simula il livello di accordo per ogni agente
                      const agreementWidth = Math.random() * 100;
                      return (
                        <div 
                          key={`agreement-${index}`} 
                          className="h-full bg-primary/80 rounded"
                          style={{ width: `${agreementWidth}%` }}
                        />
                      );
                    })}
                  </div>
                </div>
              </div>
            </CardContent>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}
