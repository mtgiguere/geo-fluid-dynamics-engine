export interface Plan {
  persuasion_share: number;
  turnout_share: number;
  persuade: [string, number][];
  turnout: [string, number][];
}
export interface Bucket {
  total: number;
  rows: { name: string; dollars: number }[];
}
export function allocate(
  budget: number,
  costPerVote: number,
  plan: Plan,
): { votes: number; persuasion: Bucket; turnout: Bucket };
