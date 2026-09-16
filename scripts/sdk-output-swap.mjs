import fs from "node:fs/promises";
import path from "node:path";

export async function replaceOutput({
  committedOutput,
  stagedOutput,
  filesystem = fs,
}) {
  const backupRoot = await filesystem.mkdtemp(
    path.join(path.dirname(committedOutput), ".sdk-backup-"),
  );
  const backup = path.join(backupRoot, path.basename(committedOutput));
  let hadPreviousOutput = true;
  try {
    await filesystem.rename(committedOutput, backup);
  } catch (error) {
    if (error.code !== "ENOENT") {
      await filesystem.rm(backupRoot, { recursive: true, force: true });
      throw error;
    }
    hadPreviousOutput = false;
    await filesystem.rm(backupRoot, { recursive: true, force: true });
  }

  try {
    await filesystem.rename(stagedOutput, committedOutput);
  } catch (installError) {
    if (hadPreviousOutput) {
      try {
        await filesystem.rename(backup, committedOutput);
      } catch (restoreError) {
        throw new Error(
          `Failed to install generated SDK output (${installError.message}); ` +
            `automatic recovery failed (${restoreError.message}). ` +
            `Previous SDK output preserved at: ${backup}`,
          { cause: installError },
        );
      }
      await filesystem.rm(backupRoot, { recursive: true, force: true });
    }
    throw installError;
  }
  if (hadPreviousOutput) {
    await filesystem.rm(backupRoot, { recursive: true, force: true });
  }
}
