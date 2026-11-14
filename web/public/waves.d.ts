export function levelAt(series: string, frame: number): number;
export const EMPTY: string;
export const FULL: string;
export function levelColor(level: number): string;
export function isFront(series: string, frame: number, mark: number): boolean;
export function markCurve(seriesList: string[], mark: number): number[];
export interface Box { x: number; y: number; width: number; height: number }
export function zoomBox(boxes: Box[], pad: number): Box;
export interface Topic {
  mark: number;
  series: Record<string, string>;
  handoffs: [string, string, number][];
  chance: Record<string, number>;
}
export function tally(topic: Topic, frame: number, inView: (fips: string) => boolean): { real: number; chance: number };
export function frameDelay(frames: number, zoomed: boolean, speed: number): number;
