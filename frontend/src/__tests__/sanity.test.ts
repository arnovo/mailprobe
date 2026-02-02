import { describe, it, expect } from 'vitest';
import { createLead } from '@/__tests__/factories/lead';
import { createJob } from '@/__tests__/factories/job';

const TEST_LEAD_OVERRIDE_ID = 42;

describe('sanity', () => {
  it('runs with jsdom and @/ alias', () => {
    expect(typeof window).toBe('object');
    expect(1 + 1).toBe(2);
  });

  it('factories return Lead and Job shapes', () => {
    const lead = createLead();
    expect(lead).toHaveProperty('id');
    expect(lead).toHaveProperty('email_best');
    expect(lead).toHaveProperty('verification_status');

    const job = createJob();
    expect(job).toHaveProperty('job_id');
    expect(job).toHaveProperty('status');
    expect(job).toHaveProperty('kind');

    const leadOverride = createLead({ id: TEST_LEAD_OVERRIDE_ID });
    expect(leadOverride.id).toBe(TEST_LEAD_OVERRIDE_ID);
  });
});
