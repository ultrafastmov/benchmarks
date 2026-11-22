import { WordHighlightCaptions } from "./word-highlight-captions.element";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  Composition,
  Easing,
  Interactive,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Video } from "@remotion/media";
import { colorCorrection } from "@remotion/effects/color-correction";
import { noise } from "@remotion/effects/noise";
import { loadFont } from "@remotion/google-fonts/Inter";

const { fontFamily } = loadFont("normal", {
  weights: ["400", "700"],
  subsets: ["latin"],
});

type Props = {};

const calculateMetadata: CalculateMetadataFunction<Props> = () => {
  return {};
};

export const MyComposition = () => {
  return (
    <Composition
      id="MyComp"
      component={MyComponent}
      durationInFrames={300}
      fps={30}
      width={1080}
      height={1920}
      calculateMetadata={calculateMetadata}
    />
  );
};

const Footage: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <Video
      name="Footage"
      src={staticFile("footage.mp4")}
      objectFit="cover"
      style={{ width: "100%", height: "100%" }}
      effects={[
        colorCorrection({ exposure: -0.2, contrast: 1.15, saturation: 0.85 }),
        noise({ amount: 0.055, seed: frame }),
      ]}
    />
  );
};

const Copy: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ fontFamily, color: "white", padding: "300px 120px" }}>
      <Interactive.Div
        name="Title"
        style={{
          fontSize: 120,
          fontWeight: 700,
          letterSpacing: -3,
          lineHeight: 1.2,
          opacity: interpolate(frame, [0.3 * fps, 0.9 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          translate: interpolate(frame, [0.3 * fps, 1.1 * fps], ["0px 80px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        Life in orbit
      </Interactive.Div>
      <Interactive.Div
        name="Line 1"
        style={{
          fontSize: 46,
          lineHeight: 1.4,
          marginTop: 12,
          color: "rgba(255, 255, 255, 0.85)",
          opacity: interpolate(frame, [1 * fps, 1.6 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          translate: interpolate(frame, [1 * fps, 1.6 * fps], ["0px 30px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        408 km above the surface
      </Interactive.Div>
      <Interactive.Div
        name="Line 2"
        style={{
          fontSize: 46,
          lineHeight: 1.4,
          color: "rgba(255, 255, 255, 0.85)",
          opacity: interpolate(frame, [1.2 * fps, 1.8 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          translate: interpolate(frame, [1.2 * fps, 1.8 * fps], ["0px 30px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        28,000 km per hour
      </Interactive.Div>
      <Interactive.Div
        name="Line 3"
        style={{
          fontSize: 46,
          lineHeight: 1.4,
          color: "rgba(255, 255, 255, 0.85)",
          opacity: interpolate(frame, [1.4 * fps, 2 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          translate: interpolate(frame, [1.4 * fps, 2 * fps], ["0px 30px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        Seven crew on board
      </Interactive.Div>
    </AbsoluteFill>
  );
};

export const MyComponent: React.FC<Props> = () => {
  return (
    <AbsoluteFill>
      <Footage />
      <Copy />
      <WordHighlightCaptions
        captions={[
          { text: "Every", startMs: 3000, endMs: 3300, timestampMs: null, confidence: null },
          { text: " ninety", startMs: 3300, endMs: 3700, timestampMs: null, confidence: null },
          { text: " minutes,", startMs: 3700, endMs: 4200, timestampMs: null, confidence: null },
          { text: " the", startMs: 4400, endMs: 4550, timestampMs: null, confidence: null },
          { text: " station", startMs: 4550, endMs: 5000, timestampMs: null, confidence: null },
          { text: " circles", startMs: 5000, endMs: 5450, timestampMs: null, confidence: null },
          { text: " the", startMs: 5450, endMs: 5600, timestampMs: null, confidence: null },
          { text: " whole", startMs: 5600, endMs: 5950, timestampMs: null, confidence: null },
          { text: " planet", startMs: 5950, endMs: 6400, timestampMs: null, confidence: null },
          { text: " once.", startMs: 6400, endMs: 6900, timestampMs: null, confidence: null },
          { text: " Sixteen", startMs: 7300, endMs: 7750, timestampMs: null, confidence: null },
          { text: " sunrises,", startMs: 7750, endMs: 8300, timestampMs: null, confidence: null },
          { text: " every", startMs: 8450, endMs: 8750, timestampMs: null, confidence: null },
          { text: " single", startMs: 8750, endMs: 9100, timestampMs: null, confidence: null },
          { text: " day.", startMs: 9100, endMs: 9600, timestampMs: null, confidence: null },
        ]}
        combineTokensWithinMilliseconds={800}
        width={840}
        durationInFrames={300}
        name="Captions"
        from={0}
        style={{ position: "absolute", top: 1080, translate: "120px 0px" }}
      />
    </AbsoluteFill>
  );
};
