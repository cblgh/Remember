#!/usr/bin/env python
# -*- coding: utf8 -*-
from datetime import datetime, timedelta
import io
import json
import sys
import os

DATE_FORMAT = "%Y-%m-%d"
TODAY = datetime.today().strftime(DATE_FORMAT)

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
        # max amount of tasks to review at any time 
        self.MAX_TASKS = 4
        # 4 years between reviews is like... enough. i can take time out to review
        # well-known concepts every 4 years
        self.MAX_REVIEW_INTERVAL = 365 * 4
        self.DEFAULT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "srs.json")

        self.load()
        self.calendar = self.populate_calendar()
        self.todays_tasks = []
        # get all tasks for review up to and including today
        for date in self.calendar:
            if datetime.strptime(date, DATE_FORMAT) <= datetime.today():
                # get the tasks that are due
                for task in self.calendar[date]:
                    # and add them to today's tasks to review
                    self.todays_tasks.append(task)
        # only show MAX_CONCURRENT_TASKS to prevent overwhelming myself,
        # and add a bit of motivation to finish tasks (in order to see more, (hopefully))
        self.todays_tasks = self.todays_tasks[:self.MAX_TASKS]

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
        temp_date = task["review_date"]
        if temp_date not in self.calendar:
            return task["review_date"]
        calendar_tasks = self.calendar[temp_date]
        if len(calendar_tasks) > self.MAX_TASKS and task["stage"] > 3:
            # schedule it a day earlier
            task["review_date"] = (datetime.strptime(temp_date, DATE_FORMAT) - timedelta(days=1)).strftime(DATE_FORMAT)
        else:
            return task["review_date"]
        return self.check_calendar(task)

    def get_interval(self, task):
        # this is a very mature task, set its review time to the max
        if task["stage"] > len(self.schedule):
            return self.MAX_REVIEW_INTERVAL
        return self.schedule[task["stage"]]

    def schedule_task(self, task):
        interval = timedelta(days=self.get_interval(task))
        new_date = datetime.strptime(task["review_date"], DATE_FORMAT) + interval
        task["review_date"] = new_date.strftime(DATE_FORMAT)
        # check calendar and reschedule if there are collisions
        task["review_date"] = self.check_calendar(task)
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
    
    def forget(self, task_number):
        task_number = int(task_number)
        task = self.todays_tasks[task_number]
        task_id = unicode(task["task_id"])
        del self.tasks[task_id]
        self.save()

    def review(self, task_number, grade):
        task_number = int(task_number)
        grade = int(grade)
        # no such task to review
        if task_number > len(self.todays_tasks) - 1:
            print "no such task to review"
            return -1
        task = self.todays_tasks[task_number]
        # maybe grade is how to increment the stage
        # 0 = reset, 1 = next stage, 2 = two stages forward, -1 = previous stage
        if grade == 0:
            task["stage"] = 0
            print task["answer"]
        else:
            task["stage"] += grade
        self.schedule_task(task)
        self.save()
        # return amount of days before next review
        return self.schedule[task["stage"]]

    def get_tasks(self, category):
        return "\n".join(["{} {}".format(index, task["data"]) for (index, task) in
            enumerate(self.todays_tasks) if (not category or (category and
                task["category"] == category))])

def remember(category, description, answer, stage=0):
    database = Database()
    print category, description, answer
    database.remember(category, description, answer, stage)

def forget(task_number):
    return Database().forget(task_number)

def review(task_number, grade=1):
    return Database().review(task_number, grade)

def parse(message):
    parts = (message.split(":") + ["", "0"])[:3]
    parts[-1] = 0 if parts[-1] == "" else parts[-1]
    return parts

def tasks(category=None):
    tasks = Database().get_tasks(category)
    return tasks

if __name__ == "__main__":
    # print usage message if not enough input params
    if len(sys.argv) < 2:
        print "usage: [tasks <optional: category>|remember <category> <description:answer>|review <item number> <grade>]"
        sys.exit()
    # printing today's tasks
    if sys.argv[1] == "tasks":
        category = None
        if len(sys.argv) > 2:
            category = sys.argv[2]
        tasks = tasks(category)
        if not tasks:
            print "no tasks left! (or empty category..)"
        else: 
            print tasks
    # add to the database
    elif sys.argv[1] == "remember" and len(sys.argv) >= 3:
        category = sys.argv[2]
        description, answer, stage = parse(" ".join(sys.argv[3:]))
        remember(category, description, answer, stage)
    # complete one of today's tasks
    elif sys.argv[1] == "review" and len(sys.argv) >= 4:
        print review(*sys.argv[2:])
