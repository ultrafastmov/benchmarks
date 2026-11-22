import {Easing, interpolate} from 'remotion';

// Times are in seconds, like the spec; `t` is frame / fps.
export const outCubic = Easing.out(Easing.cubic);
export const inCubic = Easing.in(Easing.cubic);
export const inOutCubic = Easing.inOut(Easing.cubic);
export const inOutSine = Easing.inOut(Easing.sin);

export const tween = (
	t: number,
	t0: number,
	t1: number,
	from: number,
	to: number,
	easing: (x: number) => number = (x) => x,
) =>
	interpolate(t, [t0, t1], [from, to], {
		easing,
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
