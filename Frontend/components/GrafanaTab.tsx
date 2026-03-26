'use client';

import { useState } from 'react';
import { TabContent } from './TabContent';

export function GrafanaTab() {
  const [urlInputValue, setUrlInputValue] = useState('http://localhost:3000');
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
      title="Grafana"
      icon={null}
      color="orange"
      urlInputValue={urlInputValue}
      onUrlChange={setUrlInputValue}
      isConnected={isConnected}
      onConnect={handleConnect}
      onOpen={handleOpen}
    >
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-gradient-to-br from-orange-500/10 to-orange-600/10 rounded-lg border border-orange-500/20">
            <h3 className="font-semibold text-orange-400 mb-2">📊 Grafana Dashboard</h3>
            <p className="text-sm text-gray-300">Connected to infrastructure metrics and visualization platform.</p>
          </div>
          <div className="p-4 bg-gradient-to-br from-orange-500/10 to-orange-600/10 rounded-lg border border-orange-500/20">
            <h3 className="font-semibold text-orange-400 mb-2">🎯 Default Credentials</h3>
            <p className="text-sm text-gray-300">Username: admin<br/>Password: admin</p>
          </div>
        </div>
      </div>
    </TabContent>
  );
}
