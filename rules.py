import re


#Optimization for handling wildcards
class WildCardSet(object):
    #Always return true for in operator 
    # x in WildCardSet() -> True
    def __contains__(self, key):
        return True


class BasicCronRule(object):

    holiday_re = "[\*]\s[\*]\s(\d{1,2})\s(\d{1,2})\s[\*]\s(\d{4})"
    
    def __init__(self, cron_string):
        self.rulesets = self.parse(cron_string)


    def parse_field(self, f, minimum=0, maximum=0):
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

            if len(div_splits) > 1 and div_splits[1].isdigit():
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

        #Saves boilerplate checking length of string,
        # Intead, assume it's valid, and otherwise throw error
        except IndexError:
            raise InvalidFieldError(f)


    def parse(self, cron_string):
        """
            Parses a cron_string that looks like "m h dom moy dow year"
            return is a dictionary of sets holding integers contained by that field
        """
        fields = cron_string.split(" ")
        return {
            "minutes": self.parse_field(fields[0], 0, 59),
            "hours": self.parse_field(fields[1], 0, 23),
            "dom": self.parse_field(fields[2], 1, 31),
            "moy": self.parse_field(fields[3], 1, 12),
            "dow": self.parse_field(fields[4], 1, 7),
            "year": self.parse_field(fields[5], 2000, 2025)  #What is a sensible year here?
        }

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


    def contains(self, time_obj):
        """
            Returns True/False if time_obj is contained in ruleset
        """

        #If all checks pass, the time_obj belongs to this ruleset
        #Reverse order to ensure holidays are fast
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
