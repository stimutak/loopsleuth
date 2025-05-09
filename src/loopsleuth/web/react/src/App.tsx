import React, { useEffect, useState } from 'react';
import { FixedSizeGrid as Grid, GridChildComponentProps } from 'react-window';
import './App.css';

interface Clip {
  id: number;
  filename: string;
  thumb_url: string;
}

const COLUMN_COUNT = 5;
const ROW_HEIGHT = 160;
const COLUMN_WIDTH = 220;
const API_LIMIT = 500; // FastAPI enforces limit <= 500

function App() {
  const [clips, setClips] = useState<Clip[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/clips?offset=0&limit=${API_LIMIT}`)
      .then((res) => res.json())
      .then((data) => {
        setClips(data.clips || []);
        setLoading(false);
      });
  }, []);

  const rowCount = Math.ceil(clips.length / COLUMN_COUNT);

  return (
    <div style={{ background: '#181a1b', minHeight: '100vh', color: '#f0f4fa', fontFamily: 'Inter, Segoe UI, Arial, sans-serif' }}>
      <h1 style={{ padding: '1em 2em 0.5em 2em', fontWeight: 700, fontSize: '2em', color: '#3fa7ff' }}>LoopSleuth React Grid</h1>
      {loading ? (
        <div style={{ textAlign: 'center', marginTop: '4em', color: '#3fa7ff' }}>Loading clips...</div>
      ) : (
        <Grid
          columnCount={COLUMN_COUNT}
          columnWidth={COLUMN_WIDTH}
          height={window.innerHeight - 120}
          rowCount={rowCount}
          rowHeight={ROW_HEIGHT}
          width={COLUMN_COUNT * COLUMN_WIDTH + 20}
          style={{ margin: '2em auto', background: '#23232a', borderRadius: 12, boxShadow: '0 2px 16px #000a' }}
        >
          {({ columnIndex, rowIndex, style }: GridChildComponentProps) => {
            const idx = rowIndex * COLUMN_COUNT + columnIndex;
            if (idx >= clips.length) return null;
            const clip = clips[idx];
            return (
              <div
                style={{
                  ...style,
                  padding: 12,
                  boxSizing: 'border-box',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: '#23232a',
                  borderRadius: 8,
                  margin: 6,
                }}
                key={clip.id}
              >
                <img
                  src={clip.thumb_url || '/static/placeholder.png'}
                  alt={clip.filename}
                  style={{ width: 180, height: 100, objectFit: 'cover', borderRadius: 4, background: '#181a1b', marginBottom: 8 }}
                  loading="lazy"
                />
                <div style={{ color: '#f0f4fa', fontSize: '1em', textAlign: 'center', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {clip.filename}
                </div>
              </div>
            );
          }}
        </Grid>
      )}
    </div>
  );
}

export default App;
