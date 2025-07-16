import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TooltipProvider } from '@/components/ui/tooltip';
import Index from './pages/Index';
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

const App = () => (
  <ThemeProvider>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
        <PerformanceMonitor enabled={true} sampleInterval={3000} />
      </TooltipProvider>
    </QueryClientProvider>
  </ThemeProvider>
);

export default App;
