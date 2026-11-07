import { execFileSync } from "node:child_process";
import { join } from "node:path";
import { expect, it } from "vitest";

// The source uses design-system tokens only: the guard exits non-zero on a hard-coded
// colour or radius. The script comes through the linked package (node_modules symlink).
it("passes the design-system aesthetic guard", () => {
  const guard = join(process.cwd(), "node_modules", "@suite", "design-system", "scripts", "aesthetic-guard.mjs");
  expect(() => execFileSync("node", [guard, join(process.cwd(), "src")], { encoding: "utf8" })).not.toThrow();
});
