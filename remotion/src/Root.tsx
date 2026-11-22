import React from 'react';
import {Composition} from 'remotion';
import {Title} from './Title';
import {Chart} from './Chart';
import {Footage} from './Footage';
import {Effects} from './Effects';

// The four benchmark scenes (see ../SPEC.md): 10 s at 30 fps each.
export const Root: React.FC = () => (
	<>
		<Composition id="title" component={Title} durationInFrames={300} fps={30} width={1080} height={1920} />
		<Composition id="chart" component={Chart} durationInFrames={300} fps={30} width={1920} height={1080} />
		<Composition id="footage" component={Footage} durationInFrames={300} fps={30} width={1080} height={1920} />
		<Composition id="effects" component={Effects} durationInFrames={300} fps={30} width={1920} height={1080} />
	</>
);
