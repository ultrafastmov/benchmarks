import { WordHighlightCaptions } from "./word-highlight-captions.element";
import { CalculateMetadataFunction, Composition } from "remotion";

type Props = {};

const calculateMetadata: CalculateMetadataFunction<Props> = () => {
  return {};
};

export const MyComposition = () => {
  return (
    <Composition
      id="MyComp"
      component={MyComponent}
      durationInFrames={60}
      fps={30}
      width={1280}
      height={720}
      calculateMetadata={calculateMetadata}
    />
  );
};

export const MyComponent: React.FC<Props> = () => {
  return (
    <>
      <WordHighlightCaptions
        captions={[{
          text: "Captions",
          startMs: 0,
          endMs: 800,
          timestampMs: 400,
          confidence: null
        }, {
          text: " can",
          startMs: 800,
          endMs: 1500,
          timestampMs: 1150,
          confidence: null
        }, {
          text: " move",
          startMs: 1500,
          endMs: 2300,
          timestampMs: 1900,
          confidence: null
        }, {
          text: " with",
          startMs: 2300,
          endMs: 3100,
          timestampMs: 2700,
          confidence: null
        }, {
          text: " every",
          startMs: 3100,
          endMs: 4000,
          timestampMs: 3550,
          confidence: null
        }, {
          text: " spoken",
          startMs: 4000,
          endMs: 5100,
          timestampMs: 4550,
          confidence: null
        }, {
          text: " word.",
          startMs: 5100,
          endMs: 6500,
          timestampMs: 5800,
          confidence: null
        }]}
        combineTokensWithinMilliseconds={800}
        width={682}
        durationInFrames={210}
        name="Word Highlight Captions"
        from={0}
        style={{ position: "absolute" }}
      />
    </>
  );
};
