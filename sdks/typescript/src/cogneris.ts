import { createClient } from './client';
import {
  cancelDocumentJob,
  extractDocument,
  getDocumentJob,
  submitDocumentJob,
} from './sdk.gen';
import type {
  DocumentJob,
  DocumentJobCancellation,
  DocumentJobOperation,
  DocumentJobSubmission,
  Envelope,
} from './types.gen';

export const COGNERIS_REGION_URLS = {
  us: 'https://api-us.cogneris.ai',
  eu: 'https://api-eu.cogneris.ai',
} as const;

export type CognerisRegion = keyof typeof COGNERIS_REGION_URLS;

export function cognerisBaseUrl(region: CognerisRegion): string {
  if (!Object.hasOwn(COGNERIS_REGION_URLS, region)) {
    throw new TypeError('region must be either "us" or "eu".');
  }
  return COGNERIS_REGION_URLS[region];
}

export class CognerisError extends Error {
  constructor(message: string) {
    super(message);
    this.name = new.target.name;
  }
}

export class CognerisApiError extends CognerisError {
  readonly status?: number;
  readonly retryable?: boolean;

  constructor(message: string, options: { status?: number; retryable?: boolean } = {}) {
    super(message);
    this.status = options.status;
    this.retryable = options.retryable;
  }
}

export class CognerisJobTerminalError extends CognerisError {
  readonly status: 'Failed' | 'Cancelled';
  readonly retryable?: boolean;

  constructor(job: DocumentJob) {
    const status = job.status === 'Cancelled' ? 'Cancelled' : 'Failed';
    super(`Document job reached terminal status ${status}.`);
    this.status = status;
    this.retryable = typeof job.retryable === 'boolean' ? job.retryable : undefined;
  }
}

export class CognerisMaxAttemptsError extends CognerisError {
  readonly attempts: number;

  constructor(attempts: number) {
    super(`Document job did not reach a terminal state after ${attempts} attempts.`);
    this.attempts = attempts;
  }
}

export type CognerisClientOptions = {
  apiKey: string;
  region?: CognerisRegion;
  /** Test-only loopback transport seam. Do not use in production applications. */
  _baseUrlForTesting?: string;
};

export type ExtractOptions = {
  fileName?: string;
  complementaryPrompt?: string;
};

export type WaitForJobOptions = {
  maxAttempts?: number;
  pollIntervalSeconds?: number;
};

type GeneratedResult<T> = {
  data?: T;
  error?: unknown;
  response?: Response;
};

function problemField(error: unknown, field: 'retryable'): unknown {
  if (typeof error !== 'object' || error === null) return undefined;
  return (error as Record<string, unknown>)[field];
}

function apiError(error: unknown, response?: Response): CognerisApiError {
  const status = response?.status;
  const retryable = problemField(error, 'retryable');
  const message = status === undefined
    ? 'Cogneris API request failed.'
    : `Cogneris API request failed with HTTP ${status}.`;
  return new CognerisApiError(message, {
    status,
    retryable: typeof retryable === 'boolean' ? retryable : undefined,
  });
}

function loopbackBaseUrl(value: string): string {
  const parsed = new URL(value);
  if (!['127.0.0.1', '::1', '[::1]', 'localhost'].includes(parsed.hostname)) {
    throw new TypeError('_baseUrlForTesting accepts loopback hosts only.');
  }
  return value.replace(/\/$/, '');
}

function parseRetryAfter(response: Response | undefined, fallback: number): number {
  const raw = response?.headers.get('Retry-After');
  if (raw === null || raw === undefined || raw.trim() === '') return fallback;
  const seconds = Number(raw);
  return Number.isInteger(seconds) && seconds >= 0 ? seconds : fallback;
}

function submissionRetryAfter(
  submission: DocumentJobSubmission,
  response: Response | undefined,
): number | undefined {
  const headerValue = response?.headers.get('Retry-After');
  if (headerValue !== null && headerValue !== undefined && headerValue.trim() !== '') {
    const seconds = Number(headerValue);
    if (Number.isInteger(seconds) && seconds >= 0) return seconds;
  }
  const seconds = submission.retryAfterSeconds;
  return typeof seconds === 'number' && Number.isInteger(seconds) && seconds >= 0
    ? seconds
    : undefined;
}

async function requireData<T>(result: GeneratedResult<T>): Promise<T> {
  if (result.data !== undefined) return result.data;
  throw apiError(result.error, result.response);
}

async function requireEnvelopeData<T>(
  result: GeneratedResult<{ data: T }>,
): Promise<T> {
  const envelope = await requireData(result);
  return envelope.data;
}

export class CognerisClient {
  readonly region: CognerisRegion;
  private readonly generatedClient;
  private readonly initialRetryHints = new Map<string, number>();

  constructor(options: CognerisClientOptions) {
    if (!options.apiKey || !options.apiKey.trim()) {
      throw new TypeError('apiKey must be a non-empty string.');
    }
    const region = options.region ?? 'us';
    const regionBaseUrl = cognerisBaseUrl(region);
    this.region = region;
    const baseUrl = options._baseUrlForTesting
      ? loopbackBaseUrl(options._baseUrlForTesting)
      : regionBaseUrl;
    this.generatedClient = createClient({ auth: options.apiKey, baseUrl });
  }

  async extract(file: Blob | File, options: ExtractOptions = {}): Promise<Envelope> {
    const upload = options.fileName && !(file instanceof File)
      ? new File([file], options.fileName, { type: file.type })
      : file;
    const result = await extractDocument({
      body: {
        file: upload,
        ...(options.complementaryPrompt === undefined
          ? {}
          : { ComplementaryPrompt: options.complementaryPrompt }),
      },
      client: this.generatedClient,
    });
    return requireData(result);
  }

  async submitJob(
    operation: DocumentJobOperation,
    inputReference: string,
  ): Promise<DocumentJobSubmission> {
    const result = await submitDocumentJob({
      body: { operation, inputReference },
      client: this.generatedClient,
    });
    const submission = await requireEnvelopeData<DocumentJobSubmission>(result);
    const hint = submissionRetryAfter(submission, result.response);
    if (typeof submission.jobId === 'string' && hint !== undefined) {
      this.initialRetryHints.set(submission.jobId, hint);
    }
    return submission;
  }

  async getJob(jobId: string): Promise<DocumentJob> {
    const result = await this.getJobDetailed(jobId);
    return requireEnvelopeData<DocumentJob>(result);
  }

  async waitForJob(jobId: string, options: WaitForJobOptions = {}): Promise<DocumentJob> {
    const maxAttempts = options.maxAttempts ?? 20;
    const pollIntervalSeconds = options.pollIntervalSeconds ?? 1;
    if (!Number.isInteger(maxAttempts) || maxAttempts < 1) {
      throw new TypeError('maxAttempts must be a positive integer.');
    }
    if (!Number.isFinite(pollIntervalSeconds) || pollIntervalSeconds < 0) {
      throw new TypeError('pollIntervalSeconds must be a non-negative number.');
    }

    const initialRetryHint = this.initialRetryHints.get(jobId);
    this.initialRetryHints.delete(jobId);
    if (initialRetryHint !== undefined) {
      await new Promise((resolve) => setTimeout(resolve, initialRetryHint * 1_000));
    }

    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      const result = await this.getJobDetailed(jobId);
      const job = await requireEnvelopeData<DocumentJob>(result);
      if (job.status === 'Succeeded') return job;
      if (job.status === 'Failed' || job.status === 'Cancelled') {
        throw new CognerisJobTerminalError(job);
      }
      if (attempt < maxAttempts) {
        const delaySeconds = parseRetryAfter(result.response, pollIntervalSeconds);
        await new Promise((resolve) => setTimeout(resolve, delaySeconds * 1_000));
      }
    }
    throw new CognerisMaxAttemptsError(maxAttempts);
  }

  async cancelJob(jobId: string): Promise<DocumentJobCancellation> {
    const result = await cancelDocumentJob({
      path: { jobId },
      client: this.generatedClient,
    });
    return requireEnvelopeData<DocumentJobCancellation>(result);
  }

  private getJobDetailed(jobId: string) {
    return getDocumentJob({
      path: { jobId },
      client: this.generatedClient,
    });
  }
}
