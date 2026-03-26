'use client';

import { useState } from 'react';
import { TabContent } from './TabContent';

export function PrometheusTab() {
  const [urlInputValue, setUrlInputValue] = useState('http://localhost:9090');
  const [isConnected, setIsConnected] = useState(false);

  const handleConnect = () => {
    if (urlInputValue) {
      setIsConnected(true);
    }
  };

  const handleOpen = () => {
    window.open(urlInputValue, '_blank');
  };

  return (
    <TabContent
      title="Prometheus"
      icon={null}
      color="red"
      urlInputValue={urlInputValue}
      onUrlChange={setUrlInputValue}
      isConnected={isConnected}
      onConnect={handleConnect}
      onOpen={handleOpen}
    >
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-gradient-to-br from-red-500/10 to-red-600/10 rounded-lg border border-red-500/20">
            <h3 className="font-semibold text-red-400 mb-2">📈 Prometheus Metrics</h3>
            <p className="text-sm text-gray-300">Time-series database for collecting and monitoring system metrics.</p>
          </div>
          <div className="p-4 bg-gradient-to-br from-red-500/10 to-red-600/10 rounded-lg border border-red-500/20">
            <h3 className="font-semibold text-red-400 mb-2">🔍 Metrics Port</h3>
            <p className="text-sm text-gray-300">Default Port: 9090<br/>Query Language: PromQL</p>
          </div>
        </div>
      </div>
    </TabContent>
  );
}
