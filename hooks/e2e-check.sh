#!/bin/bash
# === PHOENIX E2E Visual Check Hook v1.0 ===
# PostToolUse hook: triggers visual regression on frontend file changes.
# Absorbed from: Midscene.js E2E Visual Testing (P1#6)
#
# Environment variables:
#   E2E_SKIP=1            Skip this hook entirely
#   E2E_QUICK=1           Run only quick smoke tests (no full visual regression)
#   E2E_BASE_URL          Base URL for the app (default: http://localhost:3000)

set -euo pipefail

# ── Guard: allow skip ────────────────────────────────────────────────────────
if [[ "${E2E_SKIP:-}" == "1" ]]; then
    exit 0
fi

# ── Only trigger on frontend files ───────────────────────────────────────────
FILE_PATH="${FILE_PATH:-}"
if [[ -n "$FILE_PATH" ]]; then
    EXT="${FILE_PATH##*.}"
    if [[ ! "$EXT" =~ ^(tsx|jsx|css|scss|html|vue|svelte)$ ]]; then
        exit 0
    fi
fi

PHOENIX_HOME="$HOME/.claude/phoenix"
E2E_DIR="${E2E_DIR:-$(pwd)/e2e}"
BASE_URL="${E2E_BASE_URL:-http://localhost:3000}"

# ── Check if e2e directory exists ────────────────────────────────────────────
if [[ ! -d "$E2E_DIR" ]]; then
    echo "[e2e-check] No e2e/ directory found at $E2E_DIR — skipping"
    exit 0
fi

# ── Check if playwright is installed ─────────────────────────────────────────
if ! command -v npx &>/dev/null; then
    echo "[e2e-check] npx not found — skipping"
    exit 0
fi

# ── Quick mode: only smoke tests ─────────────────────────────────────────────
if [[ "${E2E_QUICK:-}" == "1" ]]; then
    echo "[e2e-check] Quick mode: running smoke tests only"

    # Find and run only tests tagged @smoke
    SMOKE_TESTS=$(grep -rl "@smoke" "$E2E_DIR" 2>/dev/null || true)
    if [[ -n "$SMOKE_TESTS" ]]; then
        npx playwright test $SMOKE_TESTS --reporter=line 2>&1 || {
            echo "[e2e-check] WARNING: Some smoke tests failed"
            echo "[e2e-check] See playwright-report/ for details"
        }
    else
        echo "[e2e-check] No @smoke-tagged tests found"
    fi
    exit 0
fi

# ── Determine what changed and what to test ──────────────────────────────────
CHANGED_PAGE=""
if [[ -n "$FILE_PATH" ]]; then
    case "$FILE_PATH" in
        */landing/*|*/hero/*|*/HomePage*|*/index.*)
            CHANGED_PAGE="landing"
            ;;
        */app/*|*/dashboard/*)
            CHANGED_PAGE="app"
            ;;
        */pricing/*|*/Pricing*)
            CHANGED_PAGE="pricing"
            ;;
        */docs/*|*/Docs*)
            CHANGED_PAGE="docs"
            ;;
        */components/ui/*|*/components/shared/*)
            # Shared UI change → run all visual regression
            CHANGED_PAGE="all"
            ;;
        *)
            # Unknown scope → run quick visual regression on landing
            CHANGED_PAGE="landing"
            ;;
    esac
fi

# ── Run visual regression ────────────────────────────────────────────────────
echo "[e2e-check] File changed: ${FILE_PATH:-unknown}"
echo "[e2e-check] Scope: $CHANGED_PAGE"

VISUAL_TESTS=()
case "$CHANGED_PAGE" in
    landing)
        VISUAL_TESTS=("$E2E_DIR/landing.spec.ts")
        if [[ -f "$E2E_DIR/visual-regression/desktop.spec.ts" ]]; then
            VISUAL_TESTS+=("$E2E_DIR/visual-regression/desktop.spec.ts")
        fi
        ;;
    app)
        VISUAL_TESTS=("$E2E_DIR/app.spec.ts")
        ;;
    all)
        VISUAL_TESTS=("$E2E_DIR/visual-regression/")
        ;;
    *)
        VISUAL_TESTS=("$E2E_DIR/landing.spec.ts")
        ;;
esac

FAILED=0
for test_file in "${VISUAL_TESTS[@]}"; do
    if [[ -f "$test_file" || -d "$test_file" ]]; then
        echo "[e2e-check] Running: $test_file"
        npx playwright test "$test_file" --reporter=line 2>&1 || {
            FAILED=1
        }
    fi
done

# ── Run AI assertions if midscene tests exist ────────────────────────────────
AI_ASSERT_DIR="$E2E_DIR/ai-assertions"
if [[ -d "$AI_ASSERT_DIR" ]]; then
    echo "[e2e-check] Running AI assertion tests"
    npx playwright test "$AI_ASSERT_DIR" --reporter=line 2>&1 || {
        FAILED=1
    }
fi

# ── Run accessibility check if configured ────────────────────────────────────
if [[ -f "$E2E_DIR/accessibility.spec.ts" ]]; then
    echo "[e2e-check] Running accessibility tests"
    npx playwright test "$E2E_DIR/accessibility.spec.ts" --reporter=line 2>&1 || {
        echo "[e2e-check] WARNING: Accessibility checks found issues"
    }
fi

# ── Report ───────────────────────────────────────────────────────────────────
if [[ $FAILED -eq 1 ]]; then
    echo "[e2e-check] FAILED: Visual regression detected changes"
    echo "[e2e-check] Review playwright-report/index.html for screenshot diffs"
    echo "[e2e-check] If changes are intentional, update baselines with:"
    echo "           npx playwright test --update-snapshots"
    exit 0  # Soft fail — does not block the tool
fi

echo "[e2e-check] PASSED — no visual regressions detected"
