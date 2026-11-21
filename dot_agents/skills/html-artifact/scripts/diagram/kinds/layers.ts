import type { Kind } from './types';

export const layers: Kind = {
  check: () => ({ errors: ['kind "layers" is not implemented yet'], warns: [] }),
  ids: () => [],
  layout: () => { throw new Error('kind "layers" is not implemented yet'); },
};
