import { faker } from '@faker-js/faker';
import type { Lead } from '@/hooks/useLeads';

export function createLead(overrides: Partial<Lead> = {}): Lead {
  const domain = faker.internet.domainName();
  const firstName = faker.person.firstName();
  const lastName = faker.person.lastName();
  return {
    id: faker.number.int({ min: 1, max: 999999 }),
    first_name: firstName,
    last_name: lastName,
    company: faker.company.name(),
    domain,
    email_best: faker.internet.email({ firstName, lastName }).toLowerCase(),
    verification_status: faker.helpers.arrayElement(['valid', 'invalid', 'risky', 'unknown', 'pending']),
    confidence_score: faker.number.float({ min: 0, max: 1, fractionDigits: 2 }),
    mx_found: faker.datatype.boolean(),
    spf_present: faker.datatype.boolean(),
    dmarc_present: faker.datatype.boolean(),
    catch_all: faker.helpers.arrayElement([true, false, null]),
    smtp_check: faker.datatype.boolean(),
    smtp_attempted: faker.datatype.boolean(),
    smtp_blocked: faker.datatype.boolean(),
    provider: faker.company.name(),
    web_mentioned: faker.datatype.boolean(),
    signals: [],
    notes: '',
    last_job_status: faker.helpers.arrayElement(['completed', 'failed', 'running', null]),
    ...overrides,
  };
}
