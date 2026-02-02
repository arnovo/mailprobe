import { describe, it, expect } from 'vitest';

describe('sanity', () => {
  it('runs with jsdom and @/ alias', () => {
    expect(typeof window).toBe('object');
    expect(1 + 1).toBe(2);
  });
});
