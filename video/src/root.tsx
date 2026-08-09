import React from 'react';
import {Composition} from 'remotion';
import {LanternLinkDemo} from './video';

export const Root: React.FC = () => (
  <Composition
    id="LanternLinkDemo"
    component={LanternLinkDemo}
    durationInFrames={1800}
    fps={30}
    width={1920}
    height={1080}
  />
);
