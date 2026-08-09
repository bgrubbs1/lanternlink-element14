import React from 'react';
import {
  AbsoluteFill,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const C = {
  bg: '#050b12',
  panel: '#0c1722',
  line: '#203447',
  text: '#f4f8fa',
  muted: '#8ea6b7',
  cyan: '#5ce1e6',
  green: '#64f2a6',
  amber: '#ffc857',
  red: '#ff7885',
};

const Fade: React.FC<React.PropsWithChildren<{accent?: string}>> = ({children, accent = C.cyan}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  return (
    <AbsoluteFill
      style={{
        opacity: interpolate(frame, [0, 14, durationInFrames - 14, durationInFrames], [0, 1, 1, 0], {
          extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
        }),
        padding: 88,
        color: C.text,
        fontFamily: 'Segoe UI, Arial, sans-serif',
        background: `radial-gradient(circle at 88% 0%, ${accent}23, transparent 34%), radial-gradient(circle at 5% 110%, ${C.green}13, transparent 38%), ${C.bg}`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

const Label: React.FC<React.PropsWithChildren> = ({children}) => (
  <div style={{color: C.cyan, fontFamily: 'Consolas, monospace', fontSize: 23, fontWeight: 900, letterSpacing: 5}}>
    {children}
  </div>
);

const Title: React.FC<React.PropsWithChildren<{size?: number}>> = ({children, size = 88}) => (
  <h1 style={{fontSize: size, lineHeight: 1.02, letterSpacing: -3, margin: '22px 0 28px'}}>{children}</h1>
);

const Pill: React.FC<React.PropsWithChildren<{color?: string}>> = ({children, color = C.green}) => (
  <span style={{border: `2px solid ${color}`, borderRadius: 999, color, padding: '10px 18px', fontFamily: 'Consolas, monospace', fontSize: 20, fontWeight: 800}}>
    {children}
  </span>
);

const Hook = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 18}});
  const pulse = 0.55 + 0.45 * Math.sin(frame / 7);
  return (
    <Fade>
      <div style={{width: 1220, marginTop: 95, transform: `translateY(${(1 - enter) * 45}px)`}}>
        <Label>LANTERNLINK / FUNCTIONAL TWO-DEVICE DEMO</Label>
        <Title size={118}>One signed word.<br/><span style={{color: C.cyan}}>One visible connection.</span></Title>
        <p style={{fontSize: 32, color: C.muted, lineHeight: 1.5, maxWidth: 1100}}>
          A cloud-free local signal becomes text and a Morse-timed browser lantern.
        </p>
      </div>
      <div style={{position: 'absolute', right: 170, bottom: 160, width: 260, height: 260, borderRadius: 999, border: `5px solid ${C.cyan}`, boxShadow: `0 0 ${90 * pulse}px ${C.amber}`, background: `radial-gradient(circle, ${C.amber} 0 28%, ${C.panel} 30% 62%, ${C.bg} 64%)`}} />
      <div style={{position: 'absolute', left: 88, bottom: 74, display: 'flex', gap: 18}}>
        <Pill>NO CLOUD</Pill><Pill color={C.amber}>NO MESSAGE LOG</Pill><Pill color={C.cyan}>HMAC-SHA256</Pill>
      </div>
    </Fade>
  );
};

const Architecture = () => (
  <Fade accent={C.green}>
    <Img src={staticFile('architecture.svg')} style={{position: 'absolute', left: 60, top: 35, width: 1800, borderRadius: 24, border: `2px solid ${C.line}`}} />
  </Fade>
);

const LiveResult = () => {
  return (
    <Fade accent={C.amber}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <div><Label>LIVE RECEIVER CAPTURE / 2026-08-09</Label><Title size={68}>Mac sender → Windows receiver</Title></div>
        <Pill color={C.amber}>REAL CROSS-DEVICE TEST</Pill>
      </div>
      <div style={{position: 'absolute', left: 130, right: 130, top: 230, bottom: 50, overflow: 'hidden', borderRadius: 26, border: `3px solid ${C.cyan}`, background: C.panel}}>
        <Img src={staticFile('lanternlink-live.jpg')} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
      </div>
    </Fade>
  );
};

const Verification = () => (
  <Fade accent={C.red}>
    <Label>WHY THE PACKET WAS ACCEPTED</Label>
    <Title size={78}>Every green result corresponds to a real check.</Title>
    <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 30, marginTop: 55}}>
      {[
        ['SIGNED', 'HMAC-SHA256 matches the shared secret', C.cyan],
        ['FRESH', 'timestamp is inside the 90-second window', C.green],
        ['UNIQUE', 'the nonce has not appeared before', C.amber],
      ].map(([name, text, color]) => (
        <div key={name} style={{padding: 42, minHeight: 350, border: `3px solid ${color}`, borderRadius: 24, background: C.panel}}>
          <div style={{fontFamily: 'Consolas, monospace', fontSize: 30, color, fontWeight: 900}}>{name}</div>
          <div style={{fontSize: 31, lineHeight: 1.45, marginTop: 78}}>{text}</div>
        </div>
      ))}
    </div>
    <div style={{fontFamily: 'Consolas, monospace', color: C.muted, fontSize: 25, marginTop: 55}}>
      READY → .-. . .- -.. -.--
    </div>
  </Fade>
);

const Proof = () => (
  <Fade>
    <Label>REPRODUCIBLE EVIDENCE</Label>
    <Title size={78}>Built, connected, rejected when it should, and documented.</Title>
    <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 22, marginTop: 64}}>
      {[
        ['2', 'owned computers'],
        ['8 / 8', 'automated tests'],
        ['4', 'bounded signal words'],
        ['$0', 'added hardware cost'],
      ].map(([value, text]) => (
        <div key={text} style={{padding: 34, border: `2px solid ${C.line}`, borderRadius: 22, background: C.panel}}>
          <div style={{fontSize: 68, color: C.cyan, fontWeight: 900}}>{value}</div>
          <div style={{fontSize: 24, color: C.muted, marginTop: 18}}>{text}</div>
        </div>
      ))}
    </div>
    <div style={{display: 'flex', gap: 20, marginTop: 66, flexWrap: 'wrap'}}>
      <Pill>BAD SIGNATURE REJECTED</Pill><Pill color={C.amber}>STALE PACKET REJECTED</Pill><Pill color={C.red}>REPLAY REJECTED</Pill>
    </div>
  </Fade>
);

const Close = () => (
  <Fade accent={C.green}>
    <div style={{marginTop: 118}}>
      <Label>ELEMENT14 PROJECT14 / MAKE A CONNECTION</Label>
      <Title size={105}>Make the connection<br/><span style={{color: C.cyan}}>visible.</span></Title>
      <p style={{fontSize: 31, color: C.muted, lineHeight: 1.5, maxWidth: 1320}}>
        Standard-library Python. Original interface. Sanitized real-device evidence. Source, tests, BOM, and build steps included.
      </p>
    </div>
    <div style={{position: 'absolute', left: 88, right: 88, bottom: 74, display: 'flex', justifyContent: 'space-between'}}>
      <Pill>COMPLETE + FUNCTIONAL</Pill><Pill color={C.amber}>EDUCATIONAL / NOT LIFE-SAFETY</Pill>
    </div>
  </Fade>
);

export const LanternLinkDemo: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: C.bg}}>
    <Sequence from={0} durationInFrames={240}><Hook /></Sequence>
    <Sequence from={240} durationInFrames={300}><Architecture /></Sequence>
    <Sequence from={540} durationInFrames={360}><LiveResult /></Sequence>
    <Sequence from={900} durationInFrames={300}><Verification /></Sequence>
    <Sequence from={1200} durationInFrames={330}><Proof /></Sequence>
    <Sequence from={1530} durationInFrames={270}><Close /></Sequence>
  </AbsoluteFill>
);
