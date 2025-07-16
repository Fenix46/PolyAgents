import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Gauge, BarChart3, Cpu, Clock, RefreshCw } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface PerformanceMetric {
  timestamp: number;
  fps: number;
  memory: number;
  renderTime: number;
  apiLatency: number;
}

interface PerformanceMonitorProps {
  enabled?: boolean;
  sampleInterval?: number;
  maxSamples?: number;
}

export function PerformanceMonitor({
  enabled = true,
  sampleInterval = 2000,
  maxSamples = 60
}: PerformanceMonitorProps) {
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [isVisible, setIsVisible] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(true);
  const [isPaused, setIsPaused] = useState(false);

  // Calcola metriche di performance
  useEffect(() => {
    if (!enabled || isPaused) return;

    let frameCount = 0;
    let lastFrameTime = performance.now();
    let rafId: number;

    // Funzione per contare i frame
    const countFrame = () => {
      frameCount++;
      rafId = requestAnimationFrame(countFrame);
    };

    // Avvia il conteggio dei frame
    countFrame();

    // Timer per campionare le metriche
    const intervalId = setInterval(() => {
      const now = performance.now();
      const elapsedMs = now - lastFrameTime;
      const fps = Math.round((frameCount / elapsedMs) * 1000);
      
      // Memoria utilizzata (se disponibile)
      let memory = 0;
      if (window.performance && (performance as any).memory) {
        memory = Math.round(((performance as any).memory.usedJSHeapSize / (performance as any).memory.jsHeapSizeLimit) * 100);
      }

      // Simula il tempo di rendering (in una app reale si misurerebbe con React Profiler)
      const renderTime = Math.random() * 10 + 5;
      
      // Simula la latenza API (in una app reale si misurerebbe con timing reali)
      const apiLatency = Math.random() * 200 + 50;

      // Aggiungi la nuova metrica
      setMetrics(prev => {
        const newMetrics = [...prev, {
          timestamp: Date.now(),
          fps,
          memory,
          renderTime,
          apiLatency
        }];
        
        // Limita il numero di campioni
        return newMetrics.slice(-maxSamples);
      });

      // Resetta il conteggio dei frame
      frameCount = 0;
      lastFrameTime = now;
    }, sampleInterval);

    return () => {
      clearInterval(intervalId);
      cancelAnimationFrame(rafId);
    };
  }, [enabled, sampleInterval, maxSamples, isPaused]);

  // Formatta i dati per il grafico
  const chartData = metrics.map((metric, index) => ({
    name: index,
    fps: metric.fps,
    memory: metric.memory,
    renderTime: metric.renderTime,
    apiLatency: metric.apiLatency
  }));

  // Calcola le metriche medie
  const averageMetrics = {
    fps: metrics.length ? Math.round(metrics.reduce((sum, m) => sum + m.fps, 0) / metrics.length) : 0,
    memory: metrics.length ? Math.round(metrics.reduce((sum, m) => sum + m.memory, 0) / metrics.length) : 0,
    renderTime: metrics.length ? Math.round(metrics.reduce((sum, m) => sum + m.renderTime, 0) / metrics.length * 10) / 10 : 0,
    apiLatency: metrics.length ? Math.round(metrics.reduce((sum, m) => sum + m.apiLatency, 0) / metrics.length) : 0
  };

  // Valuta le performance
  const getFpsStatus = (fps: number) => {
    if (fps >= 55) return { label: 'Ottimo', color: 'bg-green-500' };
    if (fps >= 30) return { label: 'Buono', color: 'bg-yellow-500' };
    return { label: 'Scarso', color: 'bg-red-500' };
  };

  const getMemoryStatus = (memory: number) => {
    if (memory <= 50) return { label: 'Ottimo', color: 'bg-green-500' };
    if (memory <= 80) return { label: 'Buono', color: 'bg-yellow-500' };
    return { label: 'Alto', color: 'bg-red-500' };
  };

  const getRenderTimeStatus = (time: number) => {
    if (time <= 8) return { label: 'Veloce', color: 'bg-green-500' };
    if (time <= 15) return { label: 'Accettabile', color: 'bg-yellow-500' };
    return { label: 'Lento', color: 'bg-red-500' };
  };

  const getApiLatencyStatus = (latency: number) => {
    if (latency <= 100) return { label: 'Veloce', color: 'bg-green-500' };
    if (latency <= 200) return { label: 'Accettabile', color: 'bg-yellow-500' };
    return { label: 'Lento', color: 'bg-red-500' };
  };

  const fpsStatus = getFpsStatus(averageMetrics.fps);
  const memoryStatus = getMemoryStatus(averageMetrics.memory);
  const renderTimeStatus = getRenderTimeStatus(averageMetrics.renderTime);
  const apiLatencyStatus = getApiLatencyStatus(averageMetrics.apiLatency);

  if (!enabled) return null;

  return (
    <>
      {/* Pulsante per mostrare/nascondere il monitor */}
      <Button
        variant="outline"
        size="sm"
        className="fixed bottom-4 right-4 z-50 opacity-70 hover:opacity-100"
        onClick={() => setIsVisible(!isVisible)}
      >
        <Gauge className="w-4 h-4 mr-2" />
        Performance
      </Button>

      {/* Monitor di performance */}
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          className="fixed bottom-16 right-4 z-50 w-96 bg-background border border-border rounded-lg shadow-lg"
        >
          <div className="p-3 border-b border-border flex items-center justify-between">
            <div className="flex items-center">
              <Gauge className="w-5 h-5 mr-2 text-primary" />
              <h3 className="font-medium">Monitor di Performance</h3>
            </div>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={() => setIsPaused(!isPaused)}
              >
                {isPaused ? <RefreshCw className="h-4 w-4" /> : <Clock className="h-4 w-4" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={() => setIsCollapsed(!isCollapsed)}
              >
                {isCollapsed ? <BarChart3 className="h-4 w-4" /> : <Cpu className="h-4 w-4" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={() => setIsVisible(false)}
              >
                ✕
              </Button>
            </div>
          </div>

          <div className="p-3">
            {/* Metriche principali */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              <Card className="p-2">
                <div className="text-xs text-muted-foreground">FPS</div>
                <div className="flex items-center justify-between">
                  <div className="text-lg font-semibold">{averageMetrics.fps}</div>
                  <Badge className={fpsStatus.color}>{fpsStatus.label}</Badge>
                </div>
              </Card>
              <Card className="p-2">
                <div className="text-xs text-muted-foreground">Memoria</div>
                <div className="flex items-center justify-between">
                  <div className="text-lg font-semibold">{averageMetrics.memory}%</div>
                  <Badge className={memoryStatus.color}>{memoryStatus.label}</Badge>
                </div>
              </Card>
              <Card className="p-2">
                <div className="text-xs text-muted-foreground">Tempo Rendering</div>
                <div className="flex items-center justify-between">
                  <div className="text-lg font-semibold">{averageMetrics.renderTime} ms</div>
                  <Badge className={renderTimeStatus.color}>{renderTimeStatus.label}</Badge>
                </div>
              </Card>
              <Card className="p-2">
                <div className="text-xs text-muted-foreground">Latenza API</div>
                <div className="flex items-center justify-between">
                  <div className="text-lg font-semibold">{averageMetrics.apiLatency} ms</div>
                  <Badge className={apiLatencyStatus.color}>{apiLatencyStatus.label}</Badge>
                </div>
              </Card>
            </div>

            {/* Grafici dettagliati (espandibili) */}
            {!isCollapsed && (
              <Tabs defaultValue="fps" className="w-full">
                <TabsList className="w-full grid grid-cols-4">
                  <TabsTrigger value="fps">FPS</TabsTrigger>
                  <TabsTrigger value="memory">Memoria</TabsTrigger>
                  <TabsTrigger value="render">Rendering</TabsTrigger>
                  <TabsTrigger value="api">API</TabsTrigger>
                </TabsList>
                <TabsContent value="fps" className="mt-2">
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis domain={[0, 'dataMax + 10']} />
                      <Tooltip />
                      <Line type="monotone" dataKey="fps" stroke="#8884d8" activeDot={{ r: 8 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </TabsContent>
                <TabsContent value="memory" className="mt-2">
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Line type="monotone" dataKey="memory" stroke="#82ca9d" activeDot={{ r: 8 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </TabsContent>
                <TabsContent value="render" className="mt-2">
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="renderTime" stroke="#ffc658" activeDot={{ r: 8 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </TabsContent>
                <TabsContent value="api" className="mt-2">
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="apiLatency" stroke="#ff7300" activeDot={{ r: 8 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </TabsContent>
              </Tabs>
            )}
          </div>
        </motion.div>
      )}
    </>
  );
}
