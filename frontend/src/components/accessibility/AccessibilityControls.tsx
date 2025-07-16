import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
  DropdownMenuCheckboxItem
} from '@/components/ui/dropdown-menu';
import { 
  Accessibility, 
  Type, 
  ZoomIn, 
  Contrast, 
  MousePointer, 
  Keyboard, 
  Volume2 
} from 'lucide-react';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

interface AccessibilitySettings {
  fontSize: number;
  highContrast: boolean;
  reduceMotion: boolean;
  screenReader: boolean;
  keyboardNavigation: boolean;
  textToSpeech: boolean;
}

export function AccessibilityControls() {
  const [settings, setSettings] = useState<AccessibilitySettings>({
    fontSize: 100, // percentuale
    highContrast: false,
    reduceMotion: false,
    screenReader: false,
    keyboardNavigation: true,
    textToSpeech: false
  });
  
  const [menuOpen, setMenuOpen] = useState(false);

  // Applica le impostazioni di accessibilità al documento
  React.useEffect(() => {
    // Font size
    document.documentElement.style.fontSize = `${settings.fontSize}%`;
    
    // Classi per le altre impostazioni
    document.documentElement.classList.toggle('high-contrast', settings.highContrast);
    document.documentElement.classList.toggle('reduce-motion', settings.reduceMotion);
    document.documentElement.classList.toggle('screen-reader-enabled', settings.screenReader);
    document.documentElement.classList.toggle('keyboard-navigation', settings.keyboardNavigation);
    document.documentElement.classList.toggle('text-to-speech', settings.textToSpeech);
    
    // Salva le impostazioni nel localStorage
    localStorage.setItem('accessibility-settings', JSON.stringify(settings));
  }, [settings]);

  // Carica le impostazioni dal localStorage all'avvio
  React.useEffect(() => {
    const savedSettings = localStorage.getItem('accessibility-settings');
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings));
      } catch (e) {
        console.error('Errore nel caricamento delle impostazioni di accessibilità:', e);
      }
    }
    
    // Aggiungi attributi ARIA per migliorare l'accessibilità
    document.body.setAttribute('role', 'application');
    document.body.setAttribute('aria-label', 'PolyAgent Chat Interface');
  }, []);

  const updateSetting = <K extends keyof AccessibilitySettings>(
    key: K, 
    value: AccessibilitySettings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  return (
    <DropdownMenu open={menuOpen} onOpenChange={setMenuOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="w-8 h-8" aria-label="Impostazioni di accessibilità">
          <Accessibility className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-72">
        <DropdownMenuLabel>Accessibilità</DropdownMenuLabel>
        
        <div className="p-2">
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <Label className="text-sm flex items-center">
                <Type className="h-4 w-4 mr-2" />
                Dimensione testo
              </Label>
              <span className="text-xs">{settings.fontSize}%</span>
            </div>
            <Slider
              value={[settings.fontSize]}
              min={75}
              max={200}
              step={5}
              onValueChange={(value) => updateSetting('fontSize', value[0])}
              aria-label="Dimensione del testo"
            />
          </div>
          
          <DropdownMenuSeparator />
          
          <div className="space-y-2">
            <div className="flex items-center justify-between py-1">
              <Label htmlFor="high-contrast" className="text-sm flex items-center cursor-pointer">
                <Contrast className="h-4 w-4 mr-2" />
                Alto contrasto
              </Label>
              <Switch
                id="high-contrast"
                checked={settings.highContrast}
                onCheckedChange={(checked) => updateSetting('highContrast', checked)}
                aria-label="Attiva/disattiva alto contrasto"
              />
            </div>
            
            <div className="flex items-center justify-between py-1">
              <Label htmlFor="reduce-motion" className="text-sm flex items-center cursor-pointer">
                <ZoomIn className="h-4 w-4 mr-2" />
                Riduci animazioni
              </Label>
              <Switch
                id="reduce-motion"
                checked={settings.reduceMotion}
                onCheckedChange={(checked) => updateSetting('reduceMotion', checked)}
                aria-label="Attiva/disattiva riduzione animazioni"
              />
            </div>
            
            <div className="flex items-center justify-between py-1">
              <Label htmlFor="screen-reader" className="text-sm flex items-center cursor-pointer">
                <MousePointer className="h-4 w-4 mr-2" />
                Supporto screen reader
              </Label>
              <Switch
                id="screen-reader"
                checked={settings.screenReader}
                onCheckedChange={(checked) => updateSetting('screenReader', checked)}
                aria-label="Attiva/disattiva supporto screen reader"
              />
            </div>
            
            <div className="flex items-center justify-between py-1">
              <Label htmlFor="keyboard-navigation" className="text-sm flex items-center cursor-pointer">
                <Keyboard className="h-4 w-4 mr-2" />
                Navigazione tastiera
              </Label>
              <Switch
                id="keyboard-navigation"
                checked={settings.keyboardNavigation}
                onCheckedChange={(checked) => updateSetting('keyboardNavigation', checked)}
                aria-label="Attiva/disattiva navigazione da tastiera"
              />
            </div>
            
            <div className="flex items-center justify-between py-1">
              <Label htmlFor="text-to-speech" className="text-sm flex items-center cursor-pointer">
                <Volume2 className="h-4 w-4 mr-2" />
                Sintesi vocale
              </Label>
              <Switch
                id="text-to-speech"
                checked={settings.textToSpeech}
                onCheckedChange={(checked) => updateSetting('textToSpeech', checked)}
                aria-label="Attiva/disattiva sintesi vocale"
              />
            </div>
          </div>
        </div>
        
        <DropdownMenuSeparator />
        
        <DropdownMenuItem 
          onClick={() => {
            // Ripristina le impostazioni predefinite
            setSettings({
              fontSize: 100,
              highContrast: false,
              reduceMotion: false,
              screenReader: false,
              keyboardNavigation: true,
              textToSpeech: false
            });
            setMenuOpen(false);
          }}
          className="justify-center text-center"
        >
          Ripristina impostazioni predefinite
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
