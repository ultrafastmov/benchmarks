import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {evolvePath} from '@remotion/paths';
import {SANS, MONO} from './fonts';
import {inOutCubic, outCubic, tween} from './anim';

// (b) 1920x1080 animated bar chart with a target line drawn on, labels and counters.
const VALUES = [12, 18, 23, 31, 36, 44, 52, 57, 63, 71, 80, 92];
const TARGETS = [15, 20, 26, 30, 38, 42, 50, 58, 66, 72, 78, 88];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const X0 = 160;
const X1 = 1800;
const BASE = 900;
const PXU = 6;
const SLOT = (X1 - X0) / VALUES.length;
const cx = (i: number) => X0 + SLOT * (i + 0.5);

const POINTS = TARGETS.map((v, i) => [Math.round(cx(i) * 100) / 100, BASE - v * PXU]);
const LINE = 'M ' + POINTS.map(([x, y]) => `${x} ${y}`).join(' L ');

export const Chart: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;

	const axes = tween(t, 0.3, 1.0, 0, 1, outCubic);
	const legend = tween(t, 3.0, 3.5, 0, 1, outCubic);
	const line = evolvePath(tween(t, 3.0, 5.0, 0, 1, inOutCubic), LINE);
	const dots = tween(t, 5.0, 5.4, 0, 1, outCubic);

	return (
		<AbsoluteFill style={{background: '#0b1020', fontFamily: SANS}}>
			<div
				style={{
					position: 'absolute',
					left: 120,
					top: tween(t, 0, 0.6, 100, 80, outCubic),
					fontWeight: 700,
					fontSize: 60,
					color: '#ffffff',
					whiteSpace: 'pre',
					opacity: tween(t, 0, 0.6, 0, 1, outCubic),
				}}
			>
				Monthly active users, 2026
			</div>
			<div
				style={{
					position: 'absolute',
					left: 120,
					top: tween(t, 0.15, 0.75, 178, 158, outCubic),
					fontWeight: 400,
					fontSize: 30,
					color: '#94a3b8',
					whiteSpace: 'pre',
					opacity: tween(t, 0.15, 0.75, 0, 1, outCubic),
				}}
			>
				Millions, January to December
			</div>
			{[25, 50, 75, 100].map((v) => {
				const y = BASE - v * PXU;
				return (
					<React.Fragment key={v}>
						<div
							style={{
								position: 'absolute',
								left: X0,
								top: y - 1,
								width: (X1 - X0) * axes,
								height: 2,
								background: '#1e293b',
							}}
						/>
						<div
							style={{
								position: 'absolute',
								right: 1920 - 140,
								top: y,
								transform: 'translateY(-50%)',
								fontFamily: MONO,
								fontSize: 22,
								color: '#64748b',
								opacity: axes,
							}}
						>
							{v}
						</div>
					</React.Fragment>
				);
			})}
			<div
				style={{
					position: 'absolute',
					left: X0,
					top: BASE - 1.5,
					width: (X1 - X0) * axes,
					height: 3,
					background: '#475569',
				}}
			/>
			{VALUES.map((v, i) => {
				const t0 = 0.8 + 0.12 * i;
				const p = tween(t, t0, t0 + 0.8, 0, 1, outCubic);
				const h = v * PXU * p;
				return (
					<React.Fragment key={i}>
						<div
							style={{
								position: 'absolute',
								left: cx(i) - 42,
								top: BASE - h,
								width: 84,
								height: h,
								borderRadius: 6,
								background: i === VALUES.length - 1 ? '#f472b6' : '#38bdf8',
							}}
						/>
						<div
							style={{
								position: 'absolute',
								left: cx(i),
								bottom: 1080 - (BASE - h - 12),
								transform: 'translateX(-50%)',
								fontFamily: MONO,
								fontWeight: 600,
								fontSize: 26,
								color: '#ffffff',
								opacity: tween(t, t0, t0 + 0.2, 0, 1),
							}}
						>
							{Math.round(v * p)}
						</div>
						<div
							style={{
								position: 'absolute',
								left: cx(i),
								top: 920,
								transform: 'translateX(-50%)',
								fontWeight: 500,
								fontSize: 26,
								color: '#94a3b8',
								opacity: axes,
							}}
						>
							{MONTHS[i]}
						</div>
					</React.Fragment>
				);
			})}
			<svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0}}>
				<path
					d={LINE}
					fill="none"
					stroke="#fbbf24"
					strokeWidth={5}
					strokeLinejoin="round"
					strokeLinecap="round"
					strokeDasharray={line.strokeDasharray}
					strokeDashoffset={line.strokeDashoffset}
				/>
				{POINTS.map(([x, y], i) => (
					<circle key={i} cx={x} cy={y} r={8 * dots} fill="#fbbf24" />
				))}
			</svg>
			<div style={{position: 'absolute', left: 1460, top: 99, width: 22, height: 22, borderRadius: 3, background: '#38bdf8', opacity: legend}} />
			<div style={{position: 'absolute', left: 1494, top: 110, transform: 'translateY(-50%)', fontWeight: 500, fontSize: 26, color: '#cbd5e1', opacity: legend}}>
				Actual
			</div>
			<div style={{position: 'absolute', left: 1620, top: 107.5, width: 36, height: 5, borderRadius: 2.5, background: '#fbbf24', opacity: legend}} />
			<div style={{position: 'absolute', left: 1668, top: 110, transform: 'translateY(-50%)', fontWeight: 500, fontSize: 26, color: '#cbd5e1', opacity: legend}}>
				Target
			</div>
		</AbsoluteFill>
	);
};
