import React from 'react';
import {AbsoluteFill, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Video} from '@remotion/media';
import {SANS, MONO} from './fonts';
import {outCubic, tween} from './anim';

// (c) 1080x1920 composite over a NASA clip (assets/footage/PROVENANCE.md) with
// word-timed karaoke captions, one page per phrase.
type Word = [number, number, string];
const PAGES: Word[][] = [
	[[0.4, 0.7, 'Day'], [0.7, 1.1, 'twenty'], [1.1, 1.3, 'of'], [1.3, 1.9, 'Artemis'], [1.9, 2.8, 'I.']],
	[[2.8, 3.3, 'Orion'], [3.3, 3.75, 'closes'], [3.75, 3.95, 'in'], [3.95, 4.15, 'on'], [4.15, 4.35, 'the'], [4.35, 5.4, 'Moon']],
	[[5.4, 5.75, 'ahead'], [5.75, 5.9, 'of'], [5.9, 6.1, 'its'], [6.1, 6.55, 'return'], [6.55, 7.05, 'flyby'], [7.05, 7.9, 'burn.']],
	[[7.9, 8.6, 'Splashdown'], [8.6, 8.8, 'is'], [8.8, 9.3, 'December'], [9.3, 10.0, '11.']],
];

const CaptionPage: React.FC<{words: Word[]; offset: number}> = ({words, offset}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = offset + frame / fps; // composition time
	return (
		<div
			style={{
				position: 'absolute',
				left: 100,
				width: 880,
				top: 1450,
				transform: 'translateY(-50%)',
				textAlign: 'center',
				fontFamily: SANS,
				fontWeight: 800,
				fontSize: 72,
				lineHeight: 1.18,
				color: '#ffffff',
			}}
		>
			{words.map(([a, b, w], i) => (
				<React.Fragment key={i}>
					<span style={{color: t >= a && t < b ? '#ffd23f' : '#ffffff'}}>{w}</span>
					{i < words.length - 1 ? ' ' : null}
				</React.Fragment>
			))}
		</div>
	);
};

export const Footage: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;
	return (
		<AbsoluteFill style={{background: '#000000'}}>
			<AbsoluteFill style={{transform: `scale(${tween(t, 0, 10, 1, 1.08)})`}}>
				<Video src={staticFile('footage/orion_moon_fd20.mp4')} muted objectFit="cover" style={{width: 1080, height: 1920}} />
			</AbsoluteFill>
			<div
				style={{
					position: 'absolute',
					left: 0,
					top: 1100,
					width: 1080,
					height: 820,
					background: 'linear-gradient(180deg, rgba(0,0,0,0), rgba(0,0,0,0.8))',
				}}
			/>
			<div
				style={{
					position: 'absolute',
					left: 0,
					width: 1080,
					top: 140,
					textAlign: 'center',
					fontFamily: MONO,
					fontWeight: 500,
					fontSize: 30,
					letterSpacing: 4,
					color: 'rgba(255,255,255,0.85)',
					opacity: tween(t, 0.2, 0.8, 0, 1, outCubic),
				}}
			>
				NASA · ARTEMIS I · FLIGHT DAY 20
			</div>
			{PAGES.map((words, p) => {
				const start = Math.round(words[0][0] * fps);
				const end = p + 1 < PAGES.length ? Math.round(PAGES[p + 1][0][0] * fps) : 10 * fps;
				return (
					<Sequence key={p} from={start} durationInFrames={end - start} layout="none">
						<CaptionPage words={words} offset={start / fps} />
					</Sequence>
				);
			})}
		</AbsoluteFill>
	);
};
