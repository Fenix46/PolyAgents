import React, { useState } from 'react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [theme, setTheme] = useState('system');
  const [language, setLanguage] = useState('it');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center">
      <div className="bg-background rounded-lg p-6 w-full max-w-sm shadow-lg relative">
        <button className="absolute top-2 right-2 text-xl" onClick={onClose}>&times;</button>
        <h2 className="font-bold text-lg mb-4">Impostazioni</h2>
        <div className="mb-4">
          <label className="block font-semibold mb-1">Tema</label>
          <select value={theme} onChange={e => setTheme(e.target.value)} className="w-full p-2 border rounded">
            <option value="system">Sistema</option>
            <option value="light">Chiaro</option>
            <option value="dark">Scuro</option>
          </select>
        </div>
        <div className="mb-4">
          <label className="block font-semibold mb-1">Lingua</label>
          <select value={language} onChange={e => setLanguage(e.target.value)} className="w-full p-2 border rounded">
            <option value="it">Italiano</option>
            <option value="en">English</option>
          </select>
        </div>
        <button className="bg-primary text-white px-4 py-2 rounded w-full" onClick={onClose}>Salva</button>
      </div>
    </div>
  );
};

export default SettingsModal;
