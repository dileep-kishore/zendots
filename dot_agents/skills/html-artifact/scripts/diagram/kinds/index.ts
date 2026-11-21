import { layers } from './layers';
import { quadrant } from './quadrant';
import { sequence } from './sequence';
import { swimlane } from './swimlane';
import type { Kind } from './types';

export const KINDS: Record<string, Kind> = { sequence, swimlane, layers, quadrant };
