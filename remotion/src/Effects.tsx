import React from 'react';
import {AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig} from 'remotion';
import {CameraMotionBlur} from '@remotion/motion-blur';
import {SANS, MONO} from './fonts';
import {inOutCubic, inOutSine, outCubic, tween} from './anim';

// (d) 1920x1080 "GPU looks": blurred colour fields, a glowing title, a fast
// motion-blurred whip, film grain and a vignette, done the usual web way:
// CSS filter: blur(), text-shadow, @remotion/motion-blur and a tiled noise texture.

const there = (t: number, a: [number, number], b: [number, number]) => {
	const p = t <= 5 ? tween(t, 0, 5, 0, 1, inOutSine) : tween(t, 5, 10, 1, 0, inOutSine);
	return [a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p];
};

const BLOBS: {color: string; a: [number, number]; b: [number, number]}[] = [
	{color: '#7c3aed', a: [600, 420], b: [1000, 640]},
	{color: '#06b6d4', a: [1340, 380], b: [980, 560]},
	{color: '#f43f5e', a: [900, 800], b: [720, 520]},
];

// The same 256 px fractal-noise tile the HyperFrames grain-overlay block uses,
// shifted to one of ten offsets every 0.05 s (that block's keyframes).
const NOISE =
	"url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E\")";
const GRAIN_STEPS = [
	[0, 0], [-5, -5], [-10, 5], [5, -10], [-5, 15], [-10, 5], [15, 0], [0, 10], [-15, 0], [10, 5],
];

const Whip: React.FC<{from: number; to: number}> = ({from, to}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const x = tween(frame / fps, 0, 0.6, from, to, inOutCubic);
	return (
		<div
			style={{
				position: 'absolute',
				left: x - 180,
				top: 860 - 14,
				width: 360,
				height: 28,
				borderRadius: 14,
				background: '#ffffff',
			}}
		/>
	);
};

export const Effects: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;
	const titleIn = tween(t, 0.5, 1.5, 0, 1, outCubic);
	const grain = GRAIN_STEPS[Math.floor((t % 0.5) / 0.05)];
	return (
		<AbsoluteFill style={{background: '#07060d', overflow: 'hidden'}}>
			{BLOBS.map(({color, a, b}, i) => {
				const [x, y] = there(t, a, b);
				return (
					<div
						key={i}
						style={{
							position: 'absolute',
							left: x - 280,
							top: y - 280,
							width: 560,
							height: 560,
							borderRadius: '50%',
							background: color,
							filter: 'blur(80px)',
						}}
					/>
				);
			})}
			<div
				style={{
					position: 'absolute',
					left: 0,
					width: 1920,
					top: 540,
					textAlign: 'center',
					fontFamily: SANS,
					fontWeight: 900,
					fontSize: 260,
					lineHeight: 'normal',
					color: '#ffffff',
					textShadow: '0 0 48px rgba(255,255,255,0.9)',
					opacity: titleIn,
					transform: `translateY(-50%) scale(${0.9 + 0.1 * titleIn})`,
				}}
			>
				GLOW
			</div>
			<div
				style={{
					position: 'absolute',
					left: 0,
					width: 1920,
					top: 720,
					textAlign: 'center',
					fontFamily: MONO,
					fontWeight: 500,
					fontSize: 32,
					letterSpacing: 8,
					color: '#c4b5fd',
					opacity: tween(t, 1.2, 1.8, 0, 1, outCubic),
				}}
			>
				GPU EFFECTS TEST
			</div>
			<Sequence from={30} durationInFrames={18} layout="none">
				<CameraMotionBlur shutterAngle={180}>
					<Whip from={-300} to={2220} />
				</CameraMotionBlur>
			</Sequence>
			<Sequence from={180} durationInFrames={18} layout="none">
				<CameraMotionBlur shutterAngle={180}>
					<Whip from={2220} to={-300} />
				</CameraMotionBlur>
			</Sequence>
			<AbsoluteFill
				style={{
					background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,0.69) 100%)',
				}}
			/>
			<AbsoluteFill style={{overflow: 'hidden'}}>
				<div
					style={{
						position: 'absolute',
						top: '-50%',
						left: '-50%',
						width: '200%',
						height: '200%',
						background: NOISE,
						opacity: 0.15,
						transform: `translate(${grain[0]}%, ${grain[1]}%)`,
					}}
				/>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
