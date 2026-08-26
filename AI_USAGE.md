# AI Usage

## 1. Tools used

- ChatGPT (web) — mainly for clarifying doubts while I was designing the packing rules and writing tests.

I wrote the Django models, API views, management commands, and the recommendation logic myself in this repo.

## 2. Prompts I gave (paraphrased)

1. "For shipping boxes, is checking total volume + individual item fit good enough, or do I need real 3D bin packing?"
2. "How do people usually handle rotating a product inside a box when checking if it fits?"
3. "In Django tests, what's a clean way to compare Decimal fields without floating point weirdness?"
4. "Should I pick the cheapest box or the smallest box when recommending?"

## 3. Output I accepted

- Confirmation that for a small catalog, weight + per-item fit + volume with a fill factor is a reasonable approach (full bin packing not required).
- Idea to try all dimension permutations / sort edges when checking if an item fits in a box.
- Advice to store money/weight as Decimal in Django models.
- Tie-break idea: cheapest first, then smaller volume if cost is the same.

## 4. Output I rejected or changed

- Suggestion to pull in OR-Tools / PuLP for packing — rejected. Too heavy for this assignment and harder to explain.
- A sample that used floats for dimensions — I switched everything to Decimal.
- A version that only checked volume and ignored whether a single long item could physically fit — I kept the explicit fit check.
- An API sketched with Django REST Framework serializers — I stuck to plain `JsonResponse` views to keep the project smaller and easier to follow.

## 5. Mistakes / weak suggestions from the AI

- At one point it mixed up outer product size vs inner box size and talked as if packing efficiency could be 100%. I kept a 0.85 fill factor instead.
- Early example code compared dimensions without allowing rotation, so a lamp that clearly fits sideways would have been rejected. I fixed that in `product_fits_in_box`.
- It suggested caching recommendations in Redis. Unnecessary for this scope.

## 6. How I verified the final code

1. `python manage.py makemigrations` / `migrate` — DB created cleanly.
2. `python manage.py seed_demo_data` — sample products/boxes loaded.
3. `python manage.py test packing -v 2` — all tests green (see `TEST_OUTPUT.md`).
4. Manual API checks with curl for mug-only orders (expect Small) and lamp orders (expect Medium).
5. Case where no box fits (folding chair without an XL box in the test DB) returns a clear 422 / "No active box..." reason.
6. Re-read `recommender.py` line by line to make sure weight, fit, and volume checks all run before cost sorting.
