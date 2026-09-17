import { readFile } from 'node:fs/promises';
import path from 'node:path';

import {
  CognerisClient,
  CognerisError,
  type CognerisClientOptions,
  type CognerisRegion,
  type DocumentJob,
  type DocumentJobCancellation,
  type DocumentJobSubmitOperation,
  type DocumentJobSubmission,
  type Envelope,
} from '@cogneris-ai/document-ai-sdk';

const USAGE = `Usage:
  cogneris [--region us|eu] extract <file>
  cogneris [--region us|eu] jobs submit --operation <operation> --input-reference <reference>
  cogneris [--region us|eu] jobs get <job-id>
  cogneris [--region us|eu] jobs wait <job-id>
  cogneris [--region us|eu] jobs cancel <job-id>`;

const OPERATIONS = new Set<DocumentJobSubmitOperation>([
  'Extraction',
  'Classification',
  'ZeroShot',
  'Crop',
  'Split',
  'Facematch',
]);

class UsageError extends Error {}

type Writable = {
  write(value: string): unknown;
};

type Client = {
  cancelJob(jobId: string): Promise<DocumentJobCancellation>;
  extract(file: Blob | File, options?: { fileName?: string }): Promise<Envelope>;
  getJob(jobId: string): Promise<DocumentJob>;
  submitJob(
    operation: DocumentJobSubmitOperation,
    inputReference: string,
  ): Promise<DocumentJobSubmission>;
  waitForJob(jobId: string): Promise<DocumentJob>;
};

type CliDependencies = {
  env: Record<string, string | undefined>;
  io: { stderr: Writable; stdout: Writable };
  /** Test-only factory. Tests use this to construct CognerisClient with its loopback seam. */
  _createClientForTesting?: (options: CognerisClientOptions) => Client;
};

type Command =
  | { kind: 'extract'; filePath: string }
  | { kind: 'submit'; operation: DocumentJobSubmitOperation; inputReference: string }
  | { kind: 'get' | 'wait' | 'cancel'; jobId: string };

function failUsage(message = 'Invalid command or options.'): never {
  throw new UsageError(message);
}

function parseRegion(argumentsList: string[], environmentRegion: string | undefined) {
  const remaining: string[] = [];
  let optionRegion: string | undefined;
  for (let index = 0; index < argumentsList.length; index += 1) {
    const argument = argumentsList[index];
    if (argument === '--region') {
      if (optionRegion !== undefined || index + 1 >= argumentsList.length) failUsage();
      optionRegion = argumentsList[index + 1];
      index += 1;
    } else {
      remaining.push(argument);
    }
  }
  const region = optionRegion ?? environmentRegion ?? 'us';
  if (region !== 'us' && region !== 'eu') {
    throw new UsageError('Region must be either us or eu.');
  }
  return { region: region as CognerisRegion, remaining };
}

function nonEmpty(value: string | undefined): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function requiredValue(value: string | undefined): value is string {
  return nonEmpty(value) && !value.startsWith('-');
}

function parseSubmit(argumentsList: string[]): Command {
  let operation: string | undefined;
  let inputReference: string | undefined;
  for (let index = 0; index < argumentsList.length; index += 1) {
    const argument = argumentsList[index];
    const value = argumentsList[index + 1];
    if (argument === '--operation' && operation === undefined && requiredValue(value)) {
      operation = value;
      index += 1;
    } else if (
      argument === '--input-reference' &&
      inputReference === undefined &&
      requiredValue(value)
    ) {
      inputReference = value;
      index += 1;
    } else {
      failUsage();
    }
  }
  if (!requiredValue(operation) || !OPERATIONS.has(operation as DocumentJobSubmitOperation)) failUsage();
  if (!requiredValue(inputReference)) failUsage();
  return {
    kind: 'submit',
    operation: operation as DocumentJobSubmitOperation,
    inputReference,
  };
}

function parseCommand(argumentsList: string[]): Command {
  if (argumentsList.some((argument) => argument === '--api-key' || argument.startsWith('--api-key='))) {
    failUsage();
  }
  if (
    argumentsList[0] === 'extract' &&
    argumentsList.length === 2 &&
    requiredValue(argumentsList[1])
  ) {
    return { kind: 'extract', filePath: argumentsList[1] };
  }
  if (argumentsList[0] !== 'jobs') failUsage();
  if (argumentsList[1] === 'submit') return parseSubmit(argumentsList.slice(2));
  if (
    (argumentsList[1] === 'get' ||
      argumentsList[1] === 'wait' ||
      argumentsList[1] === 'cancel') &&
    argumentsList.length === 3 &&
    requiredValue(argumentsList[2])
  ) {
    return { kind: argumentsList[1], jobId: argumentsList[2] };
  }
  failUsage();
}

function requireApiKey(value: string | undefined): string {
  if (
    typeof value !== 'string' ||
    !value.startsWith('xtkt_live_') ||
    value.length <= 'xtkt_live_'.length ||
    value.length > 4_096 ||
    !/^[\x21-\x7e]+$/.test(value)
  ) {
    throw new UsageError(
      'COGNERIS_API_KEY must be a public API key with the required prefix and a non-empty visible-ASCII suffix.',
    );
  }
  return value;
}

async function runCommand(client: Client, command: Command): Promise<unknown> {
  switch (command.kind) {
    case 'extract': {
      let contents: Buffer;
      try {
        contents = await readFile(command.filePath);
      } catch {
        throw new UsageError('Unable to read input file.');
      }
      const envelope = await client.extract(new Blob([new Uint8Array(contents)]), {
        fileName: path.basename(command.filePath),
      });
      if (envelope.hasErrors === true) {
        throw new CognerisError('Cogneris extraction failed.');
      }
      return envelope;
    }
    case 'submit':
      return client.submitJob(command.operation, command.inputReference);
    case 'get':
      return client.getJob(command.jobId);
    case 'wait':
      return client.waitForJob(command.jobId);
    case 'cancel':
      return client.cancelJob(command.jobId);
  }
}

export async function _runCliForTesting(
  argumentsList: string[],
  dependencies: CliDependencies,
): Promise<number> {
  try {
    const { region, remaining } = parseRegion(argumentsList, dependencies.env.COGNERIS_REGION);
    const command = parseCommand(remaining);
    const apiKey = requireApiKey(dependencies.env.COGNERIS_API_KEY);
    const createClient = dependencies._createClientForTesting ??
      ((options: CognerisClientOptions) => new CognerisClient(options));
    const result = await runCommand(createClient({ apiKey, region }), command);
    dependencies.io.stdout.write(`${JSON.stringify(result)}\n`);
    return 0;
  } catch (error) {
    if (error instanceof UsageError) {
      dependencies.io.stderr.write(`${error.message}\n${USAGE}\n`);
      return 2;
    }
    if (error instanceof CognerisError) {
      dependencies.io.stderr.write(`${error.message}\n`);
      return 1;
    }
    dependencies.io.stderr.write('Cogneris CLI request failed.\n');
    return 1;
  }
}

export async function runCli(argumentsList: string[]): Promise<number> {
  return _runCliForTesting(argumentsList, {
    env: process.env,
    io: { stderr: process.stderr, stdout: process.stdout },
  });
}
