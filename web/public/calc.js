// The receipt page's budget calculator: pure arithmetic, loaded by the page
// as a module and unit-tested in src/calc.test.ts. Dollars follow the
// registered persuasion/turnout split, then within each bucket follow the
// county weights (votes per point) the page embeds.
export function allocate(budget, costPerVote, plan) {
  const b = Math.max(0, Number(budget) || 0);
  const cpv = Math.max(1, Number(costPerVote) || 1);
  const bucket = (share, rows) => {
    const total = b * share;
    const weight = rows.reduce((a, r) => a + r[1], 0);
    return {
      total,
      rows: rows.map((r) => ({ name: r[0], dollars: weight ? (total * r[1]) / weight : 0 })),
    };
  };
  return {
    votes: b / cpv,
    persuasion: bucket(plan.persuasion_share, plan.persuade),
    turnout: bucket(plan.turnout_share, plan.turnout),
  };
}
