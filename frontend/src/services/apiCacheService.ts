import { Message, AgentResponse, Conversation } from '@/types';

// Configurazione della cache
interface CacheConfig {
  maxAge: number;        // Tempo massimo in ms prima che un dato sia considerato obsoleto
  staleWhileRevalidate: number; // Tempo in ms durante il quale i dati obsoleti possono essere usati mentre vengono aggiornati
  maxEntries: number;    // Numero massimo di voci nella cache
}

// Struttura di una voce nella cache
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
  staleUntil: number;
  key: string;
}

class ApiCacheService {
  private cache: Map<string, CacheEntry<any>>;
  private config: CacheConfig;
  private pendingRequests: Map<string, Promise<any>>;
  private storageKey: string;

  constructor(config?: Partial<CacheConfig>) {
    this.config = {
      maxAge: 5 * 60 * 1000, // 5 minuti
      staleWhileRevalidate: 30 * 60 * 1000, // 30 minuti
      maxEntries: 100,
      ...config
    };
    this.cache = new Map();
    this.pendingRequests = new Map();
    this.storageKey = 'polyagent-api-cache';
    this.loadFromStorage();
  }

  // Genera una chiave univoca per una richiesta API
  private generateCacheKey(url: string, params?: Record<string, any>): string {
    const paramString = params ? JSON.stringify(params) : '';
    return `${url}:${paramString}`;
  }

  // Carica la cache dal localStorage
  private loadFromStorage(): void {
    try {
      const storedCache = localStorage.getItem(this.storageKey);
      if (storedCache) {
        const entries = JSON.parse(storedCache) as Array<[string, CacheEntry<any>]>;
        
        // Filtra le voci scadute (oltre il periodo staleWhileRevalidate)
        const now = Date.now();
        const validEntries = entries.filter(([_, entry]) => entry.staleUntil > now);
        
        this.cache = new Map(validEntries);
        
        // Se abbiamo troppe voci, rimuovi le più vecchie
        this.pruneCache();
      }
    } catch (error) {
      console.error('Errore nel caricamento della cache:', error);
      this.cache = new Map();
    }
  }

  // Salva la cache nel localStorage
  private saveToStorage(): void {
    try {
      const entries = Array.from(this.cache.entries());
      localStorage.setItem(this.storageKey, JSON.stringify(entries));
    } catch (error) {
      console.error('Errore nel salvataggio della cache:', error);
    }
  }

  // Rimuovi le voci più vecchie se la cache supera il limite
  private pruneCache(): void {
    if (this.cache.size <= this.config.maxEntries) return;

    // Converti la mappa in array e ordina per timestamp
    const entries = Array.from(this.cache.entries())
      .sort((a, b) => a[1].timestamp - b[1].timestamp);

    // Rimuovi le voci più vecchie
    const entriesToRemove = entries.slice(0, entries.length - this.config.maxEntries);
    entriesToRemove.forEach(([key]) => this.cache.delete(key));
  }

  // Verifica se un dato è fresco, obsoleto o scaduto
  private checkFreshness(entry: CacheEntry<any>): 'fresh' | 'stale' | 'expired' {
    const now = Date.now();
    if (now < entry.expiresAt) {
      return 'fresh';
    } else if (now < entry.staleUntil) {
      return 'stale';
    } else {
      return 'expired';
    }
  }

  // Ottieni un dato dalla cache con strategia stale-while-revalidate
  async get<T>(
    url: string, 
    fetchFn: () => Promise<T>, 
    params?: Record<string, any>
  ): Promise<T> {
    const cacheKey = this.generateCacheKey(url, params);
    const cachedEntry = this.cache.get(cacheKey);

    // Se non c'è nulla in cache o è scaduto, esegui la richiesta
    if (!cachedEntry || this.checkFreshness(cachedEntry) === 'expired') {
      return this.fetchAndCache(cacheKey, fetchFn);
    }

    // Se il dato è obsoleto, restituiscilo ma aggiornalo in background
    if (this.checkFreshness(cachedEntry) === 'stale') {
      // Avvia l'aggiornamento in background se non è già in corso
      if (!this.pendingRequests.has(cacheKey)) {
        this.fetchAndCache(cacheKey, fetchFn)
          .catch(error => console.error(`Errore nell'aggiornamento in background:`, error));
      }
      return cachedEntry.data;
    }

    // Il dato è fresco, restituiscilo
    return cachedEntry.data;
  }

  // Esegui una richiesta e memorizza il risultato nella cache
  private async fetchAndCache<T>(cacheKey: string, fetchFn: () => Promise<T>): Promise<T> {
    // Se c'è già una richiesta in corso per questa chiave, restituisci quella
    if (this.pendingRequests.has(cacheKey)) {
      return this.pendingRequests.get(cacheKey) as Promise<T>;
    }

    // Crea una nuova richiesta
    const requestPromise = fetchFn()
      .then(data => {
        const now = Date.now();
        const entry: CacheEntry<T> = {
          data,
          timestamp: now,
          expiresAt: now + this.config.maxAge,
          staleUntil: now + this.config.maxAge + this.config.staleWhileRevalidate,
          key: cacheKey
        };
        
        this.cache.set(cacheKey, entry);
        this.pruneCache();
        this.saveToStorage();
        this.pendingRequests.delete(cacheKey);
        
        return data;
      })
      .catch(error => {
        this.pendingRequests.delete(cacheKey);
        throw error;
      });

    // Memorizza la richiesta in corso
    this.pendingRequests.set(cacheKey, requestPromise);
    
    return requestPromise;
  }

  // Invalida una specifica voce nella cache
  invalidate(url: string, params?: Record<string, any>): void {
    const cacheKey = this.generateCacheKey(url, params);
    this.cache.delete(cacheKey);
    this.saveToStorage();
  }

  // Invalida tutte le voci che iniziano con un certo URL
  invalidateByPrefix(urlPrefix: string): void {
    for (const key of this.cache.keys()) {
      if (key.startsWith(urlPrefix)) {
        this.cache.delete(key);
      }
    }
    this.saveToStorage();
  }

  // Pulisci tutta la cache
  clear(): void {
    this.cache.clear();
    this.saveToStorage();
  }
}

// Esporta un'istanza singleton
export const apiCache = new ApiCacheService();

// Funzione di utilità per avvolgere le chiamate API con la cache
export async function cachedApiCall<T>(
  url: string, 
  fetchFn: () => Promise<T>, 
  params?: Record<string, any>
): Promise<T> {
  return apiCache.get(url, fetchFn, params);
}
