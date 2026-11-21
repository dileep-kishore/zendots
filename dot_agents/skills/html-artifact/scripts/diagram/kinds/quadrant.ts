import type { Kind } from './types';

export const quadrant: Kind = {
  check: () => ({ errors: ['kind "quadrant" is not implemented yet'], warns: [] }),
  ids: () => [],
  layout: () => { throw new Error('kind "quadrant" is not implemented yet'); },
};
