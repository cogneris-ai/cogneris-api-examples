#!/usr/bin/env node

import { runCli } from './run';

let stdoutFailed = false;
process.stdout.on('error', () => {
  if (stdoutFailed) return;
  stdoutFailed = true;
  process.exitCode = 1;
  process.stderr.write('Cogneris CLI output failed.\n');
});

void runCli(process.argv.slice(2)).then(
  (exitCode) => {
    process.exitCode = stdoutFailed ? 1 : exitCode;
  },
  () => {
    process.exitCode = 1;
    process.stderr.write('Cogneris CLI request failed.\n');
  },
);
