import React, { useState } from 'react';
import { cleanupOldData, exportConversations } from '../services/adminService';

const AdminPage: React.FC = () => {
  const [cleanupResult, setCleanupResult] = useState<any>(null);
  const [exportResult, setExportResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleCleanup = async () => {
    setLoading(true);
    try {
      const res = await cleanupOldData();
      setCleanupResult(res);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    setLoading(true);
    try {
      const res = await exportConversations();
      setExportResult(res);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h2 className="font-bold text-xl mb-4">Amministrazione</h2>
      <button className="bg-primary text-white px-4 py-2 rounded mb-4 mr-2" onClick={handleCleanup} disabled={loading}>Pulizia Dati Vecchi</button>
      <button className="bg-secondary text-black px-4 py-2 rounded mb-4" onClick={handleExport} disabled={loading}>Esporta Conversazioni</button>
      {cleanupResult && (
        <div className="mt-4">
          <h3 className="font-semibold">Risultato Pulizia</h3>
          <pre className="bg-card p-4 rounded border overflow-x-auto text-sm">{JSON.stringify(cleanupResult, null, 2)}</pre>
        </div>
      )}
      {exportResult && (
        <div className="mt-4">
          <h3 className="font-semibold">Risultato Esportazione</h3>
          <pre className="bg-card p-4 rounded border overflow-x-auto text-sm">{JSON.stringify(exportResult, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default AdminPage;
