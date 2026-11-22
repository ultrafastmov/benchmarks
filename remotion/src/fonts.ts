import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';

// The same font files every tool uses (assets/fonts, SIL OFL). loadFont holds the
// render until the faces are ready.
export const SANS = 'Geist';
export const MONO = 'Geist Mono';

loadFont({family: SANS, url: staticFile('fonts/Geist-VF.ttf'), weight: '100 900', format: 'truetype'});
loadFont({family: MONO, url: staticFile('fonts/GeistMono-VF.ttf'), weight: '100 900', format: 'truetype'});
