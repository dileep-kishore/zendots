import type { Measure, SItem } from '../scene';

/** A diagram kind: validation that names the bad field, and a layout that returns scene items in any origin. */
export interface Kind {
  /** Errors stop the export; warnings print and the drawing is still written. */
  check(g: any): { errors: string[]; warns: string[] };
  /** Ids a note may target, for validation before layout. */
  ids(g: any): string[];
  layout(g: any, m: Measure): SItem[];
}
export const isText = (v: unknown): v is string => typeof v === 'string' && v.trim().length > 0;
export const TONES = new Set(['ink', 'blue', 'green', 'teal', 'peach', 'yellow', 'red', 'accent']);
