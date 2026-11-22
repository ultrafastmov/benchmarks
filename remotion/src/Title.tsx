import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {SANS, MONO} from './fonts';
import {inCubic, outCubic, tween} from './anim';

// (a) 1080x1920 social title card. Positions are the spec's: shapes by center,
// text by the top-left of its line box.
const text = (x: number, y: number): React.CSSProperties => ({
	position: 'absolute',
	left: x,
	top: y,
	whiteSpace: 'pre',
	lineHeight: 'normal',
});

export const Title: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;

	const sunX = tween(t, 0, 10, 760, 700);
	const sunY = tween(t, 0, 10, 560, 640);
	const sunScale = tween(t, 0, 0.9, 0, 1, outCubic);
	const tileX = tween(t, 0.3, 1.2, -360, 250, outCubic);
	const tileRot = tween(t, 0, 10, 8, 20);
	const ringOpacity = tween(t, 1.4, 2.0, 0, 0.9, outCubic);
	const ringScale = tween(t, 1.4, 2.0, 0.6, 1, outCubic);

	const barW = tween(t, 1.0, 1.5, 0, 160, outCubic);
	const fadeIn = (t0: number, t1: number) => tween(t, t0, t1, 0, 1, outCubic);
	const rise = (t0: number, t1: number, dy: number) => tween(t, t0, t1, dy, 0, outCubic);

	const copyOpacity = tween(t, 8.8, 9.6, 1, 0, inCubic);
	const copyY = tween(t, 8.8, 9.6, 0, -60, inCubic);

	return (
		<AbsoluteFill style={{background: 'linear-gradient(180deg, #1e1b4b, #be185d)'}}>
			<div
				style={{
					position: 'absolute',
					left: sunX - 320,
					top: sunY - 320,
					width: 640,
					height: 640,
					borderRadius: '50%',
					background: '#fbbf24',
					transform: `scale(${sunScale})`,
				}}
			/>
			<div
				style={{
					position: 'absolute',
					left: tileX - 260,
					top: 1700 - 260,
					width: 520,
					height: 520,
					borderRadius: 72,
					background: '#22d3ee',
					transform: `rotate(${tileRot}deg)`,
				}}
			/>
			<div
				style={{
					position: 'absolute',
					left: 250 - 110,
					top: 560 - 110,
					width: 220,
					height: 220,
					boxSizing: 'border-box',
					border: '10px solid #ffffff',
					borderRadius: '50%',
					opacity: ringOpacity,
					transform: `scale(${ringScale})`,
				}}
			/>
			<AbsoluteFill style={{opacity: copyOpacity, transform: `translateY(${copyY}px)`}}>
				<div
					style={{
						position: 'absolute',
						left: 120,
						top: 1000 - 7,
						width: barW,
						height: 14,
						borderRadius: 7,
						background: '#ffffff',
					}}
				/>
				<div
					style={{
						...text(120, 1030 + rise(0.8, 1.3, 30)),
						fontFamily: MONO,
						fontWeight: 500,
						fontSize: 40,
						letterSpacing: 6,
						color: 'rgba(255,255,255,0.8)',
						opacity: fadeIn(0.8, 1.3),
					}}
				>
					NEW DROP · 2026
				</div>
				<div
					style={{
						...text(120, 1090 + rise(1.0, 1.7, 80)),
						fontFamily: SANS,
						fontWeight: 800,
						fontSize: 190,
						color: '#ffffff',
						opacity: fadeIn(1.0, 1.7),
					}}
				>
					Make it
				</div>
				<div
					style={{
						...text(120, 1280 + rise(1.15, 1.85, 80)),
						fontFamily: SANS,
						fontWeight: 800,
						fontSize: 190,
						color: '#fbbf24',
						opacity: fadeIn(1.15, 1.85),
					}}
				>
					move.
				</div>
				<div
					style={{
						...text(120, 1500 + rise(2.0, 2.6, 20)),
						fontFamily: SANS,
						fontWeight: 500,
						fontSize: 52,
						color: 'rgba(255,255,255,0.85)',
						opacity: fadeIn(2.0, 2.6),
					}}
				>
					Ten seconds. One render.
				</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
