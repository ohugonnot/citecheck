# Summary of "A Short Book About Caches" (a made-up example)

Programs repeat themselves, so caches pay off. For well-behaved code the book says hit rates are "95 to 97 percent" (lesson 1). A miss to main memory costs about 200 cycles against 4 for a hit (lesson 1).

A write-back cache keeps the new value and marks the line as dirty (lesson 2). The author's warning is blunt: "dirty lines are a debt, not a gift" (lesson 2).

Expiry is the simplest invalidation policy: an entry dies after 60 seconds (lesson 3). The book never talks about SIMD instructions.
