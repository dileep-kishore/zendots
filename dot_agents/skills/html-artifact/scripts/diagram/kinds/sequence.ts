import type { Kind } from './types';

export const sequence: Kind = {
  check: () => ({ errors: ['kind "sequence" is not implemented yet'], warns: [] }),
  ids: () => [],
  layout: () => { throw new Error('kind "sequence" is not implemented yet'); },
};
