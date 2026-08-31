/**
 * Prepares the two Lambda assets CDK uploads, without needing Docker.
 *
 *   build/app/services/**   the application code
 *   build/layer/python/**   third-party dependencies
 *
 * The layer is installed with explicit manylinux flags rather than for the host
 * platform. That is the whole point: pydantic-core and cryptography are native
 * extensions, and a wheel built for Windows or macOS will import fine on the
 * developer's machine and then fail inside Lambda with a cryptic ELF error.
 * Forcing --platform/--only-binary makes that mistake impossible instead of
 * merely unlikely.
 */
import { execFileSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, "..");
const buildDir = join(here, "build");
const appDir = join(buildDir, "app");
const layerDir = join(buildDir, "layer", "python");

const PYTHON_VERSION = "3.12";
const PLATFORM = "manylinux2014_x86_64";

/** Not shipped to Lambda: tests, caches, fixtures used only by the local runner. */
const EXCLUDED = new Set(["__pycache__", "tests", ".pytest_cache", ".mypy_cache", ".ruff_cache"]);

function log(step, message) {
  console.log(`[${step}] ${message}`);
}

function pythonExecutable() {
  for (const candidate of [["python", ["--version"]], ["python3", ["--version"]], ["py", ["-3", "--version"]]]) {
    try {
      execFileSync(candidate[0], candidate[1], { stdio: "ignore" });
      return candidate[0] === "py" ? { cmd: "py", prefix: ["-3", "-m", "pip"] } : { cmd: candidate[0], prefix: ["-m", "pip"] };
    } catch {
      // try the next one
    }
  }
  throw new Error("No encuentro Python en el PATH. Instala Python 3.12+ y vuelve a intentar.");
}

rmSync(buildDir, { recursive: true, force: true });
mkdirSync(appDir, { recursive: true });
mkdirSync(layerDir, { recursive: true });

log("app", "copiando services/ ...");
cpSync(join(repoRoot, "services"), join(appDir, "services"), {
  recursive: true,
  filter: (src) => !EXCLUDED.has(src.split(/[\\/]/).pop()),
});

const requirements = join(here, "lambda-requirements.txt");
if (!existsSync(requirements)) {
  throw new Error(`No encuentro ${requirements}`);
}

const python = pythonExecutable();
log("layer", `instalando dependencias para ${PLATFORM} / cp${PYTHON_VERSION.replace(".", "")} ...`);
execFileSync(
  python.cmd,
  [
    ...python.prefix,
    "install",
    "--quiet",
    "--target", layerDir,
    "--platform", PLATFORM,
    "--implementation", "cp",
    "--python-version", PYTHON_VERSION,
    "--only-binary=:all:",
    "--upgrade",
    "-r", requirements,
  ],
  { stdio: "inherit" },
);

log("listo", `app -> ${appDir}`);
log("listo", `layer -> ${layerDir}`);
