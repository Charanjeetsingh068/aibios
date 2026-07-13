"use client";

import { Loader2 } from 'lucide-react';

export default function RootLoading() {
  return (
    <div 
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: 'var(--bg-primary)',
        width: '100vw'
      }}
    >
      <Loader2 size={36} className="animate-spin" style={{ color: 'var(--brand)' }} />
    </div>
  );
}
