import { execFileSync } from 'node:child_process';
import { cp, mkdtemp, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const temporaryDirectory = await mkdtemp(path.join(os.tmpdir(), 'cogneris-cli-build-'));
const sdkDirectory = path.join(temporaryDirectory, 'typescript-sdk');

function run(command, argumentsList, cwd) {
  execFileSync(command, argumentsList, { cwd, stdio: 'inherit' });
}

function capture(command, argumentsList, cwd) {
  return execFileSync(command, argumentsList, {
    cwd,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'inherit'],
  });
}

try {
  await cp(path.join(root, 'sdks', 'typescript'), sdkDirectory, {
    recursive: true,
    filter: (entry) => {
      const relative = path.relative(path.join(root, 'sdks', 'typescript'), entry);
      return !relative.split(path.sep).includes('dist') &&
        !relative.split(path.sep).includes('node_modules');
    },
  });
  run(
    path.join(root, 'node_modules', '.bin', 'tsc'),
    ['-p', path.join(sdkDirectory, 'tsconfig.json')],
    sdkDirectory,
  );
  const packedName = capture(
    'npm',
    ['pack', '--pack-destination', temporaryDirectory, '--silent'],
    sdkDirectory,
  ).trim().split('\n').at(-1);
  if (!packedName) throw new Error('SDK package did not produce a tarball.');
  run(
    'npm',
    [
      'install',
      '--ignore-scripts',
      '--no-audit',
      '--no-fund',
      '--no-save',
      path.join(temporaryDirectory, packedName),
    ],
    root,
  );
  run('npm', ['run', 'build', '--prefix', 'cli'], root);
} finally {
  await rm(temporaryDirectory, { recursive: true, force: true });
}
