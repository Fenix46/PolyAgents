import React, { createContext, useContext, useState, useEffect } from 'react';

export type ThemeType = 'dark' | 'light' | 'system' | 'high-contrast';
export type LayoutType = 'default' | 'compact' | 'comfortable' | 'focused';

interface ThemeContextType {
  theme: ThemeType;
  layout: LayoutType;
  setTheme: (theme: ThemeType) => void;
  setLayout: (layout: LayoutType) => void;
  toggleTheme: () => void;
}

const defaultThemeContext: ThemeContextType = {
  theme: 'dark',
  layout: 'default',
  setTheme: () => {},
  setLayout: () => {},
  toggleTheme: () => {},
};

export const ThemeContext = createContext<ThemeContextType>(defaultThemeContext);

export const useTheme = () => useContext(ThemeContext);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<ThemeType>(() => {
    // Try to get the theme from localStorage
    const savedTheme = localStorage.getItem('polyagent-theme');
    return (savedTheme as ThemeType) || 'dark';
  });
  
  const [layout, setLayoutState] = useState<LayoutType>(() => {
    // Try to get the layout from localStorage
    const savedLayout = localStorage.getItem('polyagent-layout');
    return (savedLayout as LayoutType) || 'default';
  });

  useEffect(() => {
    // Apply theme to document
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('polyagent-theme', theme);
    
    // Apply layout class
    document.documentElement.setAttribute('data-layout', layout);
    localStorage.setItem('polyagent-layout', layout);
  }, [theme, layout]);

  const setTheme = (newTheme: ThemeType) => {
    setThemeState(newTheme);
  };

  const setLayout = (newLayout: LayoutType) => {
    setLayoutState(newLayout);
  };

  const toggleTheme = () => {
    setThemeState(prevTheme => prevTheme === 'dark' ? 'light' : 'dark');
  };

  return (
    <ThemeContext.Provider value={{ theme, layout, setTheme, setLayout, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};
