import React from 'react';

interface SidebarProps {
  children?: React.ReactNode;
}

const Sidebar: React.FC<SidebarProps> = ({ children }) => {
  return (
    <aside className="w-64 bg-[#14161c] border-r h-screen flex flex-col p-0 shadow-lg">
      <div className="flex items-center justify-center h-16 border-b border-muted mb-2">
        <span className="text-xl font-bold text-primary tracking-wide">PolyAgent</span>
      </div>
      <nav className="flex-1 flex flex-col gap-1 px-2">
        <a href="/" className="flex items-center gap-2 p-3 rounded hover:bg-primary/10 text-white font-medium transition-all">
          <span>💬</span> Chat
        </a>
        <a href="/conversations" className="flex items-center gap-2 p-3 rounded hover:bg-primary/10 text-white font-medium transition-all">
          <span>🕑</span> Storico
        </a>
        <a href="/statistics" className="flex items-center gap-2 p-3 rounded hover:bg-primary/10 text-white font-medium transition-all">
          <span>📊</span> Statistiche
        </a>
        <a href="/admin" className="flex items-center gap-2 p-3 rounded hover:bg-primary/10 text-white font-medium transition-all">
          <span>🛠️</span> Admin
        </a>
        <button className="flex items-center gap-2 p-3 rounded hover:bg-primary/10 text-white font-medium transition-all" disabled>
          <span>⭐</span> Preferiti
        </button>
        <button className="flex items-center gap-2 p-3 rounded hover:bg-primary/10 text-white font-medium transition-all mt-6" onClick={() => window.dispatchEvent(new CustomEvent('open-settings'))}>
          <span>⚙️</span> Impostazioni
        </button>
      </nav>
      <div className="mt-auto flex items-center gap-2 p-4 border-t border-muted">
        <img src="https://api.dicebear.com/7.x/identicon/svg?seed=user" alt="avatar" className="w-10 h-10 rounded-full" />
        <div>
          <div className="font-semibold text-white text-sm">Utente</div>
          <div className="text-xs text-muted-foreground">online</div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
