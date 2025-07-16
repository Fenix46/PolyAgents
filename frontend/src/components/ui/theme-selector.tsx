import React from 'react';
import { Button } from '@/components/ui/button';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel
} from '@/components/ui/dropdown-menu';
import { Sun, Moon, Monitor, Palette, Layout, Eye } from 'lucide-react';
import { useTheme, ThemeType, LayoutType } from '@/contexts/ThemeContext';

export function ThemeSelector() {
  const { theme, layout, setTheme, setLayout } = useTheme();

  const themeOptions: { value: ThemeType; label: string; icon: React.ReactNode }[] = [
    { value: 'light', label: 'Chiaro', icon: <Sun className="h-4 w-4 mr-2" /> },
    { value: 'dark', label: 'Scuro', icon: <Moon className="h-4 w-4 mr-2" /> },
    { value: 'system', label: 'Sistema', icon: <Monitor className="h-4 w-4 mr-2" /> },
    { value: 'high-contrast', label: 'Alto contrasto', icon: <Eye className="h-4 w-4 mr-2" /> },
  ];

  const layoutOptions: { value: LayoutType; label: string }[] = [
    { value: 'default', label: 'Standard' },
    { value: 'compact', label: 'Compatto' },
    { value: 'comfortable', label: 'Confortevole' },
    { value: 'focused', label: 'Focalizzato' },
  ];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="w-8 h-8">
          <Palette className="h-4 w-4" />
          <span className="sr-only">Cambia tema</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>Tema</DropdownMenuLabel>
        {themeOptions.map((option) => (
          <DropdownMenuItem
            key={option.value}
            onClick={() => setTheme(option.value)}
            className="flex items-center cursor-pointer"
          >
            {option.icon}
            {option.label}
            {theme === option.value && (
              <span className="ml-auto">✓</span>
            )}
          </DropdownMenuItem>
        ))}
        
        <DropdownMenuSeparator />
        
        <DropdownMenuLabel>Layout</DropdownMenuLabel>
        {layoutOptions.map((option) => (
          <DropdownMenuItem
            key={option.value}
            onClick={() => setLayout(option.value)}
            className="flex items-center cursor-pointer"
          >
            <Layout className="h-4 w-4 mr-2" />
            {option.label}
            {layout === option.value && (
              <span className="ml-auto">✓</span>
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
