from collections import defaultdict
from datetime import *
import re

from rules import *

#TODO: rename moy -> month
#TODO: add support for ','
#TODO: More accurate name for CronParser


class CronParser(object):
    """
        Space delimited cron string:
        
        minute[0..59] hour[0..23] dom[1..31] moy[1..12] dow[1..7](1=Monday) year

        allows "*", "-", "/", and "[0-9]"
    """
    fields = ["minute", "hour", "dom", "moy", "dow", "year"]

    def __init__(self, rules=list(), exceptions=list(), start_year=None, stop_year=None, in_utc=False):
        """
            rules and exeptions should look like:
            [("name", "* * * * * *"), ...]

            start_year and stop_year are integers that determine the inclusive range of years that will be checked
                default is the class variables start_year and stop_year for the Rule class
        """
        
        self.rules = defaultdict(list)
        self.exceptions = defaultdict(list)
        self.holiday_exceptions = {}  #Optimization to reduce the effect of one day exceptions on the runtime
                                      #  Looks like {(dd,mm,yyyy): name}  

        self.start_year = start_year
        self.stop_year = stop_year

        self.add_rules(rules)
        self.add_exceptions(exceptions)

    

    def add_rules(self, rules):
        for rname, rule in rules:
            self.rules[rname].append(self.get_rule(rule))



    def add_exceptions(self, exceptions):
        for ename, exception in exceptions:
            #Holidays can be queried faster than more general rules
            if BasicCronRule.is_holiday(exception):
                self.holiday_exceptions[BasicCronRule.holiday_tuple(exception)] = ename
            else:
                self.exceptions[ename].append(self.get_rule(exception))                


    def get_rule(self, cron_string):
        #Try range rule
        if CronRangeRule.looks_like_range_rule(cron_string):
            return CronRangeRule(cron_string, start_year=self.start_year, stop_year=self.stop_year)
        else:
            return BasicCronRule(cron_string, start_year=self.start_year, stop_year=self.stop_year)


    def pick_rules(self, time_obj):
        """
            Picks the rules that time_obj belongs to.  
            
            time_obj is a datetime object.

            if self.in_utc is defined, then the time_obj will be converted to UTC

            If rules overlap, the time_obj will belong to multiple rules.
            Therefore return is a list:
                e.g.
                [], ["2001"], ["weekday_afternoons", "every_thursday"],
        """
        

        rule_list = []

        #Check holiday exceptions:
        holiday_exc_name = self.holiday_exceptions.get((time_obj.day, time_obj.month, time_obj.year), None)

        if holiday_exc_name is not None:
            return [holiday_exc_name]

        #Check exceptions
        for ename, exceptions in self.exceptions.items():
            for exception in exceptions:
                if time_obj in exception:
                    return [ename]

        #No exceptions match, so all rules are available
        for rname, rules in self.rules.items():
            for rule in rules:
                if time_obj in rule:
                    rule_list.append(rname)

        return rule_list
