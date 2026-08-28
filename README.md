````markdown
# Box Recommender

Small Django project for an ecommerce warehouse flow: given an order (products + quantities), recommend the most suitable shipping box.

## What it does

Each **product** has length / width / height (cm) and weight (kg).  
Each **box** has inner dimensions, max weight, and cost.

For an order the system:

1. Checks **weight** — total item weight must be ≤ box max weight
2. Checks **fit** — every product must fit inside the box (items may be rotated)
3. Checks **volume** — total item volume must fit under usable box volume (85% fill factor, since packing is never perfect)
4. Among boxes that pass, picks the **cheapest**; if cost is equal, picks the **smallest volume**


## Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py createsuperuser   # optional, for admin
python manage.py runserver
````

**Admin:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

## API

| Method | URL                           | Purpose                              |
| ------ | ----------------------------- | ------------------------------------ |
| GET    | `/api/boxes/`                 | List active boxes                    |
| POST   | `/api/recommend/`             | Recommend from `order_id` or `items` |
| GET    | `/api/orders/<id>/recommend/` | Recommend + save on that order       |
| POST   | `/api/orders/`                | Create order, recommend box          |

### Examples

Recommend by SKUs:

```bash
curl -X POST http://127.0.0.1:8000/api/recommend/ ^
  -H "Content-Type: application/json" ^
  -d "{\"items\": [{\"sku\": \"MUG-01\", \"quantity\": 2}]}"
```

Create an order:

```bash
curl -X POST http://127.0.0.1:8000/api/orders/ ^
  -H "Content-Type: application/json" ^
  -d "{\"reference\": \"ORD-1001\", \"items\": [{\"sku\": \"LAMP-01\", \"quantity\": 1}]}"
```

CLI:

```bash
python manage.py recommend_box ORD-1001
```

## Project layout

```text
config/                 # Django project settings
packing/
  models.py             # Product, Box, Order, OrderItem
  services/recommender.py
  views.py              # JSON API
  management/commands/  # seed_demo_data, recommend_box
  tests/
```

## Tests

```bash
python manage.py test packing -v 2
```

Also intended for GitHub Actions — workflow file is `github-actions-tests.yml`. To enable CI on GitHub: create `.github/workflows/tests.yml` from that file (needs a token with the `workflow` scope), or paste the local run from `TEST_OUTPUT.md`.

## Design notes

* Dimensions are stored as `Decimal` so money/weight math stays precise.
* Rotation: all 6 orientations are considered when checking if a product fits.
* Fill factor `0.85` is a constant in `recommender.py` — easy to tune later.
* Inactive boxes (`is_active=False`) are ignored.

## Submission files

* `README.md` — this file
* `AI_USAGE.md` — how AI was used
* `LEARNINGS.md` — what I learned
* `TEST_OUTPUT.md` — test run paste
* `CHAT_TRANSCRIPT.md` — exported chat 

````

