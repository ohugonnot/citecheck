# Summary of "A Short Book About Caches" (the same summary, with four faults)

Programs repeat themselves, so caches pay off. For well-behaved code the book says hit rates are "99 to 100 percent" (lesson 1). A miss to main memory costs about 300 cycles against 4 for a hit (lesson 1).

A write-back cache keeps the new value and marks the line as dirty (lesson 2). The author's warning is blunt: "dirty lines are a debt, not a gift" (lesson 3).

Expiry is the simplest invalidation policy: an entry dies after 60 seconds (lesson 9). The book never talks about write-through caches.
