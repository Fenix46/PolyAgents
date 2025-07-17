import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TooltipProvider } from '@/components/ui/tooltip';
import ChatPage from './pages/ChatPage';
import ConversationsPage from './pages/ConversationsPage';
import StatisticsPage from './pages/StatisticsPage';
import AdminPage from './pages/AdminPage';
import NotFound from './pages/NotFound';
import { ThemeProvider } from './contexts/ThemeContext';
import { PerformanceMonitor } from './components/performance/PerformanceMonitor';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minuto
      cacheTime: 5 * 60 * 1000, // 5 minuti
      refetchOnWindowFocus: false,
      retry: 1
    }
  }
});

import Sidebar from './components/Sidebar';
import { Outlet } from 'react-router-dom';

const MainLayout: React.FC = () => (
  <div className="flex h-screen w-screen bg-[#10121a] text-white">
    <Sidebar />
    <main className="flex-1 flex flex-col h-full">
      <Outlet />
    </main>
  </div>
);

const App = () => (
  <ThemeProvider>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route element={<MainLayout />}>
              <Route path="/" element={<ChatPage />} />
              <Route path="/conversations" element={<ConversationsPage />} />
              <Route path="/statistics" element={<StatisticsPage />} />
              <Route path="/admin" element={<AdminPage />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </BrowserRouter>
        <PerformanceMonitor enabled={true} sampleInterval={3000} />
      </TooltipProvider>
    </QueryClientProvider>
  </ThemeProvider>
);

export default App;
