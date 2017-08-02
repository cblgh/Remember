# tome-srs

```py
INTENT
i want to remember specific items using prompts to aid recall like
"how does kademlia work?" 
i don't want to get overloaded with items to review, so i spread out reviews
such that there are never more than x tasks to review per day

a task has:
  an id (a sequential integer)
  a category (french, general)
  a creation date (unixtime), 
  a review date 
  and a stage
  
the database containing all of the tasks and their review dates
the database has:
  a counter (from which to spawn ids)
  the review schedule (a list of intervals)
  a map of tasks (map[task.id] => task)

afterwards each stage's interval is calculated as the sum of the two preceeding intervals
next_interval = schedule[stage-1] + schedule[stage-2]
so interval = schedule[3] + schedule[4] = 6 + 12 = 18
for a in xrange(10):
    interval = schedule[-1] + schedule[-2]
    schedule.append(interval)

interval => min(schedule[stage], 365*3)

```
