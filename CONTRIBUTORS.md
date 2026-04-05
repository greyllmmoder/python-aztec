# Contributors & Lineage

## Authors
- Originally written by Dmitry Alimov (delimitry).
- Updates, bug fixes, and active maintenance in this fork by greyllmmoder.

## Current maintainer
- greyllmmoder - https://github.com/greyllmmoder

## Upstream lineage (MIT license chain)
This project is a fork of **dlenski/aztec_code_generator**
(https://github.com/dlenski/aztec_code_generator), which is itself
a fork of **delimitry/aztec_code_generator**
(https://github.com/delimitry/aztec_code_generator).

Both upstream projects are MIT licensed. The original upstream license
text is preserved in `LICENSE.upstream`.

## What changed from upstream
- Fixed: CRLF encoding crash (upstream issue #5)
- Fixed: Error correction capacity calculation (upstream issue #7)
- Added: SVG renderer (based on upstream PR #6)
- Added: Type hints, docstrings, CLI, PDF output, Rune mode
- Restructured: Single-file module split into package

## Third-party contributions incorporated
- SVG support: originally authored by Zazzik1
  (https://github.com/dlenski/aztec_code_generator/pull/6), MIT license
