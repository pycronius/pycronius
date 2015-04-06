import re

from utils import Bunch

#TODO: option to set min/max year
#TODO: add is_valid_rule methods


#Optimization for handling wildcards
class WildCardSet(object):
    #Always return true for in operator 
    # x in WildCardSet() -> True
    def __contains__(self, key):
        return True


class InvalidFieldError(Exception):
    pass

class InvalidCronStringError(Exception):
    pass


class BasicCronRule(object):

    holiday_re = "[\*]\s[\*]\s(\d{1,2})\s(\d{1,2})\s[\*]\s(\d{4})"
    
    def __init__(self, cron_string):
        self.rulesets = self.parse(cron_string)


    @classmethod
    def parse_field(cls, f, minimum=0, maximum=0):
        """
            Returns a set containing the right elements
            minimum and maximum define the range of values used for wildcards
            minimum and maximum as passed should be inclusive integers. 
            All +1s will be added here.
                e.g. parse_field("0-1", 0, 2) -> set([0,1])
                e.g. parse_field("*", 0, 1) -> set([0,1])

        """
        digits = {i for i in xrange(10)}

        final_range = []
        try:
            #Handle clauses containing '/'
            divisor = 1
            div_splits = f.split("/")

            if len(div_splits) > 1:
                divisor = int(div_splits[1])

            # *, */x
            if f[0] == "*":
                if len(f) == 0:
                    return WildCardSet()
                else:
                    return set(xrange(minimum, maximum + 1, divisor))
               
            # Don't parse the divisor again 
            f = div_splits[0]

            # i, j-k, j-k/x
            hyphen_splits = f.split("-")
            
            if hyphen_splits[0].isdigit():
                #j-k, j-k/x
                if len(hyphen_splits) > 1:
                    return set( xrange(int(hyphen_splits[0]), int(hyphen_splits[1]) + 1, divisor) )

                # i
                return {int(f)}

            #If no rule matches, the string isn't valid
            raise InvalidFieldError(f)

        #Saves boilerplate string checks,
        # Intead, assume field is valid, and otherwise throw error
        except (IndexError, ValueError):
            raise InvalidFieldError(f)


    @classmethod
    def parse(cls, cron_string):
        """
            Parses a cron_string that looks like "m h dom moy dow year"
            return is a dictionary of sets holding integers contained by that field
        """
        try:
            fields = cron_string.split(" ")
            return {
                "minutes": cls.parse_field(fields[0], 0, 59),
                "hours": cls.parse_field(fields[1], 0, 23),
                "dom": cls.parse_field(fields[2], 1, 31),
                "moy": cls.parse_field(fields[3], 1, 12),
                "dow": cls.parse_field(fields[4], 1, 7),
                "year": cls.parse_field(fields[5], 2000, 2025)  #What is a sensible year here?
            }
        except InvalidFieldError as e:
            raise InvalidCronStringError("{}:  ({})".format(cron_string, e.args[0]))


    @staticmethod
    def is_holiday(rule):
        """
            Holiday is defined as one day, one month, one year:

            e.g. Easter: "* * 5 4 * 2015"
        """
        return re.compile(BasicCronRule.holiday_re).match(rule.strip()) is not None


    @staticmethod
    def holiday_tuple(hrule):
        """
            assumes hrule is a holiday
            returns tuple: (dd, mm, yyyy)
        """
        return tuple([ int(d) for d in re.findall(BasicCronRule.holiday_re, hrule.strip())[0] ])


    @classmethod
    def is_valid(cls, cron_string):
        """
            This class method checks whether or not a cron string looks like "12:34 13:31 * */2 1-5 *"
            That is, the first two fields are start and stop, and the last 4 are standard cron

            Note that this is just a wrapper around parse(), so usually it's faster to just attempt parse, 
                and catch the error
        """
        try:
            cls.parse(cron_string)
            return True
        except InvalidCronStringError:
            return False


    def contains(self, time_obj):
        """
            Returns True/False if time_obj is contained in ruleset
        """

        #If all checks pass, the time_obj belongs to this ruleset
        if time_obj.year not in self.rulesets["year"]:
            return False
        
        if time_obj.month not in self.rulesets["moy"]:
            return False

        if time_obj.day not in self.rulesets["dom"]:
            return False
        
        if time_obj.isoweekday() not in self.rulesets["dow"]:
            return False

        if time_obj.hour not in self.rulesets["hours"]:
            return False

        if time_obj.minute not in self.rulesets["minutes"]:
            return False


        return True


    def __contains__(self, time_obj):
        return self.contains(time_obj)



class CronRangeRule(BasicCronRule):

    hhmm_re = "(\d{1,2}):(\d{1,2})"

    @classmethod
    def parse_field(cls, f, minimum=0, maximum=0):
        #Try to find HH:MM fields
        try:
            hour, minute = map(int, re.findall(CronRangeRule.hhmm_re, f.strip())[0])
            return Bunch(hour=hour, minute=minute)
        except:
            #Otherwise assume nomal cron field
            return super(CronRangeRule, cls).parse_field(f, minimum, maximum)


    @classmethod
    def parse(cls, cron_string):
        try:
            if not cls.looks_like_range_rule(cron_string):
                raise InvalidCronStringError(cron_string)

            fields = cron_string.split(" ")
            return {
                "start": cls.parse_field(fields[0]),
                "stop": cls.parse_field(fields[1]),
                "dom": cls.parse_field(fields[2], 1, 31),
                "moy": cls.parse_field(fields[3], 1, 12),
                "dow": cls.parse_field(fields[4], 1, 7),
                "year": cls.parse_field(fields[5], 2000, 2025)  #What is a sensible year here?
            }
        except InvalidFieldError as e:
            raise InvalidCronStringError("{}:  ({})".format(cron_string, e.args[0]))


    def contains(self, time_obj):
        """
            Returns True/False if time_obj is contained in ruleset
        """

        #If all checks pass, the time_obj belongs to this ruleset

        if time_obj.year not in self.rulesets["year"]:
            return False
        
        if time_obj.month not in self.rulesets["moy"]:
            return False

        if time_obj.day not in self.rulesets["dom"]:
            return False
        
        if time_obj.isoweekday() not in self.rulesets["dow"]:
            return False

        #Determine if time_obj is within the time range 
        if time_obj.hour < self.rulesets["start"].hour or (time_obj.hour == self.rulesets["start"].hour and time_obj.minute < self.rulesets["start"].minute):
            return False

        if time_obj.hour > self.rulesets["stop"].hour or (time_obj.hour == self.rulesets["stop"].hour and\
             time_obj.minute > self.rulesets["stop"].minute):
            return False

        return True


    @staticmethod
    def looks_like_range_rule(cron_string):
        """
            This class method checks whether or not a cron string looks like "12:34 13:31 ..."
            It doesn't go through the logic of checking each field.  Parsing is equivalent to validating
        """
        fields = cron_string.split(" ")
        hhmm_re = re.compile(CronRangeRule.hhmm_re)
        return (hhmm_re.match(fields[0]) is not None) and (hhmm_re.match(fields[1]) is not None)



