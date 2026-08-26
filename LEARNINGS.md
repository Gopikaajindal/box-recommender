# What I learned

The biggest thing I learned is that box selection is not just "pick the box with enough volume." Weight limits matter, and so does whether each item can physically fit. A long product can have a small volume and still not go into a short carton.

I also learned that rotation is important. If you only compare length with length, width with width, and height with height, you reject products that would fit after turning them. Checking orientations fixed a few of my early test cases.

Another practical lesson: packing is never 100% efficient. Even when the math says the volumes fit, real packing leaves gaps. That is why I used a fill factor of 0.85 instead of comparing raw volumes.

On the Django side, putting the recommendation rules in `services/recommender.py` instead of stuffing everything into views made testing much easier. I could unit-test the logic first, then add a few API tests.

I thought about full 3D bin packing, but for this assignment it felt too complex. A clear set of rules (weight, fit, volume, then cheapest box) was enough and easier to explain to a warehouse team.
