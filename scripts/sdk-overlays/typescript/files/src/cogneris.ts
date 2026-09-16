import { createClient } from './client';
import {
  cancelDocumentJob,
  extractDocument,
  getDocumentJob,
  submitDocumentJob,
} from './sdk.gen';
import type {
  DocumentJob,
  DocumentJobOperation,
  Envelope,
  SubmitDocumentJobResponse,
} from './types.gen';

export const COGNERIS_REGION_URLS = {
  us: 'https://api-us.cogneris.ai',
  eu: 'https://api-eu.cogneris.ai',
} as const;

export type CognerisRegion = keyof typeof COGNERIS_REGION_URLS;

export function cognerisBaseUrl(region: CognerisRegion): string {
  if (!(region in COGNERIS_REGION_URLS)) {
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
  readonly code?: string;
  readonly retryable?: boolean;

  constructor(message: string, options: { status?: number; code?: string; retryable?: boolean } = {}) {
    super(message);
    this.status = options.status;
    this.code = options.code;
    this.retryable = options.retryable;
  }
}

export class CognerisJobTerminalError extends CognerisError {
  readonly job: DocumentJob;
  readonly failureCode?: string;

  constructor(job: DocumentJob) {
    const status = job.status ?? 'unknown';
    const failure = job.failureCode ? ` (${job.failureCode})` : '';
    super(`Document job reached terminal status ${status}${failure}.`);
    this.job = job;
    this.failureCode = job.failureCode ?? undefined;
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

function problemField(error: unknown, field: 'code' | 'title' | 'retryable'): unknown {
  if (typeof error !== 'object' || error === null) return undefined;
  return (error as Record<string, unknown>)[field];
}

function apiError(error: unknown, response?: Response): CognerisApiError {
  const status = response?.status;
  const code = problemField(error, 'code');
  const title = problemField(error, 'title');
  const retryable = problemField(error, 'retryable');
  const label = typeof title === 'string'
    ? title
    : typeof code === 'string'
      ? code
      : status
        ? `HTTP ${status}`
        : 'request failed';
  return new CognerisApiError(`Cogneris API request failed: ${label}.`, {
    status,
    code: typeof code === 'string' ? code : undefined,
    retryable: typeof retryable === 'boolean' ? retryable : undefined,
  });
}

function loopbackBaseUrl(value: string): string {
  const parsed = new URL(value);
  if (!['127.0.0.1', '::1', 'localhost'].includes(parsed.hostname)) {
    throw new TypeError('_baseUrlForTesting accepts loopback hosts only.');
  }
  return value.replace(/\/$/, '');
}

function parseRetryAfter(response: Response | undefined, fallback: number): number {
  const raw = response?.headers.get('Retry-After');
  if (raw === null || raw === undefined || raw.trim() === '') return fallback;
  const seconds = Number(raw);
  return Number.isFinite(seconds) && seconds >= 0 ? seconds : fallback;
}

async function requireData<T>(result: GeneratedResult<T>): Promise<T> {
  if (result.data !== undefined) return result.data;
  throw apiError(result.error, result.response);
}

export class CognerisClient {
  readonly region: CognerisRegion;
  private readonly generatedClient;

  constructor(options: CognerisClientOptions) {
    if (!options.apiKey || !options.apiKey.trim()) {
      throw new TypeError('apiKey must be a non-empty string.');
    }
    const region = options.region ?? 'us';
    this.region = region;
    const baseUrl = options._baseUrlForTesting
      ? loopbackBaseUrl(options._baseUrlForTesting)
      : cognerisBaseUrl(region);
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
  ): Promise<SubmitDocumentJobResponse> {
    const result = await submitDocumentJob({
      body: { operation, inputReference },
      client: this.generatedClient,
    });
    return requireData(result);
  }

  async getJob(jobId: string): Promise<DocumentJob> {
    const result = await this.getJobDetailed(jobId);
    return requireData(result);
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

    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      const result = await this.getJobDetailed(jobId);
      const job = await requireData(result);
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

  async cancelJob(jobId: string): Promise<DocumentJob> {
    const result = await cancelDocumentJob({
      path: { jobId },
      client: this.generatedClient,
    });
    return requireData(result);
  }

  private getJobDetailed(jobId: string) {
    return getDocumentJob({
      path: { jobId },
      client: this.generatedClient,
    });
  }
}
