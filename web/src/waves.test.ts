// The wave player's frame logic (public/waves.js): which colour each county
// is at a given frame. Pure logic, so it is tested here, not left inline on
// the page (rule 7). The Python side (geofluid.map.waves) ships one string
// per county, one character per frame: "0"-"9" = 0-90% of the county's own
// final total so far, "A" = all of it.
import { describe, expect, it } from "vitest";

import { EMPTY, FULL, isFront, levelAt, levelColor, markCurve } from "../public/waves.js";

describe("levelAt", () => {
  it("reads the county's level at a frame from its string", () => {
    // Derivation: "114A" is 10%, 10%, 40%, 100% -> 1, 1, 4, 10.
    expect([0, 1, 2, 3].map((f) => levelAt("114A", f))).toEqual([1, 1, 4, 10]);
  });
});

describe("levelColor", () => {
  it("runs from EMPTY (nothing yet) to FULL (all of it), evenly by channel", () => {
    // Derivation: EMPTY #ece8df = (236, 232, 223), FULL #0b5563 = (11, 85, 99).
    // Level 5 is halfway: (123.5, 158.5, 161) -> rounded (124, 159, 161) = #7c9fa1.
    expect(EMPTY).toBe("#ece8df");
    expect(FULL).toBe("#0b5563");
    expect(levelColor(0)).toBe(EMPTY);
    expect(levelColor(10)).toBe(FULL);
    expect(levelColor(5)).toBe("#7c9fa1");
  });
});

describe("isFront", () => {
  it("flags the frame a county crosses the topic's mark (the take-off rule)", () => {
    // Derivation: "0247A" is 0, 20, 40, 70, 100%. Mark 5 (50%): crossed at
    // frame 3 only. Mark 2 (20%): crossed at frame 1 only.
    expect([0, 1, 2, 3, 4].map((f) => isFront("0247A", f, 5))).toEqual([false, false, false, true, false]);
    expect([0, 1, 2, 3, 4].map((f) => isFront("0247A", f, 2))).toEqual([false, true, false, false, false]);
  });

  it("flags frame 0 when a county is already past the mark (arrived at once)", () => {
    // Derivation: "6AAA": 60% in the first frame, nothing before it to cross from.
    expect(isFront("6AAA", 0, 5)).toBe(true);
  });
});

describe("markCurve", () => {
  it("gives, per frame, the share of counties at or past the mark (an S-curve for a wave, a cliff for a broadcast)", () => {
    // Derivation: three counties, three frames, mark 5 (50%).
    //   "05A": 0, 50, 100%   -> at or past the mark at frames 1, 2
    //   "16A": 10, 60, 100%  -> frames 1, 2
    //   "AAA": 100% from the start -> frames 0, 1, 2
    // Frame 0: 1 of 3; frames 1 and 2: 3 of 3. At mark 1 (10%), "16A" is
    // past it from frame 0 too: 2 of 3, then 3 of 3.
    expect(markCurve(["05A", "16A", "AAA"], 5)).toEqual([1 / 3, 1, 1]);
    expect(markCurve(["05A", "16A", "AAA"], 1)).toEqual([2 / 3, 1, 1]);
  });
});
