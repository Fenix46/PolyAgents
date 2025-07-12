import { useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { 
  Settings, 
  Menu, 
  Zap, 
  Wifi, 
  WifiOff, 
  AlertCircle,
  User
} from 'lucide-react';
import { ConnectionStatus } from '@/types';

interface HeaderProps {
  connectionStatus: ConnectionStatus;
  onToggleSidebar: () => void;
  onOpenSettings: () => void;
}

export default function Header({ 
  connectionStatus, 
  onToggleSidebar, 
  onOpenSettings 
}: HeaderProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);

  const getStatusIcon = () => {
    switch (connectionStatus.status) {
      case 'connected':
        return <Wifi className="w-4 h-4 text-success" />;
      case 'connecting':
        return <Wifi className="w-4 h-4 text-warning animate-pulse" />;
      case 'disconnected':
        return <WifiOff className="w-4 h-4 text-muted-foreground" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-destructive" />;
      default:
        return <WifiOff className="w-4 h-4 text-muted-foreground" />;
    }
  };

  const getStatusText = () => {
    switch (connectionStatus.status) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'disconnected':
        return 'Disconnected';
      case 'error':
        return 'Connection Error';
      default:
        return 'Unknown';
    }
  };

  const getStatusColor = () => {
    switch (connectionStatus.status) {
      case 'connected':
        return 'bg-success/20 text-success border-success/30';
      case 'connecting':
        return 'bg-warning/20 text-warning border-warning/30';
      case 'disconnected':
        return 'bg-muted/20 text-muted-foreground border-muted/30';
      case 'error':
        return 'bg-destructive/20 text-destructive border-destructive/30';
      default:
        return 'bg-muted/20 text-muted-foreground border-muted/30';
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 glass-effect border-b border-border h-16 flex items-center px-4">
      <div className="flex items-center space-x-4">
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={onToggleSidebar}
          className="md:hidden"
        >
          <Menu className="w-5 h-5" />
        </Button>

        <motion.div 
          className="flex items-center space-x-3"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex items-center space-x-2">
            <Zap className="w-6 h-6 text-primary" />
            <h1 className="text-xl font-bold text-gradient">PolyAgents</h1>
          </div>
          
          <Badge variant="outline" className="text-xs">
            Multi-Agent AI
          </Badge>
        </motion.div>
      </div>

      <div className="flex-1" />

      <div className="flex items-center space-x-3">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.2 }}
        >
          <Badge 
            variant="outline" 
            className={`${getStatusColor()} flex items-center space-x-2`}
          >
            {getStatusIcon()}
            <span className="text-xs font-medium">{getStatusText()}</span>
          </Badge>
        </motion.div>

        <Button 
          variant="ghost" 
          size="icon"
          onClick={onOpenSettings}
          className="surface-hover"
        >
          <Settings className="w-5 h-5" />
        </Button>

        <div className="relative">
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="surface-hover"
          >
            <Avatar className="w-8 h-8">
              <AvatarFallback className="bg-primary/20 text-primary">
                <User className="w-4 h-4" />
              </AvatarFallback>
            </Avatar>
          </Button>

          {showUserMenu && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute right-0 top-12 w-48 bg-card border border-border rounded-lg shadow-lg p-2 z-50"
            >
              <div className="px-3 py-2 border-b border-border">
                <p className="text-sm font-medium">User</p>
                <p className="text-xs text-muted-foreground">API Connected</p>
              </div>
              <div className="mt-2">
                <Button 
                  variant="ghost" 
                  className="w-full justify-start text-sm"
                  onClick={onOpenSettings}
                >
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </Button>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </header>
  );
}