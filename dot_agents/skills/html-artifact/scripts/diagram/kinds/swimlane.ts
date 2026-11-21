import type { Kind } from './types';

export const swimlane: Kind = {
  check: () => ({ errors: ['kind "swimlane" is not implemented yet'], warns: [] }),
  ids: () => [],
  layout: () => { throw new Error('kind "swimlane" is not implemented yet'); },
};
