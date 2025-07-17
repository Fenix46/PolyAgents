import React, { useEffect, useState } from 'react';
import { getStatistics, getRedisInfo } from '../services/statisticsService';

const StatisticsPage: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [redis, setRedis] = useState<any>(null);

  useEffect(() => {
    getStatistics().then(setStats);
    getRedisInfo().then(setRedis);
  }, []);

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h2 className="font-bold text-xl mb-4">Statistiche di Sistema</h2>
      {stats ? (
        <pre className="bg-card p-4 rounded border overflow-x-auto text-sm">{JSON.stringify(stats, null, 2)}</pre>
      ) : (
        <div>Caricamento statistiche...</div>
      )}
      <h3 className="font-semibold mt-8 mb-2">Info Redis</h3>
      {redis ? (
        <pre className="bg-card p-4 rounded border overflow-x-auto text-sm">{JSON.stringify(redis, null, 2)}</pre>
      ) : (
        <div>Caricamento info Redis...</div>
      )}
    </div>
  );
};

export default StatisticsPage;
