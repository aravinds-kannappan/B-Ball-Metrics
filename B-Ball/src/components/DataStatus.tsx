import React from 'react';
import { Wifi, WifiOff, RefreshCw, AlertCircle } from 'lucide-react';

interface DataStatusProps {
  isLoading: boolean;
  hasError: boolean;
  lastUpdated: Date | null;
  onRefresh: () => void;
}

export const DataStatus: React.FC<DataStatusProps> = ({
  isLoading,
  hasError,
  lastUpdated,
  onRefresh
}) => {
  const getStatusIcon = () => {
    if (isLoading) return <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />;
    if (hasError) return <WifiOff className="w-4 h-4 text-red-400" />;
    return <Wifi className="w-4 h-4 text-green-400" />;
  };

  const getStatusText = () => {
    if (isLoading) return 'Loading NBA data...';
    if (hasError) return 'Connection error';
    if (lastUpdated) {
      const timeDiff = Date.now() - lastUpdated.getTime();
      const minutes = Math.floor(timeDiff / 60000);
      return `Updated ${minutes}m ago`;
    }
    return 'No data';
  };

  const getStatusColor = () => {
    if (isLoading) return 'text-blue-400';
    if (hasError) return 'text-red-400';
    return 'text-green-400';
  };

  return (
    <div className="flex items-center gap-2 text-sm">
      {getStatusIcon()}
      <span className={getStatusColor()}>{getStatusText()}</span>
      {hasError && (
        <button
          onClick={onRefresh}
          className="flex items-center gap-1 px-2 py-1 bg-red-900/20 text-red-400 rounded text-xs hover:bg-red-900/30 transition-colors"
        >
          <AlertCircle className="w-3 h-3" />
          Retry
        </button>
      )}
      {!isLoading && !hasError && (
        <button
          onClick={onRefresh}
          className="px-2 py-1 bg-slate-700 text-slate-300 rounded text-xs hover:bg-slate-600 transition-colors"
        >
          Refresh
        </button>
      )}
    </div>
  );
};