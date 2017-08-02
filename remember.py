#!/usr/bin/env python
# -*- coding: utf8 -*-
import datetime
import io
import json
import sys

DATE_FORMAT = "%Y-%m-%d"
TODAY = datetime.datetime.today().strftime(DATE_FORMAT)


# INTENT
# i want to remember specific items using prompts to aid recall like
# "how does kademlia work?" 
# i don't want to get overloaded with items to review, so i spread out reviews
# such that there are never more than x tasks to review per day


# a task has:
#   an id (a sequential integer)
#   a category (french, general)
#   a creation date (unixtime), 
#   a review date 
#   and a stage



# afterwards each stage's interval is calculated as the sum of the two preceeding intervals
# next_interval = schedule[stage-1] + schedule[stage-2]
# so interval = schedule[3] + schedule[4] = 6 + 12 = 18
# for a in xrange(10):
#     interval = schedule[-1] + schedule[-2]
#     schedule.append(interval)
#
# print schedule

# interval => min(schedule[stage], 365*3)

# the database containing all of the tasks and their review dates
# the database has:
#   a counter (from which to spawn ids)
#   the review schedule (a list of intervals)
#   a map of tasks (map[task.id] => task)
class Database(object):

    def __init__(self):
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
        self.DEFAULT_PATH = "srs.json"

        self.load()
        self.calendar = self.populate_calendar()
        self.todays_tasks = []
        if TODAY in self.calendar:
            self.todays_tasks = self.calendar[TODAY]

    def generate_id(self):
        task_id = self.counter
        # increment counter
        self.counter += 1
        self.save()
        return task_id

    def load(self):
        try: 
            with io.open(self.DEFAULT_PATH, "r", encoding="utf-8") as f:
                obj = json.load(f)
                # these wont exist on first load
                if "tasks" in obj:
                    self.tasks = obj["tasks"]
                if "counter" in obj:
                    self.counter = obj["counter"]
        except IOError as e:
            pass

    def save(self):
        with io.open(self.DEFAULT_PATH, "w", encoding="utf-8") as f:
            data = json.dumps({"tasks": self.tasks, "counter": self.counter}, ensure_ascii=False)
            if isinstance(data, str):
                data = data.decode("utf-8")
            f.write(data)

    def populate_calendar(self):
        calendar = dict()
        for _, task in self.tasks.items():
            date = task["review_date"]
            if not date in calendar:
                calendar[date] = []
            calendar[date].append(task)
        return calendar

    def check_calendar(self, task):
        calendar_tasks = calendar[task["review_date"]]
        if len(calendar_tasks) > MAX_TASKS:
            # schedule it a day earlier
            task["review_date"] = task["review_date"] - 1
        else:
            return task["review_date"]
        return self.check_calendar(task)

    def get_interval(self, task):
        # this is a very mature task, set its review time to the max
        if task["stage"] > len(self.schedule):
            return MAX_REVIEW_INTERVAL
        return self.schedule[task["stage"]]

    def schedule_task(self, task):
        interval = datetime.timedelta(days=self.get_interval(task))
        new_date = datetime.datetime.strptime(task["review_date"], DATE_FORMAT) + interval
        task["review_date"] = new_date.strftime(DATE_FORMAT)
        self.update_calendar(task)
        self.save()

    def update_calendar(self, task):
        self.tasks[task["task_id"]] = task
        self.save()

    def remember(self, category, description, answer="", stage=0):
        task = dict()
        task["category"] = category
        task["data"] = description
        task["answer"] = answer
        task["stage"] = stage
        task["review_date"] = TODAY
        task["creation_date"] = TODAY
        task["task_id"] = self.generate_id()
        self.schedule_task(task)
        self.save()

    def review(self, task_number, grade):
        task = self.todays_tasks[task_number]
        # maybe grade is how to increment the stage
        # 0 = reset, 1 = next stage, 2 = two stages forward, -1 = previous stage
        if grade == 0:
            task["stage"] = 0
        else:
            task["stage"] += grade
        self.schedule_task(task)
        self.save()
        # return amount of days before next review
        return self.schedule[task.stage]

    def get_tasks(self, category):
        return "\n".join(["{} {}".format(index, task["data"]) for (index, task) in
            enumerate(self.todays_tasks) if (!category or (category and task["category"] is category))])

def remember(category, description, answer, stage=0):
    database = Database()
    database.remember(category, description, stage)

def review(task, grade):
    return Database().review(task, grade)

def tasks(category=None):
    return Database().get_tasks(category)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "usage: [tasks|remember <description>|review <item number> <grade>]"
        sys.exit()
    if sys.argv[1] == "tasks":
        print tasks()
    elif sys.argv[1] == "remember" and len(sys.argv) >= 3:
        remember(sys.argv[2])
    elif sys.argv[1] == "review" and len(sys.argv) >= 4:
        review(*sys.argv[2:])
