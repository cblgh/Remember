#!/usr/bin/env python
# -*- coding: utf8 -*-
import datetime
import io
import json
from collections import namedtuple

# INTENT
# i want to remember specific items using prompts to aid recall like
# "how does kademlia work?" 
# i don't want to get overloaded with items to review, so i spread out reviews
# such that there are never more than x tasks to review per day


# a task has:
#   an id (a sequential integer)
#   a creation date (unixtime), 
#   a review date 
#   and a stage
Task = namedtuple("Task", ["date", "stage", "id", "creation_date"])

# afterwards each stage's interval is calculated as the sum of the two preceeding intervals
# next_interval = schedule[stage-1] + schedule[stage-2]
# so interval = schedule[3] + schedule[4] = 6 + 12 = 18
for a in xrange(10):
    interval = schedule[-1] + schedule[-2]
    schedule.append(interval)

print schedule

# interval => min(schedule[stage], 365*3)

# the database containing all of the tasks and their review dates
# the database has:
#   a counter (from which to spawn ids)
#   the review schedule (a list of intervals)
#   a map of tasks (map[task.id] => task)
class Database:
    # a counter (from which to spawn ids)
    self.counter = 0
    # the map of tasks i currently want to remember
    self.tasks = dict()
    # populated from self.tasks with dates which contain the lists of tasks for review
    self.calendar = dict()
    # list of intervals, each index correlating to the stage a task may be in
    self.schedule = [1, 2, 6, 12, 18, 30, 48, 78, 126, 204, 330, 534, 864, 1398]
    # the list of tasks for review today
    self.todays_tasks = list()

    # max amount of tasks to review each day
    self.MAX_TASKS = 4
    # 4 years between reviews is like... enough. i can take time out to review
    # well-known concepts every 4 years
    self.MAX_REVIEW_INTERVAL = 365 * 4
    # path where flatfile database resides
    self.DEFAULT_PATH = "./srs.json"

    def __init__(self):
        self.load()
        self.populate_calendar()

    def generate_id(self):
        task_id = self.counter
        # increment counter
        self.counter += 1
        return task_id

    def load(self):
        with open(self.DEFAULT_PATH, "r") as f:
            obj = json.load(f)
            # these wont exist on first load
            if "tasks" in obj:
                self.tasks = {task["id"]: Task(**task) for (_, task) in obj["tasks"]}
            if "counter" in obj:
                self.counter = obj["counter"]

    def save(self):
        with io.open(DEFAULT_PATH, "w", encoding="utf8") as f:
            f.write(json.dumps({"tasks": self.tasks, "counter": self.counter}, ensure_ascii=False))

    def populate_calendar(self):
        calendar = dict()
        for task in self.tasks:
            date = task.date
            if not date in calendar:
                calendar[date] = []
            calendar[date].append(task)
        return calendar

    def check_calendar(task):
        calendar_tasks = calendar[task.date]
        if len(calendar_tasks) > MAX_TASKS:
            # schedule it a day earlier
            task.date = task.date - 1
        else:
            return task.date
        return self.check_calendar(task)

    def get_interval(task):
        # this is a very mature task, set its review time to the max
        if task.stage > len(schedule):
            return MAX_REVIEW_INTERVAL
        return schedule[task.stage]

    def schedule_task(task):
        interval = get_interval(task)
        task.date += interval
        update_calendar(task)

    def update_calendar(task):
        database["tasks"][task.id] = task

def remember(task):
    init()
    task.stage = 0
    task.id = generate_id()
    schedule_task(task)
    save(database)

def review(task, grade):
    init()
    # maybe grade is how to increment the stage
    # 0 = reset, 1 = next stage, 2 = two stages forward, -1 = previous stage
    if grade == 0:
        task.stage = 0
    else:
        task.stage += grade
    schedule_task(task)
    save(database)
    # return amount of days before next review
    return schedule[task.stage]
