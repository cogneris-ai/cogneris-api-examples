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
  run(
    'npm',
    ['install', '--ignore-scripts', '--no-audit', '--no-fund', '--no-save', sdkDirectory],
    root,
  );
  run('npm', ['run', 'build', '--prefix', 'cli'], root);
} finally {
  await rm(temporaryDirectory, { recursive: true, force: true });
}
