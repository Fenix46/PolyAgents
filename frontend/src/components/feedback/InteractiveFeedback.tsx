import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { ThumbsUp, ThumbsDown, MessageSquare, Lightbulb, Send } from 'lucide-react';
import { Textarea } from '@/components/ui/textarea';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface InteractiveFeedbackProps {
  messageId: string;
  onSubmitFeedback: (messageId: string, feedback: FeedbackData) => void;
}

interface FeedbackData {
  rating: number;
  helpful: boolean;
  comment?: string;
  influence?: number;
}

export function InteractiveFeedback({ messageId, onSubmitFeedback }: InteractiveFeedbackProps) {
  const [expanded, setExpanded] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackData>({
    rating: 3,
    helpful: true,
    influence: 50
  });
  const [comment, setComment] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    onSubmitFeedback(messageId, {
      ...feedback,
      comment
    });
    setSubmitted(true);
    setTimeout(() => {
      setExpanded(false);
    }, 1500);
  };

  const ratingLabels = ['Pessimo', 'Scarso', 'Medio', 'Buono', 'Eccellente'];
  
  if (submitted && !expanded) {
    return (
      <div className="flex items-center gap-2 mt-1 text-xs text-slate-400">
        <ThumbsUp className="h-3 w-3" />
        <span>Feedback inviato</span>
      </div>
    );
  }

  return (
    <div className="mt-2">
      {!expanded ? (
        <div className="flex items-center gap-2">
          <Button 
            variant="ghost" 
            size="sm" 
            className="h-6 px-2 text-xs"
            onClick={() => setExpanded(true)}
          >
            <MessageSquare className="h-3 w-3 mr-1" />
            Valuta risposta
          </Button>
          
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="h-6 w-6 p-0 text-green-400"
                  onClick={() => {
                    setFeedback({...feedback, helpful: true});
                    onSubmitFeedback(messageId, {...feedback, helpful: true});
                    setSubmitted(true);
                  }}
                >
                  <ThumbsUp className="h-3 w-3" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Utile</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="h-6 w-6 p-0 text-red-400"
                  onClick={() => {
                    setFeedback({...feedback, helpful: false});
                    onSubmitFeedback(messageId, {...feedback, helpful: false});
                    setSubmitted(true);
                  }}
                >
                  <ThumbsDown className="h-3 w-3" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Non utile</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      ) : (
        <Card className="border border-slate-700 bg-slate-800/50">
          <CardHeader className="p-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Lightbulb className="h-4 w-4" />
              Valuta questa risposta
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3 pt-0 space-y-4">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs text-slate-400">Valutazione</span>
                <Badge variant="outline" className="text-xs">
                  {ratingLabels[feedback.rating - 1]}
                </Badge>
              </div>
              <Slider
                value={[feedback.rating]}
                min={1}
                max={5}
                step={1}
                onValueChange={(value) => setFeedback({...feedback, rating: value[0]})}
                className="py-1"
              />
            </div>
            
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs text-slate-400">Influenza sul consenso</span>
                <Badge variant="outline" className="text-xs">
                  {feedback.influence}%
                </Badge>
              </div>
              <Slider
                value={[feedback.influence || 50]}
                min={0}
                max={100}
                step={10}
                onValueChange={(value) => setFeedback({...feedback, influence: value[0]})}
                className="py-1"
              />
              <p className="text-xs text-slate-400 mt-1">
                Determina quanto questa valutazione influenzerà il consenso futuro
              </p>
            </div>
            
            <div>
              <span className="text-xs text-slate-400 block mb-1">Commento (opzionale)</span>
              <Textarea
                placeholder="Inserisci un commento..."
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                className="resize-none h-20 bg-slate-900/50"
              />
            </div>
          </CardContent>
          <CardFooter className="p-3 pt-0 flex justify-between">
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => setExpanded(false)}
            >
              Annulla
            </Button>
            <Button 
              variant="default" 
              size="sm"
              onClick={handleSubmit}
              className="flex items-center gap-1"
            >
              <Send className="h-3 w-3" />
              Invia feedback
            </Button>
          </CardFooter>
        </Card>
      )}
    </div>
  );
}
