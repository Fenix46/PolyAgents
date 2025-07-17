import React from 'react';

interface FusionResponseCardProps {
  response: string;
  loading?: boolean;
  error?: string;
}

const FusionResponseCard: React.FC<FusionResponseCardProps> = ({ response, loading, error }) => {
  return (
    <div className="bg-primary/10 border-2 border-primary rounded-lg shadow p-4 mb-4">
      <div className="font-bold text-primary text-lg flex items-center gap-2">
        <span>Risposta Finale</span>
        <span className="text-xs bg-primary text-white px-2 py-0.5 rounded ml-2">Fusione Locale</span>
      </div>
      {loading ? (
        <div className="text-muted-foreground mt-2">Sto fondendo le risposte degli agenti...</div>
      ) : error ? (
        <div className="text-destructive mt-2">Errore: {error}</div>
      ) : (
        <div className="mt-2 whitespace-pre-line">{response}</div>
      )}
    </div>
  );
};

export default FusionResponseCard;
