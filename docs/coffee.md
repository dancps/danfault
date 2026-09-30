# Coffee Calculator

A desktop GUI tool for calculating coffee-to-water proportions.

## Install

```bash
cd python/danfault
pip install -e ".[gui]"
```

Requires Python 3.8+ and PyQt6 (installed via the `gui` extra above).

## Run

```bash
coffee
```

## Usage

Fill in any two of the three fields — results appear inline as you type.

| Ratio | Coffee (g) | Water (g) | Shows |
|-------|-----------|-----------|-------|
| ✅ | ✅ | — | Water needed (gray) |
| ✅ | — | ✅ | Coffee needed (gray) |
| — | ✅ | ✅ | Derived ratio (gray) |
| ✅ | ✅ | ✅ consistent | ✓ (green) next to ratio |
| ✅ | ✅ | ✅ inconsistent | ✗ (red) + targets and diffs per field |

**Diff colors:** `(+Xg)` in green means you need to add more; `(-Xg)` in red means you have too much.

### Ratio format

The ratio field accepts `coffee:water` in any scale:

```
1:15      → 1g coffee per 15g water
15:200    → 15g coffee per 200g water (same as 1:13.33)
```

## Recipes

Built-in presets:

| Recipe | Ratio |
|--------|-------|
| V60 | 1:15 |
| French Press | 1:10 |
| Espresso | 1:2 |
| Chemex | 1:17 |
| AeroPress | 1:13 |
| Cold Brew | 1:5 |
| Moka Pot | 1:7 |

**Apply** — loads the selected recipe's ratio into the ratio field.

**Save as…** — saves the current ratio field as a named recipe. Custom recipes are persisted at `~/.config/danfault/coffee_recipes.json` and merged with the built-in list on startup.
