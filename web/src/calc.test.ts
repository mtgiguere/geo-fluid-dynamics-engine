// The budget calculator on the public receipt page. Pure arithmetic that was
// inline, untested JavaScript on the page; it now lives in public/calc.js
// (loaded by the page as a module) and is tested here.
import { describe, expect, it } from "vitest";

import { allocate } from "../public/calc.js";

const plan = {
  persuasion_share: 0.75,
  turnout_share: 0.25,
  persuade: [
    ["St. Charles", 3],
    ["Jefferson", 1],
  ] as [string, number][],
  turnout: [["St. Louis County", 1]] as [string, number][],
};

describe("allocate", () => {
  it("splits the budget by the registered shares and within each bucket by weight", () => {
    // Derivation: $1,000 at $10 per vote buys 100 votes. 75% persuasion =
    // $750, split 3:1 -> St. Charles $562.50, Jefferson $187.50; 25% turnout
    // = $250, one county gets all of it.
    const out = allocate(1000, 10, plan);
    expect(out.votes).toBe(100);
    expect(out.persuasion.total).toBe(750);
    expect(out.persuasion.rows).toEqual([
      { name: "St. Charles", dollars: 562.5 },
      { name: "Jefferson", dollars: 187.5 },
    ]);
    expect(out.turnout.total).toBe(250);
    expect(out.turnout.rows).toEqual([{ name: "St. Louis County", dollars: 250 }]);
  });

  it("clamps nonsense inputs: a negative budget allocates nothing, cost per vote floors at 1", () => {
    const nothing = allocate(-5, 10, plan);
    expect(nothing.votes).toBe(0);
    expect(nothing.persuasion.total).toBe(0);
    const cheap = allocate(100, 0, plan);
    expect(cheap.votes).toBe(100);
  });
});
