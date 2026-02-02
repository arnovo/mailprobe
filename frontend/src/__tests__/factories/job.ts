import { faker } from '@faker-js/faker';
import type { Job } from '@/hooks/useJobs';

export function createJob(overrides: Partial<Job> = {}): Job {
  return {
    job_id: faker.string.uuid(),
    kind: faker.helpers.arrayElement(['verify', 'import', 'export']),
    status: faker.helpers.arrayElement(['pending', 'running', 'completed', 'failed', 'cancelled']),
    progress: faker.number.int({ min: 0, max: 100 }),
    lead_id: faker.helpers.arrayElement([faker.number.int({ min: 1, max: 999999 }), null]),
    created_at: faker.date.past().toISOString(),
    ...overrides,
  };
}
